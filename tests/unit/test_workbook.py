from pathlib import Path
from openpyxl import Workbook, load_workbook
import pytest
from bd_agent_neural_net_coder.workbook import COUNT_KEYS, selected_companies, update_rating

HEADERS=["company_id","company_name","Other_names","company_domain","country","industry","notes","Scan Y/N","Overall Product Match","Total Retrieved Sources","Total Retrieved and approved Sources","total retrieved PDFs","total retrieved and approved PDFs","total retrieved Patents","total retrieved and approved patents","Validated Source assignees"]
COUNTS={
    "total_retrieved_sources":12,
    "total_retrieved_and_approved_sources":5,
    "total_retrieved_pdfs":4,
    "total_retrieved_and_approved_pdfs":2,
    "total_retrieved_patents":3,
    "total_retrieved_and_approved_patents":2,
}

def test_registry_selects_only_y_with_blank_rating(tmp_path: Path):
    path=tmp_path/"Companies.xlsx"; wb=Workbook(); ws=wb.active; ws.title="Companies"
    ws.append(HEADERS)
    ws.append(["A","Alpha",None,"alpha.example","DE","Power",""," y ",None])
    ws.append(["B","Beta","Beta GmbH, BETA","beta.example","DE","Power","","Y",50,None,None,None,None,None,None,"Beta IP GmbH; Beta Research LLC"])
    ws.append(["C","Gamma",None,"gamma.example","DE","Power","","N",None]); wb.save(path)
    rows=selected_companies(path,"cycle_test")
    assert [r["company_id"] for r in rows]==["A","B"]
    assert rows[1]["previous_overall_product_match"]==50
    assert rows[1]["other_names"]==["Beta GmbH","BETA"]
    assert rows[1]["validated_source_assignees"]==["Beta IP GmbH","Beta Research LLC"]

def test_registry_normalizes_space_rating_and_full_url_domain(tmp_path: Path):
    path=tmp_path/"Companies.xlsx"; wb=Workbook(); ws=wb.active; ws.title="Companies"
    ws.append(HEADERS)
    ws.append(["A","Alpha","General Motors Company, GMC, GM","https://www.compredict.ai/","DE","Tiny AI","","Y"," "])
    wb.save(path)
    row=selected_companies(path,"cycle_test")[0]
    assert row["company_domain"]=="compredict.ai"
    assert row["company_domain_raw"]=="https://www.compredict.ai/"
    assert row["previous_overall_product_match"] is None
    assert row["previous_overall_product_match_raw"]==" "
    assert row["other_names"]==["General Motors Company","GMC","GM"]
    audit=update_rating(path,"A","Alpha"," ",73,"cycle_test","run_test",COUNTS,{key:None for key in COUNT_KEYS})
    assert audit["rating_update"]["new_value"]==73 and audit["rating_update"]["score_change"] is None
    assert audit["event"]=="company_cycle_results_written"
    check=selected_companies(path,"cycle_check")[0]
    assert check["previous_overall_product_match"]==73
    assert check["previous_cycle_source_counts_raw"]==COUNTS
    written=load_workbook(path); ws=written["Companies"]
    assert [ws.cell(2,column).value for column in range(10,16)]==list(COUNTS.values())
    assert all(ws.cell(2,column).number_format=="#,##0" for column in range(10,16))
    written.close()

def test_registry_accepts_bare_domain_and_numeric_rating(tmp_path: Path):
    path=tmp_path/"Companies.xlsx"; wb=Workbook(); ws=wb.active; ws.title="Companies"
    ws.append(HEADERS)
    ws.append(["A","Alpha",None,"compredict.ai","DE","Tiny AI","","Y",42])
    wb.save(path)
    row=selected_companies(path,"cycle_test")[0]
    assert row["company_domain"]=="compredict.ai"
    assert row["previous_overall_product_match"]==42

def test_registry_rejects_invalid_source_counts(tmp_path: Path):
    path=tmp_path/"Companies.xlsx"; wb=Workbook(); ws=wb.active; ws.title="Companies"
    ws.append(HEADERS); ws.append(["A","Alpha",None,"alpha.example","DE","Tiny AI","","Y",None]); wb.save(path)
    with pytest.raises(ValueError,match="incomplete"):
        update_rating(path,"A","Alpha",None,50,"cycle_test","run_test",{"total_retrieved_sources":1})
    invalid=dict(COUNTS); invalid["total_retrieved_pdfs"]=-1
    with pytest.raises(ValueError,match="non-negative"):
        update_rating(path,"A","Alpha",None,50,"cycle_test","run_test",invalid)
