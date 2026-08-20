from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain import fair_price_range, quotation_risk_flags, smart_match_score
from app.models import AIAnalysis, AIRiskFlag
from app.schemas import FairPriceRequest, NaturalLanguageRequirement, RiskCheckRequest, SmartMatchRequest
from app.services.ai import OptionalGeminiService

router=APIRouter(prefix="/api/v1/ai",tags=["ai"])


@router.post("/extract-requirement")
async def extract_requirement(payload:NaturalLanguageRequirement,db:AsyncSession=Depends(get_db))->dict[str,object]:
    output,fallback=await OptionalGeminiService().extract_requirement(payload.text)
    db.add(AIAnalysis(analysis_type="requirement_extraction",provider="rules" if fallback else "gemini",input_snapshot={"text":payload.text},output=output,fallback_used=fallback))
    return output


@router.post("/smart-match")
async def smart_match(payload:SmartMatchRequest)->list[dict[str,str]]:
    ranked=[{"id":item.id,"score":str(smart_match_score(item.route_score,item.capacity_fit,item.rating,item.cancellation_percent,item.completed_trips,item.price_index))} for item in payload.candidates]
    return sorted(ranked,key=lambda item:float(item["score"]),reverse=True)


@router.post("/fair-price")
async def fair_price(payload:FairPriceRequest,db:AsyncSession=Depends(get_db))->dict[str,str]:
    try:low,high,source=fair_price_range(payload.historical_prices,payload.fallback_per_km_tonne,payload.distance_km,payload.weight_tonnes)
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc)) from exc
    result={"low":str(low),"high":str(high),"currency":"INR","source":source,"label":"estimate_not_guarantee"}
    db.add(AIAnalysis(analysis_type="fair_price",provider="rules",input_snapshot={key:str(value) for key,value in payload.model_dump().items()},output=result,fallback_used=True))
    return result


@router.post("/quotation-risk")
async def quotation_risk(payload:RiskCheckRequest,db:AsyncSession=Depends(get_db))->dict[str,object]:
    flags=quotation_risk_flags(payload.price,payload.fair_low,payload.fair_high,payload.cancellation_percent,payload.dispute_count)
    if payload.quote_id:
        for code in flags:db.add(AIRiskFlag(quote_id=payload.quote_id,flag_code=code,severity="review",explanation=f"Rule-based flag: {code.replace('_',' ')}. Administrator review required."))
    return {"flags":flags,"action":"admin_review" if flags else "none","auto_banned":False}
