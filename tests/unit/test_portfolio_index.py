import math
import pytest
from bd_agent_neural_net_coder.portfolio_index import chunk_pages, file_hash

def test_deterministic_chunk_ids():
    pages=[{"page":1,"text":"CAPABILITIES\n"+"simulation control test "*300}]
    a=chunk_pages(pages,"item","Item","a.pdf","sha256:"+"a"*64)
    b=chunk_pages(pages,"item","Item","a.pdf","sha256:"+"a"*64)
    assert [x["chunk_id"] for x in a]==[x["chunk_id"] for x in b]
    assert all(x["page_start"]==1 and x["section"]=="CAPABILITIES" for x in a)

def test_chunk_ids_change_with_source_hash():
    pages=[{"page":2,"text":"TEST\n"+"HIL simulation "*300}]
    a=chunk_pages(pages,"item","Item","a.pdf","sha256:"+"a"*64)
    b=chunk_pages(pages,"item","Item","a.pdf","sha256:"+"b"*64)
    assert a[0]["chunk_id"]!=b[0]["chunk_id"]
