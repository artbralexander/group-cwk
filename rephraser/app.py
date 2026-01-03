from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import re

app = FastAPI(title="Rephraser", version="1.0.0")


class GroupFact(BaseModel):
    group_id: int
    group_name: str
    currency: str
    paid: float
    owed: float
    net: float


class FactsPayload(BaseModel):
    overall_paid: float
    overall_owed: float
    overall_net: float
    groups: List[GroupFact] = Field(default_factory=list)

    
    top_categories_owed: Optional[list] = None


class RephraseRequest(BaseModel):
    facts: FactsPayload
    max_sentences: int = Field(default=2, ge=1, le=2)


class RephraseResponse(BaseModel):
    summary: str
    mode: str  


def _fmt_money(value: float) -> str:
    
    return f"{value:.2f}"


def _choose_top_group(groups: List[GroupFact]) -> Optional[GroupFact]:
    if not groups:
        return None
    
    return sorted(groups, key=lambda g: abs(g.net), reverse=True)[0]


def _template_summary(facts: FactsPayload, max_sentences: int) -> str:
    
    if not facts.groups:
        
        line = f"You have no group activity yet (paid {_fmt_money(facts.overall_paid)}, owed {_fmt_money(facts.overall_owed)})."
        return line

    top = _choose_top_group(facts.groups)
    if top is None:
        line = f"Across your groups you paid {_fmt_money(facts.overall_paid)} and owed {_fmt_money(facts.overall_owed)} (net {_fmt_money(facts.overall_net)})."
        return line

    
    s1 = (
        f"Across your groups you paid {_fmt_money(facts.overall_paid)} and owed "
        f"{_fmt_money(facts.overall_owed)} (net {_fmt_money(facts.overall_net)})."
    )

    
    direction = "ahead" if top.net >= 0 else "behind"
    s2 = (
        f"In “{top.group_name}”, you paid {_fmt_money(top.paid)} and owed {_fmt_money(top.owed)} "
        f"({direction} by {_fmt_money(abs(top.net))} {top.currency})."
    )

    return s1 if max_sentences == 1 else f"{s1} {s2}"


@app.post("/rephrase", response_model=RephraseResponse)
def rephrase(req: RephraseRequest):
    facts = req.facts

    
    if facts.overall_paid < 0 or facts.overall_owed < 0:
        raise HTTPException(status_code=400, detail="overall values must be non-negative")

    summary = _template_summary(facts, req.max_sentences)

    
    summary = re.sub(r"\s+", " ", summary).strip()

    return RephraseResponse(summary=summary, mode="template")


@app.get("/health")
def health():
    return {"ok": True}