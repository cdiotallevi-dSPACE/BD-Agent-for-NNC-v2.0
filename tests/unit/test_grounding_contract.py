def test_empty_supporting_chunks_cannot_be_positive():
    assessed={"hard_rule_passed":False,"decision":"insufficient_dspace_portfolio_grounding","supporting_dspace_document_chunk_ids":[]}
    assert not assessed["hard_rule_passed"]
    assert assessed["decision"]=="insufficient_dspace_portfolio_grounding"
