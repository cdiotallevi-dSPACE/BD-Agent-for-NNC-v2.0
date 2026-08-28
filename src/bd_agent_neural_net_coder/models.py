from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl

Scope = Literal["target_company", "neutral_engineering_need", "dspace_portfolio"]

class Source(BaseModel):
    source_id: str
    url: HttpUrl
    title: str = ""
    source_type: str = "web"
    retrieved_at: str
    content_hash: str
    official: bool = False

class Evidence(BaseModel):
    evidence_id: str
    entity_scope: Scope
    claim: str
    passage: str
    source_id: str
    taxonomy_term_id: str
    evidence_status: Literal["confirmed", "inferred", "unknown", "contradicted"]
    assessment: Literal["accepted", "rejected", "ambiguous"]
    confidence: float = Field(ge=0, le=1)
    claim_fingerprint: str
    rejection_reason: str | None = None

class ApplicabilityMapping(BaseModel):
    mapping_id: str
    target_company_entity_id: str
    engineering_need_id: str
    dspace_capability_id: str
    dspace_portfolio_item_id: str
    target_company_evidence_ids: list[str]
    supporting_dspace_document_chunk_ids: list[str]
    applicability_relations: list[str]
    hard_rule_passed: bool
    dspace_applicability_score: float = Field(ge=0, le=100)

