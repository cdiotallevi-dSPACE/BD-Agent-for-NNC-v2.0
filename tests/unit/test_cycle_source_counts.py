from bd_agent_neural_net_coder.pipeline import calculate_cycle_source_counts


def test_cycle_source_counts_distinguish_retrieved_approved_pdf_and_patent():
    sources=[
        {"source_id":"SRC-0001","source_type":"html","content_hash":"a","url":"https://gm.com/page"},
        {"source_id":"SRC-0002","source_type":"pdf","content_hash":"b","url":"https://gm.com/paper.pdf"},
        {"source_id":"SRC-0003","source_type":"html","content_hash":"c","url":"https://patents.google.com/patent/US123/en","source_domain_class":"specialist_patent_source","normalized_publication_number":"US123"},
        {"source_id":"SRC-0004","source_type":"html","content_hash":"d","url":"https://data.uspto.gov/example","source_domain_class":"specialist_patent_source","normalized_publication_number":"US123"},
        {"source_id":"SRC-0005","source_type":"pdf","content_hash":None,"retrieval_status":"retrieval_failed","retrieval_error":"timeout","url":"https://example.com/fail.pdf"},
    ]
    relevant={"relevant_evidence":[{"source_id":"SRC-0002"},{"source_id":"SRC-0003"}]}
    assert calculate_cycle_source_counts(sources,relevant)=={
        "total_retrieved_sources":4,
        "total_retrieved_and_approved_sources":2,
        "total_retrieved_pdfs":1,
        "total_retrieved_and_approved_pdfs":1,
        "total_retrieved_patents":1,
        "total_retrieved_and_approved_patents":1,
    }
