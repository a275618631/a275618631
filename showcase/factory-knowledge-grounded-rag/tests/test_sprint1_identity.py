# -*- coding: utf-8 -*-
"""
Sprint 1 Unit Tests: Stable Chunk Identity Generator.
Validates SHA-256 repeatability across runs, processes, and sensitivity to source changes.
Prohibits Python built-in hash().
"""

import subprocess
import sys
from adapters.chunking.identity import generate_deterministic_chunk_id


def test_deterministic_chunk_id_repeatability():
    params = {
        "document_id": "DOC-MOTOR-01",
        "source_checksum": "a1b2c3d4e5f67890",
        "page": 3,
        "heading_path": ["Maintenance", "Bearing Replacement"],
        "content": "Step 1: Check lube oil temperature.",
        "chunker_version": "1.0.0",
        "chunk_index_in_block": 0
    }

    id1 = generate_deterministic_chunk_id(**params)
    id2 = generate_deterministic_chunk_id(**params)
    assert id1 == id2
    assert id1.startswith("DOC-MOTOR-01-P3-")
    assert len(id1) > 16


def test_deterministic_cross_process_consistency():
    cmd = [
        sys.executable,
        "-c",
        (
            "from adapters.chunking.identity import generate_deterministic_chunk_id; "
            "print(generate_deterministic_chunk_id("
            "document_id='DOC-MOTOR-01', "
            "source_checksum='a1b2c3d4e5f67890', "
            "page=3, "
            "heading_path=['Maintenance', 'Bearing Replacement'], "
            "content='Step 1: Check lube oil temperature.', "
            "chunker_version='1.0.0', "
            "chunk_index_in_block=0))"
        )
    ]
    
    res1 = subprocess.check_output(cmd, text=True).strip()
    res2 = subprocess.check_output(cmd, text=True).strip()
    local_id = generate_deterministic_chunk_id(
        document_id="DOC-MOTOR-01",
        source_checksum="a1b2c3d4e5f67890",
        page=3,
        heading_path=["Maintenance", "Bearing Replacement"],
        content="Step 1: Check lube oil temperature.",
        chunker_version="1.0.0",
        chunk_index_in_block=0
    )

    assert res1 == res2 == local_id, "Chunk ID must be completely stable across distinct Python processes"


def test_chunk_id_sensitivity():
    base_params = {
        "document_id": "DOC-MOTOR-01",
        "source_checksum": "a1b2c3d4e5f67890",
        "page": 3,
        "heading_path": ["Maintenance", "Bearing Replacement"],
        "content": "Step 1: Check lube oil temperature.",
        "chunker_version": "1.0.0",
        "chunk_index_in_block": 0
    }
    base_id = generate_deterministic_chunk_id(**base_params)

    # 1. Content variation
    content_modified = dict(base_params, content="Step 1: Check lube oil pressure.")
    assert generate_deterministic_chunk_id(**content_modified) != base_id

    # 2. Source Checksum / revision variation
    checksum_modified = dict(base_params, source_checksum="ffffffffffffffff")
    assert generate_deterministic_chunk_id(**checksum_modified) != base_id

    # 3. Page variation
    page_modified = dict(base_params, page=4)
    assert generate_deterministic_chunk_id(**page_modified) != base_id

    # 4. Heading path variation
    heading_modified = dict(base_params, heading_path=["Maintenance", "Emergency Stop"])
    assert generate_deterministic_chunk_id(**heading_modified) != base_id

    # 5. Chunker version variation
    version_modified = dict(base_params, chunker_version="2.0.0")
    assert generate_deterministic_chunk_id(**version_modified) != base_id
