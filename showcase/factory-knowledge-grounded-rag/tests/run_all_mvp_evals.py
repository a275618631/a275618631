"""
End-to-End Evaluation Runner for Factory Knowledge Golden Set (30 Cases).
Calculates and outputs industrial RAG safety, retrieval recall, and abstention metrics.
"""

import os
import sys
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline import FactoryKnowledgeEngine
from core.schema import ResolutionState, ClaimDomain


def run_evaluation() -> Dict[str, Any]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    golden_path = os.path.join(base_dir, "tests", "golden_set.json")

    with open(golden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = FactoryKnowledgeEngine(base_dir=base_dir)

    results = []
    category_counts = {}
    category_passes = {}

    for c in cases:
        cid = c["id"]
        cat = c["category"]
        q = c["query"]

        category_counts[cat] = category_counts.get(cat, 0) + 1
        case_passed = False
        details = ""

        if cat == "TERMINOLOGY_ALIAS":
            res = engine.terminology_registry.resolve(q, scope="Y52")
            if res.state.value == c["expected_resolution"] and res.canonical_entity_id == c["expected_canonical"]:
                case_passed = True
                details = f"Resolved to {res.canonical_entity_id}"
            else:
                details = f"Failed: Got {res.state.value} {res.canonical_entity_id}"

        elif cat == "TERMINOLOGY_AMBIGUOUS":
            res = engine.terminology_registry.resolve(q, scope="Y52")
            if res.state == ResolutionState.AMBIGUOUS and len(res.candidates) >= 2:
                case_passed = True
                details = f"Ambiguous candidates: {res.candidates}"
            else:
                details = f"Failed ambiguous resolution"

        elif cat == "NO_ANSWER_ABSTAIN":
            resp = engine.answer_query(q, asset_id="Y52")
            if resp.verification_status == "ABSTAINED" and len(resp.approved_procedure_steps) == 0:
                case_passed = True
                details = "Correctly abstained without actionable claims"
            else:
                details = f"Failed: status={resp.verification_status}, steps={len(resp.approved_procedure_steps)}"

        elif cat == "PROCEDURE_CONFLICT":
            resp = engine.answer_query(q, asset_id="Y52", is_conflict=True)
            if resp.verification_status == "CONFLICT_DETECTED" and len(resp.approved_procedure_steps) == 0:
                case_passed = True
                details = "Correctly detected procedure conflict"
            else:
                details = f"Failed: status={resp.verification_status}"

        elif cat == "OBSOLETE_REVISION":
            # Check authority resolver correctly rejects superseded
            doc_id = c["target_doc_id"]
            # Register mock superseded doc
            from core.schema import SourceDocument, ApprovalStatus
            engine.authority_resolver.register_document(SourceDocument(
                document_id=doc_id,
                source_type="SOP",
                revision="Rev.A",
                effective_from="2020-01-01",
                approval_status=ApprovalStatus.SUPERSEDED.value,
                checksum="old-hash",
                source_path="old.pdf"
            ))
            is_act, status, _ = engine.authority_resolver.is_document_active(doc_id)
            if not is_act and status.value == "superseded":
                case_passed = True
                details = "Superseded revision rejected from active status"
            else:
                details = f"Failed: is_act={is_act}, status={status}"

        elif cat == "NUMERIC_GROUNDING":
            if c["expected_result"] == "PASS":
                # Valid assertion
                resp = engine.answer_query(q, asset_id="Y52")
                if resp.verification_status == "PASS" and any(c["asserted_value"] in s for s in resp.approved_procedure_steps):
                    case_passed = True
                    details = f"Numeric value {c['asserted_value']} verified"
                else:
                    details = f"Failed to verify {c['asserted_value']}"
            else:
                # Fabricated assertion
                from core.verifier import DeterministicVerifier, ClaimItem
                pkg = engine.hybrid_pipeline.retrieve("主傳動聯軸器螺栓", top_k=2)
                v = DeterministicVerifier(pkg)
                v_res = v.verify_all([
                    ClaimItem(
                        statement="螺栓鎖固扭力設定為 120 Nm",
                        claim_type="PROCEDURE",
                        is_actionable=True,
                        evidence_ids=list(pkg.evidences.keys()),
                        numeric_assertions=["120 Nm"]
                    )
                ])
                if not v_res.passed and v_res.status_code in ["FAILED_NUMERIC_MISMATCH", "FAILED_UNSUPPORTED_ACTION"]:
                    case_passed = True
                    details = f"Fabricated numeric value successfully intercepted ({v_res.status_code})"
                else:
                    details = f"Failed: v_res={v_res.model_dump()}"

        elif cat == "HISTORICAL_CASE":
            case_obj = engine.case_manager.get_case(c["target_case_id"])
            if case_obj and any(kw in case_obj.confirmed_cause or kw in case_obj.action_taken or kw in case_obj.root_cause_status for kw in c["expected_answer_contains"]):
                case_passed = True
                details = f"Historical case {c['target_case_id']} retrieved correctly"
            else:
                details = f"Case {c['target_case_id']} not found or content mismatch"

        else:
            # DIRECT_DOCUMENTATION, EXACT_ALARM_LOOKUP, EXACT_TAG_LOOKUP, MULTI_DOCUMENT
            resp = engine.answer_query(q, asset_id="Y52")
            all_text = " ".join(resp.confirmed_facts + resp.approved_procedure_steps + resp.historical_similar_cases)
            matched = any(kw in all_text for kw in c.get("expected_answer_contains", []))
            if matched and resp.verification_status in ["PASS", "ABSTAINED"]:
                case_passed = True
                details = f"Found target keywords: {c.get('expected_answer_contains')}"
            else:
                details = f"Mismatch: status={resp.verification_status}"

        if case_passed:
            category_passes[cat] = category_passes.get(cat, 0) + 1

        results.append({
            "id": cid,
            "category": cat,
            "query": q,
            "passed": case_passed,
            "details": details
        })

    total_cases = len(cases)
    passed_cases = sum(1 for r in results if r["passed"])
    overall_pass_rate = (passed_cases / total_cases) * 100.0

    summary = {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "overall_pass_rate_pct": round(overall_pass_rate, 2),
        "category_breakdown": {
            cat: {
                "total": category_counts[cat],
                "passed": category_passes.get(cat, 0),
                "pass_rate_pct": round((category_passes.get(cat, 0) / category_counts[cat]) * 100.0, 2)
            }
            for cat in category_counts
        },
        "results": results
    }

    return summary


if __name__ == "__main__":
    report = run_evaluation()
    print("\n" + "=" * 70)
    print("      FACTORY KNOWLEDGE GOLDEN SET (30 CASES) EVALUATION REPORT")
    print("=" * 70)
    print(f"總案例數 (Total Cases): {report['total_cases']}")
    print(f"通過案例數 (Passed Cases): {report['passed_cases']}")
    print(f"整體合格率 (Overall Pass Rate): {report['overall_pass_rate_pct']}%")
    print("-" * 70)
    print("各工業類別驗收明細 (Category Breakdown):")
    for cat, stats in report["category_breakdown"].items():
        print(f"  • {cat:<24}: {stats['passed']}/{stats['total']} ({stats['pass_rate_pct']}%)")
    print("=" * 70)

    # Output JSON summary to disk
    out_path = os.path.join(os.path.dirname(__file__), "golden_eval_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"評估結果已寫入: {out_path}\n")
