from __future__ import annotations

import json
from datetime import date

import httpx

from app.core.config import settings
from app.domain import fallback_extract


class OptionalGeminiService:
    async def extract_requirement(self,text:str)->tuple[dict[str,object|None],bool]:
        if not settings.GEMINI_API_KEY:return fallback_extract(text),True
        schema={"type":"object","properties":{"quantity":{"type":["integer","null"]},"pickup":{"type":["string","null"]},"destination":{"type":["string","null"]},"pickup_date":{"type":["string","null"]},"time_period":{"type":["string","null"]},"weight":{"type":["number","null"]},"weight_unit":{"type":["string","null"]},"cargo_type":{"type":["string","null"]}},"required":["quantity","pickup","destination","pickup_date","time_period","weight","weight_unit","cargo_type"]}
        prompt=f"Extract an Indian road-logistics requirement. Resolve relative dates using today={date.today().isoformat()}. Do not invent missing values. Input: {text}"
        try:
            async with httpx.AsyncClient(timeout=18) as client:
                response=await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",headers={"x-goog-api-key":settings.GEMINI_API_KEY},json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json","responseSchema":schema}})
                response.raise_for_status();raw=response.json()["candidates"][0]["content"]["parts"][0]["text"]
                result=json.loads(raw);result.update({"confidence":"ai_extracted","requires_confirmation":True});return result,False
        except (httpx.HTTPError,KeyError,IndexError,json.JSONDecodeError):return fallback_extract(text),True
