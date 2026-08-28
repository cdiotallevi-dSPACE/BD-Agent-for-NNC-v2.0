from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

REQUIRED_ORDER=("OVERALL ASSESSMENT","Use-Case Product Fit","Relevant Evidence","Applicability Mappings","Authoritative dSPACE Portfolio Sources")


def report_identity(company_name:str,moment:datetime|None=None)->dict:
    moment=(moment or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    report_timestamp=moment.strftime("%Y-%m-%d_%H-%M-%S_UTC")
    safe=re.sub(r"-+","-",re.sub(r"[^A-Za-z0-9]+","-",company_name.encode("ascii","ignore").decode())).strip("-") or "Company"
    filename=f"{safe}_Sales-Assessment_{report_timestamp}.pdf"
    if not re.fullmatch(r"[A-Za-z0-9-]+_Sales-Assessment_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_UTC\.pdf",filename):
        raise ValueError("invalid readable report filename")
    return {
        "section_title":"OVERALL ASSESSMENT",
        "report_generated_at":moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "report_generated_display":moment.strftime("%d %B %Y at %H:%M:%S UTC").lstrip("0"),
        "report_timestamp":report_timestamp,
        "report_filename":filename,
    }


def _validate(final:dict,relevant:dict,identity:dict)->None:
    data=final.get("report_data",{})
    for key,value in identity.items():
        if data.get(key)!=value: raise ValueError(f"{key} differs from persisted report data")
    numbers=[item.get("display_number") for item in relevant.get("relevant_evidence",[])]
    if numbers!=list(range(1,len(numbers)+1)): raise ValueError("evidence display numbers must be progressive and gap-free")
    source_ids={item.get("source_id") for item in relevant.get("relevant_evidence",[])}
    if None in source_ids or len(source_ids)!=len(relevant.get("relevant_evidence",[])):
        raise ValueError("relevant evidence source IDs must be present and unique")
    if any(not re.fullmatch(r"SRC-\d{4,}",str(source_id)) for source_id in source_ids):
        raise ValueError("invalid relevant evidence source ID")
    if set(data.get("relevant_evidence_source_ids",[]))!=source_ids: raise ValueError("unknown relevant evidence source")
    seen=set()
    for mapping in final.get("applicability_mappings",[]):
        if not mapping.get("dspace_commercial_name"): raise ValueError("positive mapping lacks validated dSPACE commercial name")
        if mapping["mapping_id"] in seen: raise ValueError("duplicate applicability mapping ID")
        seen.add(mapping["mapping_id"])


def _mapping_display(mapping:dict)->str:
    value=mapping.get("mapping_display")
    if value: return value
    chain=mapping.get("mapping_chain")
    if not chain: raise ValueError("mapping chain missing")
    return " -> ".join(chain)


def _display_evidence_description(description:str)->str:
    """Preserve the complete normalized evidence statement in durable reports."""
    return re.sub(r"\s+"," ",str(description)).strip()


def _use_case_rows(final:dict)->list[tuple[str,str,int]]:
    """Return distinct use cases in descending Product Fit order."""
    values=final.get("overall_product_match",{}).get("use_case_scores",[])
    rows=[]; seen=set()
    for item in sorted(values,key=lambda x:(-int(x.get("use_case_score",0)),str(x.get("use_case_id","")))):
        use_case_id=str(item.get("use_case_id") or "unclassified_use_case")
        if use_case_id in seen: continue
        seen.add(use_case_id)
        label=use_case_id.replace("_"," ").strip().title()
        sources=", ".join(item.get("supporting_source_ids",[])[:3]) or "Not available"
        rows.append((label,sources,int(item.get("use_case_score",0))))
    return rows


def render_reports(out:Path,slug:str,stamp:str,final:dict,relevant:dict,report_generated_at:datetime)->Path:
    identity=report_identity(final["company_name"],report_generated_at)
    _validate(final,relevant,identity)
    compact_base=f"{slug}_{stamp}_sales_assessment"
    generated_line=f"Report generated on {identity['report_generated_display']}"
    assessment=str(final.get("narrative",{}).get("overall_assessment") or final.get("narrative",{}).get("executive_summary",""))
    target=final.get("target_company",{})
    company_domain=str(target.get("official_domain") or final.get("company_domain") or "Not specified")
    company_country=str(target.get("country") or final.get("country") or "Not specified")
    rating_band=final.get("overall_product_match",{}).get("band","not_classified")
    readiness=final.get("overall_product_match",{}).get("deployment_readiness",{})
    readiness_label="Qualification required" if readiness else "Not assessed"
    use_cases=_use_case_rows(final)
    patent_coverage=final.get("search_coverage",{}).get("patents",{})
    coverage_note=patent_coverage.get("interpretation","")
    lines=[f"# Sales Assessment: {final['company_name']}",f"Company domain: {company_domain}",f"Country: {company_country}","",f"Overall Product Match: **{final['overall_dspace_portfolio_applicability']}/100 - {rating_band}**",f"Deployment Readiness: **{readiness_label}**",generated_line,"","## OVERALL ASSESSMENT",assessment,"","## Use-Case Product Fit","","| USE CASES | Supporting Sources (max 3) | PRODUCT FIT |","| --- | --- | ---: |"]
    for label,sources,score in use_cases:
        lines.append(f"| {label} | {sources} | {score}/100 |")
    if not use_cases: lines.append("| No scored use cases identified | None | 0/100 |")
    lines.extend(["","## Search Coverage",coverage_note or "Patent search coverage status was not recorded.","","## Relevant Evidence","","| Source ID | Evidence | URL |","| --- | --- | --- |"])
    for item in relevant["relevant_evidence"]:
        display_description=_display_evidence_description(item["description"]).replace("|","/")
        lines.append(f"| {item['source_id']} | {display_description} | {item['canonical_url']} |")
    lines.extend(["","## Applicability Mappings","","| Use Case | Customer Evidence / Readiness | Potential NNC Capability |","| --- | --- | --- |"])
    for mapping in final["applicability_mappings"]:
        label=str(mapping.get("use_case_id","")).replace("_"," ").title()
        lines.append(f"| {label} | {mapping.get('customer_evidence_and_readiness','')} | {mapping.get('nnc_product_capability','')} |")
    if not final["applicability_mappings"]:
        lines.append("| No qualified mapping | No approved supporting evidence | Not assessed |")
    lines.extend(["","## Authoritative dSPACE Portfolio Sources"])
    seen=set(); references=[]
    for mapping in final["applicability_mappings"]:
        for ref in mapping.get("dspace_source_references",[]):
            if ref["chunk_id"] in seen: continue
            seen.add(ref["chunk_id"]); references.append(ref)
            pages=str(ref["page_start"]) if ref["page_start"]==ref["page_end"] else f"{ref['page_start']}-{ref['page_end']}"
            lines.append(f"- {ref['source_filename']}, page {pages}, section: {ref['section']}, chunk: `{ref['chunk_id']}`")
    (out/f"{compact_base}.md").write_text("\n".join(lines),encoding="utf-8")

    styles=getSampleStyleSheet()
    body=ParagraphStyle("BDA Body",parent=styles["BodyText"],fontName="Helvetica",fontSize=9.2,leading=12.5,spaceAfter=5,splitLongWords=True)
    small=ParagraphStyle("BDA Small",parent=body,fontSize=7.5,leading=9.5,splitLongWords=True)
    number=ParagraphStyle("BDA Number",parent=body,alignment=1)
    bullet=ParagraphStyle("BDA Bullet",parent=body,fontSize=8.2,leading=10.5,leftIndent=10,firstLineIndent=-7,spaceAfter=3)
    metadata=ParagraphStyle("BDA Metadata",parent=body,fontSize=9,leading=11,spaceAfter=1,alignment=0)
    story=[
        Paragraph(escape(f"Sales Assessment: {final['company_name']}"),styles["Title"]),
        Spacer(1,1.5*mm),
        Paragraph(escape(f"Company domain: {company_domain}"),metadata),
        Paragraph(escape(f"Country: {company_country}"),metadata),
        Spacer(1,3*mm),
        Paragraph(escape(f"Overall Product Match: {final['overall_dspace_portfolio_applicability']}/100 - {rating_band}"),styles["Heading2"]),
        Paragraph(escape(f"Deployment Readiness: {readiness_label}"),body),
        Paragraph(escape(generated_line),body),
        Spacer(1,2*mm),
        Paragraph("OVERALL ASSESSMENT",styles["Heading2"]),
        Paragraph(escape(assessment),body),
        Spacer(1,2*mm),
        Paragraph("Use-Case Product Fit",styles["Heading2"]),
    ]
    use_case_table_rows=[[Paragraph("<b>USE CASES</b>",body),Paragraph("<b>Supporting Sources (max 3)</b>",body),Paragraph("<b>PRODUCT FIT</b>",body)]]
    for label,sources,score in use_cases:
        use_case_table_rows.append([Paragraph(escape(label),body),Paragraph(escape(sources),small),Paragraph(f"{score}/100",number)])
    if not use_cases: use_case_table_rows.append([Paragraph("No scored use cases identified",body),Paragraph("None",small),Paragraph("0/100",number)])
    use_case_table=LongTable(use_case_table_rows,colWidths=[82*mm,57*mm,29*mm],repeatRows=1,splitByRow=1,hAlign="LEFT")
    use_case_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#8AA4B8")),("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(1,1),(1,-1),"CENTER"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.extend([use_case_table,Spacer(1,3*mm),Paragraph("Search Coverage",styles["Heading2"]),
                  Paragraph(escape(coverage_note or "Patent search coverage status was not recorded."),body),
                  Spacer(1,3*mm),Paragraph("Relevant Evidence",styles["Heading2"])])
    rows=[[Paragraph("<b>Source ID</b>",number),Paragraph("<b>Evidence</b>",body),Paragraph("<b>URL</b>",body)]]
    for item in relevant["relevant_evidence"]:
        url=item["canonical_url"]; href=escape(url).replace('"','&quot;')
        display_description=_display_evidence_description(item["description"])
        rows.append([Paragraph(escape(str(item["source_id"])),number),Paragraph(escape(display_description),body),Paragraph(f'<link href="{href}" color="blue">{escape(url)}</link>',small)])
    table=LongTable(rows,colWidths=[19*mm,90*mm,59*mm],repeatRows=1,splitByRow=1,hAlign="LEFT")
    commands=[("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#8AA4B8")),("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(0,0),(0,-1),"CENTER"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]
    for row in range(2,len(rows),2): commands.append(("BACKGROUND",(0,row),(-1,row),colors.HexColor("#F6F9FB")))
    table.setStyle(TableStyle(commands)); story.extend([table,Spacer(1,3*mm),Paragraph("Applicability Mappings",styles["Heading2"])])
    mapping_rows=[[Paragraph("<b>Use Case</b>",body),Paragraph("<b>Customer Evidence / Readiness</b>",body),Paragraph("<b>Potential NNC Capability</b>",body)]]
    for mapping in final["applicability_mappings"]:
        mapping_rows.append([Paragraph(escape(str(mapping.get("use_case_id","")).replace("_"," ").title()),body),
            Paragraph(escape(mapping.get("customer_evidence_and_readiness","")),small),Paragraph(escape(mapping.get("nnc_product_capability","")),small)])
    if len(mapping_rows)==1: mapping_rows.append([Paragraph("No qualified mapping",body),Paragraph("No approved supporting evidence.",small),Paragraph("Not assessed",small)])
    mapping_table=LongTable(mapping_rows,colWidths=[43*mm,62*mm,63*mm],repeatRows=1,splitByRow=1,hAlign="LEFT")
    mapping_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#D9EAF7")),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#8AA4B8")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.extend([mapping_table,Spacer(1,2*mm),Paragraph("Authoritative dSPACE Portfolio Sources",styles["Heading2"])])
    for ref in references:
        pages=str(ref["page_start"]) if ref["page_start"]==ref["page_end"] else f"{ref['page_start']}-{ref['page_end']}"
        story.append(Paragraph("&#8226; "+escape(f"{ref['source_filename']}, page {pages}, section: {ref['section']}, chunk: {ref['chunk_id']}"),bullet))
    destination=out/identity["report_filename"]
    SimpleDocTemplate(str(destination),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=16*mm,bottomMargin=16*mm,title=f"Sales Assessment: {final['company_name']}").build(story)
    return destination
