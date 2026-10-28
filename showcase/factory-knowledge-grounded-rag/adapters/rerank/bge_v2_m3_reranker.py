# -*- coding: utf-8 -*-
"""
Production Cross-Encoder Reranker using BAAI/bge-reranker-v2-m3.
Implements BaseReranker decoupled contract.
Computes true joint cross-attention relevance scores for (query, chunk) pairs.
Normalizes logits to [0.0, 1.0] probabilities via Sigmoid.
Preserves full ranking lineage (hybrid_rrf_score, original_rank, reranker_score).
"""

import time
import torch
from typing import List, Optional, Tuple
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from core.interfaces import BaseReranker
from core.schema import NormalizedBlock


class BGEv2M3Reranker(BaseReranker):
    """
    Real multilingual Cross-Encoder Reranker powered by BAAI/bge-reranker-v2-m3.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        calibrated_threshold: float = 0.5,
        max_length: int = 512,
        batch_size: int = 16,
        device: Optional[str] = None
    ) -> None:
        self.model_name = model_name
        self.calibrated_threshold = calibrated_threshold
        self.max_length = max_length
        self.batch_size = batch_size

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        t0 = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        self.load_duration_seconds = time.time() - t0

    def set_calibrated_threshold(self, threshold: float) -> None:
        """Update active filtering threshold based on calibration metrics."""
        self.calibrated_threshold = threshold

    def compute_scores(self, query: str, texts: List[str]) -> List[float]:
        """
        Compute joint cross-encoder normalized relevance scores for (query, text) pairs.
        Returns float probabilities in range [0.0, 1.0] after sigmoid activation.
        """
        if not texts:
            return []

        pairs = [[query, text] for text in texts]
        all_probs: List[float] = []

        with torch.no_grad():
            for i in range(0, len(pairs), self.batch_size):
                batch_pairs = pairs[i : i + self.batch_size]
                inputs = self.tokenizer(
                    batch_pairs,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                ).to(self.device)

                logits = self.model(**inputs, return_dict=True).logits.view(-1).float()
                probs = torch.sigmoid(logits).tolist()
                if isinstance(probs, float):
                    probs = [probs]
                all_probs.extend(probs)

        return all_probs

    def rerank(
        self,
        query: str,
        candidates: List[NormalizedBlock],
        threshold: Optional[float] = None
    ) -> List[NormalizedBlock]:
        """
        Rerank and filter NormalizedBlocks.
        Updates block metadata with reranker_score, raw_logit, reranker_rank, and threshold acceptance.
        """
        if not candidates:
            return []

        active_thresh = threshold if threshold is not None else self.calibrated_threshold
        texts = [c.content for c in candidates]

        scores = self.compute_scores(query, texts)

        # Store lineage on all candidates before filtering
        scored_candidates: List[Tuple[float, int, NormalizedBlock]] = []
        for idx, (block, score) in enumerate(zip(candidates, scores)):
            block.metadata["original_rank"] = idx + 1
            block.metadata["hybrid_rrf_score"] = block.metadata.get("rrf_score", 0.0)
            block.metadata["reranker_score"] = score
            block.metadata["reranker_normalized_score"] = score
            block.metadata["accepted_by_threshold"] = (score >= active_thresh)
            scored_candidates.append((score, idx, block))

        # Sort descending by reranker_score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        accepted_blocks: List[NormalizedBlock] = []
        for rank, (score, orig_idx, block) in enumerate(scored_candidates, start=1):
            block.metadata["reranker_rank"] = rank
            if score >= active_thresh:
                accepted_blocks.append(block)

        return accepted_blocks
