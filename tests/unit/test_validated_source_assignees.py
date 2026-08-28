from bd_agent_neural_net_coder.search_orchestrator import load_company_profile

def test_workbook_assignees_override_and_yaml_cannot_invent_identity(tmp_path):
    folder=tmp_path/"data/company_source_profiles"; folder.mkdir(parents=True)
    (folder/"alpha.yaml").write_text("validated_patent_assignees:\n  - assignee_name: Invented LLC\n    validation_status: established\n",encoding="utf-8")
    empty=load_company_profile(tmp_path,"Alpha","alpha.example")
    assert empty["validated_source_assignees"]==[]
    assert empty["validated_patent_assignees"]==[]
    explicit=load_company_profile(tmp_path,"Alpha","alpha.example",validated_source_assignees=["Alpha IP LLC"])
    assert [x["assignee_name"] for x in explicit["validated_source_assignees"]]==["Alpha IP LLC"]
    assert explicit["validated_source_assignees"][0]["validation_basis"]=="companies_workbook_validated_source_assignee"
