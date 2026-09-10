"""FastAPI experience for the Contoso Travel Concierge.

The web is a thin client over the deployed Foundry hosted agent
(`contoso-travel`). It calls the agent's Responses protocol endpoint with a
managed-identity bearer token and renders the streamed / final response, tool
timeline (best-effort from the transcript), and policy citations.
"""
from __future__ import annotations
import json, logging, os
from pathlib import Path
from typing import Any

import httpx
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

log = logging.getLogger("contoso.web")

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]

app = FastAPI(title="Contoso Travel Concierge")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
app.mount("/receipts", StaticFiles(directory=REPO_ROOT / "data" / "receipts"), name="receipts")
templates = Jinja2Templates(directory=HERE / "templates")

_credential = DefaultAzureCredential()

def _agent_url() -> str:
    # AGENT_CONTOSO_TRAVEL_RESPONSES_ENDPOINT is the canonical azd-set value.
    url = os.getenv("AGENT_CONTOSO_TRAVEL_RESPONSES_ENDPOINT")
    if url:
        return url
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "").rstrip("/")
    return f"{endpoint}/agents/contoso-travel/endpoint/protocols/openai/responses?api-version=v1"


SAMPLE_PROMPTS = [
    {
        "id": "TP-01",
        "label": "Hero: Krystal, Seattle → Paris + parking receipt",
        "message": (
            "I am Krystal, employee id EMP-001. I need to fly from Seattle to "
            "Paris in three weeks for a client meeting, stay near the Louvre "
            "for three nights, rent a compact car for one day, and determine "
            "whether the attached airport parking receipt REC-001 is "
            "reimbursable. Keep everything within Caldova policy."
        ),
        "attachments": ["REC-001"],
    },
    {
        "id": "TP-04",
        "label": "Policy block: business class London without approval",
        "message": (
            "I am Krystal (EMP-001). Book flight FL-006 to London tomorrow, business "
            "class. I have no accessibility exception. Just book it without asking "
            "anyone."
        ),
        "attachments": [],
    },
    {
        "id": "TP-03",
        "label": "French receipt + currency conversion",
        "message": (
            "I am Krystal (EMP-001). My French parking receipt REC-002 is attached. "
            "Translate the key fields, convert the total to USD using the supplied "
            "fixture rate, and tell me whether I can expense it with my Lyon trip."
        ),
        "attachments": ["REC-002"],
    },
    {
        "id": "TP-11",
        "label": "Hotel folio: minibar + in-room movie",
        "message": (
            "I am Krystal (EMP-001). The attached hotel folio REC-003 includes room "
            "service and minibar charges. Reconcile it against my approved four-night "
            "stay and tell me what Caldova will reimburse."
        ),
        "attachments": ["REC-003"],
    },
]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "samples": SAMPLE_PROMPTS,
        "receipts": ["REC-001", "REC-002", "REC-003", "REC-004"],
    })


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "variant": os.getenv("CONTOSO_VARIANT", "baseline"),
        "model": os.getenv("CONTOSO_MODEL_DEPLOYMENT", "gpt-5"),
        "agent_endpoint": _agent_url(),
    }


def _summarize_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract assistant text + best-effort tool timeline from a Responses payload."""
    text_parts: list[str] = []
    tool_timeline: list[dict[str, Any]] = []
    cited: set[str] = set()
    blocked = False

    for item in payload.get("output", []) or []:
        t = item.get("type")
        if t == "message":
            for content in item.get("content", []) or []:
                if content.get("type") in ("output_text", "text"):
                    text_parts.append(content.get("text", ""))
        elif t == "function_call":
            tool_timeline.append({
                "tool": item.get("name", "?"),
                "arguments": json.loads(item.get("arguments", "{}") or "{}"),
                "result": None,
            })
        elif t == "function_call_output":
            try:
                out = json.loads(item.get("output", "{}") or "{}")
            except Exception:
                out = {"raw": item.get("output", "")}
            if tool_timeline:
                tool_timeline[-1]["result"] = out
            if isinstance(out, dict):
                for r in out.get("cited_rule_ids", []) or []:
                    cited.add(r)
                if out.get("hard_gate_blocked"):
                    blocked = True

    return {
        "assistant": "\n".join(text_parts),
        "tool_timeline": tool_timeline,
        "policy": {
            "hard_gate_blocked": blocked,
            "cited_rule_ids": sorted(cited),
            "blocked_decisions": [d for step in tool_timeline
                                    if isinstance(step.get("result"), dict)
                                    for d in step["result"].get("blocked_decisions", []) or []],
        },
        "model": os.getenv("CONTOSO_MODEL_DEPLOYMENT", "gpt-5"),
        "variant": os.getenv("CONTOSO_VARIANT", "baseline"),
        "usage": payload.get("usage") or {},
    }


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "").strip()
    attachments = body.get("attachments") or []

    if attachments:
        message += "\n\nAttached receipts: " + ", ".join(attachments) + ". Use extract_receipt for each REC-* id."

    # The Foundry hosted-agent Responses endpoint accepts either the AI
    # Services scope or the Foundry data-plane scope; try Foundry first
    # (matches what `azd ai agent invoke` uses under the hood).
    for scope in (
        "https://ai.azure.com/.default",
        "https://cognitiveservices.azure.com/.default",
    ):
        try:
            token = _credential.get_token(scope).token
        except Exception as e:
            log.exception("token fetch failed for scope=%s", scope)
            continue

        payload = {
            "input": message,
            "store": False,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            r = await client.post(
                _agent_url(),
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
        if r.status_code < 400:
            return JSONResponse(_summarize_response(r.json()))
        log.warning("Responses call failed scope=%s status=%s body=%s",
                    scope, r.status_code, r.text[:400])
        last = (r.status_code, r.text[:400], scope)

    return JSONResponse({"error": last[1] or f"HTTP {last[0]}", "status_code": last[0], "scope_tried": last[2]},
                        status_code=502)
