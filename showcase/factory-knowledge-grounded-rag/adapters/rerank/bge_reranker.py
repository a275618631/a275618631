"""
Heuristic Token-Overlap Reranker Baseline.
Implements BaseReranker decoupled contract.
NOTE: This is a lightweight heuristic baseline based on character n-grams and token overlap,
preserved as a deterministic fallback. For the deep multilingual neural Cross-Encoder,
see `adapters.rerank.bge_v2_m3_reranker.BGEv2M3Reranker`.
"""

import re
from typing import List, Optional
from core.interfaces import BaseReranker
from core.schema import NormalizedBlock


class BGEReranker(BaseReranker):
    """
    Token-overlap heuristic reranker baseline.
    Maintained as deterministic fallback and baseline comparison.
    """


    def __init__(self, calibrated_threshold: float = 0.25) -> None:
        self.calibrated_threshold = calibrated_threshold

    def set_calibrated_threshold(self, threshold: float) -> None:
        """Update threshold based on golden set validation."""
        self.calibrated_threshold = threshold

    @staticmethod
    def _extract_tokens(text: str) -> List[str]:
        # Extract alphanumeric codes and tokens
        code_tokens = re.findall(r"[A-Za-z0-9\-]+", text.lower())
        # Extract CJK n-grams (2-3 chars)
        stopwords = {"是什麼", "是多少", "應使用", "何種", "規格", "為何", "在", "的", "之", "與", "及", "有", "請", "問", "y52", "冷軋", "產線"}
        cjk_chunks = re.findall(r"[\u4e00-\u9fa5]+", text)
        cjk_tokens = []
        for chunk in cjk_chunks:
            if 2 <= len(chunk) <= 4 and chunk not in stopwords:
                cjk_tokens.append(chunk)
            else:
                for n in [2, 3]:
                    for i in range(len(chunk) - n + 1):
                        sub = chunk[i:i+n]
                        if sub not in stopwords:
                            cjk_tokens.append(sub)
        return list(dict.fromkeys(code_tokens + cjk_tokens))

    def _score(self, query: str, block: NormalizedBlock) -> float:
        q_tokens = set(self._extract_tokens(query))
        if not q_tokens:
            return 0.0

        content_lower = block.content.lower()
        headings_lower = " ".join(block.heading_path).lower()
        full_text = f"{headings_lower} {content_lower}"
        c_tokens = set(self._extract_tokens(full_text))

        # Check entity overlap
        overlap = len(q_tokens & c_tokens)
        if overlap == 0:
            return 0.0

        score = overlap / len(q_tokens)

        # Bonus for exact phrase or critical code match
        for q_tok in q_tokens:
            if len(q_tok) >= 3 and q_tok in full_text:
                score += 0.15

        if query.lower() in full_text:
            score += 0.4

        return min(1.0, score)

    def rerank(
        self,
        query: str,
        candidates: List[NormalizedBlock],
        threshold: Optional[float] = None
    ) -> List[NormalizedBlock]:
        active_thresh = threshold if threshold is not None else self.calibrated_threshold
        scored = []
        for c in candidates:
            sc = self._score(query, c)
            if sc >= active_thresh:
                scored.append((sc, c))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in scored]

    def compute_scores(self, query: str, texts: List[str]) -> List[float]:
        """Compute relevance scores for (query, text) pairs based on token overlap."""
        q_tokens = set(self._extract_tokens(query))
        if not q_tokens:
            return [0.0] * len(texts)

        scores = []
        for text in texts:
            text_lower = text.lower()
            c_tokens = set(self._extract_tokens(text_lower))
            overlap = len(q_tokens & c_tokens)
            if overlap == 0:
                scores.append(0.0)
                continue

            score = overlap / len(q_tokens)
            for q_tok in q_tokens:
                if len(q_tok) >= 3 and q_tok in text_lower:
                    score += 0.15
            if query.lower() in text_lower:
                score += 0.4
            scores.append(min(1.0, score))

        return scores


# Explicit alias for architecture clarity
HeuristicReranker = BGEReranker

