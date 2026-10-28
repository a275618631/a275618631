"""
Real Ollama Local LLM Adapter for Grounded Industrial Diagnosis.
Provides native HTTP connectivity to local Ollama runtime (default: qwen3:8b),
enforcing strict Pydantic JSON Schema validation, deterministic temperature=0,
and end-to-end integration with the DeterministicVerifier gate.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional, Any, Dict, List
from core.interfaces import BaseLLM
from core.evidence import EvidencePackage
from core.response_schema import FactoryDiagnosisResponse
from core.verifier import DeterministicVerifier, ClaimItem, VerificationResult


class OllamaServiceUnavailableError(RuntimeError):
    """Raised when the Ollama local HTTP service is unreachable or encounters transport errors."""
    pass


class SchemaValidationError(RuntimeError):
    """Raised when the LLM output fails to deserialize against the strict Pydantic schema."""
    pass


class OllamaAdapter(BaseLLM):
    """
    Production Adapter for local Ollama runtime.
    - Default Endpoint: http://127.0.0.1:11434
    - Default Model: qwen3:8b (or OLLAMA_MODEL environment variable)
    - Enforces JSON Schema structured output
    - Enforces temperature=0 for deterministic reproducibility
    - Integrates DeterministicVerifier safety gate before returning response
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:11434",
        model_name: Optional[str] = None,
        timeout: int = 120
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "qwen3:8b")
        self.timeout = timeout

    def generate_structured(self, prompt: str, schema_cls: Any) -> Any:
        """
        Invoke Ollama API with explicit Pydantic JSON Schema format and temperature=0.
        Raises OllamaServiceUnavailableError if service is unreachable.
        Raises SchemaValidationError if output does not conform to schema_cls.
        """
        schema = schema_cls.model_json_schema()
        system_instruction = (
            "你是一位世界級的工廠設備診斷與安全分析工程師。\n"
            "你必須以台灣繁體中文回應。\n"
            "嚴格遵守以下安全與真實性準則：\n"
            "1. 僅能依據檢索到的 Evidence 進行事實陳述與處方建議，絕不憑空捏造。\n"
            "2. 歷史工單或歷史相似問題 (HISTORICAL_CASE) 僅能作為歷史經驗參考，嚴禁冒充為當前事件的現場真因。\n"
            "3. 所有具體主張必須填入 claims 列表，引用對應的 evidence_ids。\n"
            "4. 提及數值（如壓力、扭矩、間隙）時，數值必須與 Evidence 內的原始數據精確吻合。\n"
            "5. 若資料不足或無依據，必須填寫於 unknowns 與 required_field_checks，不可隨意下達操作指令。\n"
            "6. 輸出必須完全符合所提供的 JSON Schema。"
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "format": schema,
            "options": {
                "temperature": 0.0
            },
            "stream": False
        }

        api_url = f"{self.endpoint}/api/chat"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=req_data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
                data = json.loads(resp_bytes.decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                if not content:
                    raise SchemaValidationError("Ollama returned empty message content.")
                return schema_cls.model_validate_json(content)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            raise OllamaServiceUnavailableError(
                f"無法連線至 Ollama 服務 ({api_url}): {e}。請確認 Ollama 守護行程正在運行。"
            ) from e
        except Exception as e:
            if isinstance(e, SchemaValidationError):
                raise
            raise SchemaValidationError(f"無法解析 Ollama 結構化輸出為 {schema_cls.__name__}: {e}") from e

    def build_grounded_prompt(self, query: str, evidence_pkg: EvidencePackage, asset_id: Optional[str]) -> str:
        """Constructs an evidence-grounded prompt for the LLM."""
        evidence_lines = []
        for ev in evidence_pkg.evidences.values():
            domain_label = f"[{ev.claim_domain}]" if ev.claim_domain else ""
            doc_info = f"文件: {ev.source_doc_id or 'UNKNOWN'}"
            evidence_lines.append(
                f"- [依據ID: {ev.evidence_id}] {domain_label} {doc_info}\n"
                f"  內容摘要: {ev.content_snippet}"
            )
        evidence_text = "\n".join(evidence_lines) if evidence_lines else "（無可用檢索依據）"

        prompt = (
            f"【工廠設備問題諮詢】\n"
            f"設備編號 (Asset ID): {asset_id or '未指定'}\n"
            f"現場工程問題: {query}\n\n"
            f"【檢索之可佐證依據 (Evidence Package)】:\n"
            f"{evidence_text}\n\n"
            f"請依據上述提供的依據，填寫結構化診斷報告。\n"
            f"務必在 claims 中列出各項主張並標註正確的 evidence_ids（使用 EV-xxx 代號）。"
        )
        return prompt

    def generate_diagnosis(
        self,
        query: str,
        evidence_pkg: EvidencePackage,
        asset_id: Optional[str] = "Y52",
        is_conflict: bool = False
    ) -> FactoryDiagnosisResponse:
        """
        Main pipeline: Grounded Prompt -> Real Ollama -> DeterministicVerifier Gate.
        """
        # 1. Conflict Safety Gate
        if is_conflict:
            verifier = DeterministicVerifier(evidence_pkg)
            v_res = verifier.verify_all([], is_conflict=True)
            return FactoryDiagnosisResponse(
                query=query,
                asset_id=asset_id,
                unknowns=["現場文件存在數值或程序衝突，系統拒絕下達操作指令。"],
                required_field_checks=["請設備主管工程師介入審查衝突文件版本。"],
                claims=[],
                verification_status="CONFLICT_DETECTED",
                verification_details=v_res.model_dump()
            )

        # 2. No Evidence Available Gate -> Safe Abstain
        if not evidence_pkg or not evidence_pkg.evidences:
            claim_abstain = ClaimItem(
                statement=f"查無關於「{query}」的現場標準文件或足夠佐證，系統自動棄權以確保現場安全。",
                claim_type="HYPOTHESIS",
                is_actionable=False
            )
            verifier = DeterministicVerifier(evidence_pkg)
            v_res = verifier.verify_all([claim_abstain], no_evidence_available=True)
            return FactoryDiagnosisResponse(
                query=query,
                asset_id=asset_id,
                unknowns=[f"未在標準文件中檢索到「{query}」之相關規範。"],
                required_field_checks=["請攜帶儀表至現場進行手動量測與確認。", "核對設備出廠銘牌代號。"],
                claims=[claim_abstain],
                verification_status=v_res.status_code,
                verification_details=v_res.model_dump()
            )

        # 3. Grounded Prompt Generation via Real Ollama
        prompt = self.build_grounded_prompt(query, evidence_pkg, asset_id)
        response: FactoryDiagnosisResponse = self.generate_structured(prompt, FactoryDiagnosisResponse)
        response.query = query
        response.asset_id = asset_id

        # 4. Deterministic Verification Gate
        verifier = DeterministicVerifier(evidence_pkg)
        v_res = verifier.verify_all(response.claims, is_conflict=is_conflict, no_evidence_available=False)
        response.verification_status = v_res.status_code
        response.verification_details = v_res.model_dump()

        # 5. Safety Interlock: If verification failed, sanitize actionable procedures
        if not v_res.passed:
            if response.approved_procedure_steps:
                response.unknowns.append(
                    f"安全警示：生成之處方未通過確定性安全驗證 ({v_res.status_code})，系統已阻擋可執行步驟。"
                )
                response.approved_procedure_steps = []

        return response
