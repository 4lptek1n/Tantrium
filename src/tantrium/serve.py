"""Tantrium REST API — FastAPI tabanlı HTTP arayüzü.

Kullanım:
  python -m tantrium.serve              # 0.0.0.0:8000
  python -m tantrium.serve --port 9000
  uvicorn tantrium.serve:app --reload

Endpoint'ler:
  GET  /status
  POST /ask          {token}
  POST /learn        {text}
  POST /grounding    {token}
  POST /causal_chain {goal, depth=4}
  POST /what_if      {concept, depth=4}
  POST /analogy      {a, b, c, top_k=5}
  POST /hypothesize  {concept, depth=3}
  POST /visualize    {concept, depth=4, mode=ascii}
  POST /report       {topic, depth=3}
  POST /benchmark
  POST /bind_percept {concept, signal, modality=signal, paradigm=HAS_SIGNAL, name=null}
  POST /meaning_compose {text}
  POST /generate     {seed, steps=8, goal=null, lang=tr, use_meaning=false}
  GET  /health
"""
from __future__ import annotations

import json
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import PlainTextResponse
    from pydantic import BaseModel
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False
    FastAPI = object  # type: ignore
    BaseModel = object  # type: ignore

import tantrium

app = FastAPI(title="Tantrium AGI API", version="1.0") if _FASTAPI_OK else None
_ai: tantrium.AI | None = None


def _get_ai() -> tantrium.AI:
    global _ai
    if _ai is None:
        _ai = tantrium.AI()
    return _ai


if _FASTAPI_OK:
    class LearnReq(BaseModel):
        text: str

    class TokenReq(BaseModel):
        token: str

    class CausalReq(BaseModel):
        goal: str
        depth: int = 4

    class WhatIfReq(BaseModel):
        concept: str
        depth: int = 4

    class AnalogyReq(BaseModel):
        a: str
        b: str
        c: str
        top_k: int = 5

    class HypothesizeReq(BaseModel):
        concept: str
        depth: int = 3

    class VisualizeReq(BaseModel):
        concept: str
        depth: int = 4
        mode: str = "ascii"

    class ReportReq(BaseModel):
        topic: str
        depth: int = 3

    class BenchmarkReq(BaseModel):
        facts: list[list[str]] | None = None

    class BindPerceptReq(BaseModel):
        concept: str
        signal: list[float]
        modality: str = "signal"
        paradigm: str = "HAS_SIGNAL"
        name: str | None = None

    class MeaningComposeReq(BaseModel):
        text: str

    class GenerateReq(BaseModel):
        seed: str
        steps: int = 8
        goal: str | None = None
        lang: str = "tr"
        use_meaning: bool = False

    @app.get("/health")
    def health():
        return {"status": "ok", "fastapi": True}

    @app.get("/status")
    def status():
        ai = _get_ai()
        return ai.status()

    @app.post("/certify")
    def certify(req: TokenReq):
        c = _get_ai().certify_all(req.token)
        return {
            "query": req.token,
            "paradigms_passed": getattr(c, "paradigms_passed", None),
            "grounding": c.grounding,
            "grounding_score": c.grounding_score,
            "truth": c.truth,
            "truth_score": c.truth_score,
            "confidence": c.confidence,
            "coherent": c.coherent,
        }

    @app.post("/grounding")
    def grounding(req: TokenReq):
        cert = _get_ai().grounding(req.token)
        return {
            "token": cert.token,
            "verdict": cert.verdict,
            "score": cert.score,
            "direct_edges": cert.direct_edges,
            "grounded_neighbors": cert.grounded_neighbors,
            "summary": cert.summary(),
        }

    @app.post("/causal_chain")
    def causal_chain(req: CausalReq):
        return _get_ai().causal_chain(req.goal, depth=req.depth)

    @app.post("/what_if")
    def what_if(req: WhatIfReq):
        return _get_ai().what_if(req.concept, depth=req.depth)

    @app.post("/analogy")
    def analogy(req: AnalogyReq):
        results = _get_ai().analogy(req.a, req.b, req.c, top_k=req.top_k)
        return {"a": req.a, "b": req.b, "c": req.c,
                "results": [{"name": n, "distance": d} for n, d in results]}

    @app.post("/hypothesize")
    def hypothesize(req: HypothesizeReq):
        return _get_ai().hypothesize(req.concept, depth=req.depth)

    @app.post("/visualize", response_class=PlainTextResponse)
    def visualize(req: VisualizeReq):
        return _get_ai().visualize_causal(req.concept, depth=req.depth, mode=req.mode)

    @app.post("/benchmark")
    def benchmark(req: BenchmarkReq):
        facts = [tuple(f) for f in req.facts] if req.facts else None  # type: ignore
        return _get_ai().benchmark(facts)

    @app.post("/quantum_distance")
    def quantum_distance(a: str, b: str):
        return {"a": a, "b": b, "distance": _get_ai().quantum_distance(a, b)}

    @app.post("/synthesize")
    def synthesize(a: str, b: str):
        return {"result": _get_ai().synthesize(a, b)}

    @app.post("/entangle")
    def entangle(a: str, b: str):
        return _get_ai().entangle(a, b)

    @app.post("/bind_percept")
    def bind_percept(req: BindPerceptReq):
        import numpy as np
        signal = np.array(req.signal, dtype=float)
        percept_name = _get_ai().bind_percept(
            req.concept, signal,
            modality=req.modality,
            paradigm=req.paradigm,
            name=req.name,
        )
        return {"concept": req.concept, "percept_name": percept_name,
                "modality": req.modality, "paradigm": req.paradigm}

    @app.post("/meaning_compose")
    def meaning_compose(req: MeaningComposeReq):
        cs = _get_ai().meaning_compose(req.text)
        if cs is None:
            return {"text": req.text, "components": [], "moments": [],
                    "n_surface": 0, "summary": "Bileşen bulunamadı."}
        return {
            "text": req.text,
            "components": [{"name": c[0], "moments": [float(x) for x in c[1][:4]]}
                           for c in cs.components],
            "moments": [float(x) for x in cs.moments[:8]],
            "n_surface": cs.n_surface,
            "nearest": cs.nearest(n=5),
            "summary": str(cs),
        }


# CLI entry point
if __name__ == "__main__":
    import argparse
    if not _FASTAPI_OK:
        print("FastAPI kurulu değil. Kurmak için: pip install fastapi uvicorn")
        raise SystemExit(1)
    import uvicorn
    parser = argparse.ArgumentParser(description="Tantrium API Sunucusu")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    print(f"Tantrium API başlatılıyor: http://{args.host}:{args.port}")
    uvicorn.run("tantrium.serve:app", host=args.host, port=args.port, reload=args.reload)
