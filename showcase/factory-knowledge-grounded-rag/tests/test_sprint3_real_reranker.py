import pytest
from core.schema import NormalizedBlock
from adapters.rerank.bge_v2_m3_reranker import BGEv2M3Reranker
from adapters.rerank.bge_reranker import HeuristicReranker


def test_heuristic_reranker_baseline():
    """Verify baseline heuristic reranker functions as documented fallback."""
    reranker = HeuristicReranker()
    b1 = NormalizedBlock(
        block_id="b1",
        document_id="doc1",
        page=1,
        block_type="procedure_step",
        parser="test_parser",
        parser_version="1.0",
        content="主軸軸承溫度過高檢測與潤滑更換程序",
        metadata={"domain": "PROCEDURE"}
    )
    b2 = NormalizedBlock(
        block_id="b2",
        document_id="doc2",
        page=1,
        block_type="paragraph",
        parser="test_parser",
        parser_version="1.0",
        content="員工考勤打卡作業規範",
        metadata={"domain": "GENERAL"}
    )
    results = reranker.rerank("主軸軸承異常", [b1, b2], threshold=0.1)
    assert len(results) >= 1
    assert results[0].block_id == "b1"


def test_bge_v2_m3_scoring_and_rerank():
    """Verify BGE-v2-M3 neural cross-encoder loads and scores semantic relevance."""
    reranker = BGEv2M3Reranker(model_name="BAAI/bge-reranker-v2-m3")
    query = "CNC 車床主軸軸承溫度過高，請說明檢修標準程序。"

    relevant_block = NormalizedBlock(
        block_id="blk-rel",
        document_id="DOC-08_Y52",
        page=1,
        block_type="procedure_step",
        parser="test_parser",
        parser_version="1.0",
        content="Y52主軸單元：主軸軸承運轉溫度過高（超過 65 度 C）時，應立即停機檢查冷卻油路與預緊力矩（標準 45 Nm）。",
        metadata={"domain": "PROCEDURE"}
    )
    irrelevant_block = NormalizedBlock(
        block_id="blk-irrel",
        document_id="DOC-99_HR",
        page=1,
        block_type="paragraph",
        parser="test_parser",
        parser_version="1.0",
        content="行政處公告：本年度員工健康檢查將於下週五於總部大樓三樓會議室辦理，請同仁依時段報到。",
        metadata={"domain": "GENERAL"}
    )

    scores = reranker.compute_scores(query, [relevant_block.content, irrelevant_block.content])
    assert len(scores) == 2
    assert scores[0] > scores[1]
    assert scores[0] > 0.5
    assert scores[1] < 0.1

    reranked = reranker.rerank(query, [irrelevant_block, relevant_block], threshold=0.05)
    assert len(reranked) >= 1
    assert reranked[0].block_id == "blk-rel"
