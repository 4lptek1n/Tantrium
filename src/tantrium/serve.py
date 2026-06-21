"""Tantrium REST API — FastAPI tabanlı HTTP arayüzü (durumsuz saf-matematik).

Kullanım:
  python -m tantrium.serve              # 0.0.0.0:8000
  python -m tantrium.serve --port 9000
  uvicorn tantrium.serve:app --reload

Endpoint'ler (hepsi saf matematik, durumsuz):
  GET  /health · /status
  POST /ask            {query}                 → paradigma sertifikası
  POST /certify        {query}                 → UnifiedCertificate (RH bundle + mühür)
  POST /rh             {query}                 → tam RH sertifikası (τ/pivot/Stieltjes/χ/seal)
  POST /rh_distance    {a, b}                  → ayırt edici mesafe
  POST /transport      {source, target}        → sertifikalı dyadic+Sturm+Zeta geçiş
  POST /sturm          {poly}                  → Sturm zinciri
  POST /positivity     {poly}                  → Hankel PSD
  POST /jensen         {sequence}              → Laguerre-Pólya hiperbolisite
  POST /bezoutian      {coeffs}                → Bezoutian/Lah/ilk-beş-pivot
  POST /free_entropy   {query}                 → serbest entropi χ
  POST /reconstruct    {moments}               → momentlerden ölçü
  POST /discover_law   {series}                → yönetici yasa + tahmin
  POST /seal           {query} / /verify {sealed} → mühür + tamper-tespiti
"""
from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False
    FastAPI = object  # type: ignore
    BaseModel = object  # type: ignore

import tantrium

app = FastAPI(title="Tantrium API", version="2.0") if _FASTAPI_OK else None
_ai: "tantrium.AI | None" = None


def _get_ai() -> "tantrium.AI":
    global _ai
    if _ai is None:
        _ai = tantrium.AI()
    return _ai


if _FASTAPI_OK:
    class QueryReq(BaseModel):
        query: str

    class PairReq(BaseModel):
        a: str
        b: str

    class TransportReq(BaseModel):
        source: str
        target: str

    class PolyReq(BaseModel):
        poly: str

    class CoeffReq(BaseModel):
        coeffs: list[float]

    class SeqReq(BaseModel):
        sequence: list[float]

    class SeriesReq(BaseModel):
        series: list[float]

    class MomentsReq(BaseModel):
        moments: list[float]

    class SealedReq(BaseModel):
        sealed: dict

    @app.get("/health")
    def health():
        return {"status": "ok", "fastapi": True, "machine": "pure-math"}

    @app.get("/status")
    def status():
        return {"status": _get_ai().status()}

    @app.post("/ask")
    def ask(req: QueryReq):
        r = _get_ai().ask(req.query)
        return {"query": getattr(r, "query", req.query),
                "certified": getattr(r, "certified", None),
                "paradigms_passed": getattr(r, "paradigms_passed", None),
                "paradigms_total": getattr(r, "paradigms_total", None),
                "summary": str(r)}

    @app.post("/certify")
    def certify(req: QueryReq):
        c = _get_ai().certify_all(req.query)
        return {"name": c.name, "paradigms_passed": c.paradigms_passed,
                "paradigms_total": c.paradigms_total, "coherent": c.coherent,
                "rh_grade": c.rh_grade, "rh_rank": c.rh_rank,
                "rh_stieltjes": c.rh_stieltjes, "rh_hausdorff": c.rh_hausdorff,
                "rh_free_entropy": c.rh_free_entropy, "sealed_hash": c.sealed_hash,
                "summary": str(c)}

    @app.post("/rh")
    def rh(req: QueryReq):
        return _get_ai().rh_certificate(req.query).as_dict()

    @app.post("/rh_distance")
    def rh_distance(req: PairReq):
        return {"a": req.a, "b": req.b, "distance": _get_ai().rh_distance(req.a, req.b)}

    @app.post("/transport")
    def transport(req: TransportReq):
        tc = _get_ai().transport(req.source, req.target)
        return {"source": req.source, "target": req.target, "summary": tc.summary()
                if hasattr(tc, "summary") else str(tc),
                "certified": getattr(tc, "certified", None)}

    @app.post("/sturm")
    def sturm(req: PolyReq):
        return {"poly": req.poly, "result": str(_get_ai().sturm(req.poly))}

    @app.post("/positivity")
    def positivity(req: PolyReq):
        return {"poly": req.poly, "result": str(_get_ai().positivity(req.poly))}

    @app.post("/jensen")
    def jensen(req: SeqReq):
        return _get_ai().jensen(req.sequence).as_dict()

    @app.post("/bezoutian")
    def bezoutian(req: CoeffReq):
        r = _get_ai().bezoutian(req.coeffs)
        return r.as_dict() if hasattr(r, "as_dict") else {"summary": str(r)}

    @app.post("/free_entropy")
    def free_entropy(req: QueryReq):
        return {"query": req.query, "free_entropy": _get_ai().free_entropy(req.query),
                "semicircle_distance": _get_ai().semicircle_distance(req.query)}

    @app.post("/reconstruct")
    def reconstruct(req: MomentsReq):
        return {"result": str(_get_ai().reconstruct(req.moments))}

    @app.post("/discover_law")
    def discover_law(req: SeriesReq):
        r = _get_ai().discover_law(req.series)
        return {"order": getattr(r, "order", None), "summary": str(r)}

    @app.post("/seal")
    def seal(req: QueryReq):
        return _get_ai().seal(req.query)

    @app.post("/verify")
    def verify(req: SealedReq):
        return _get_ai().verify(req.sealed)


def main() -> None:
    """CLI giriş noktası (tantrium-serve)."""
    import argparse
    if not _FASTAPI_OK:
        print("FastAPI kurulu değil. Kurmak için: pip install 'tantrium[server]'")
        raise SystemExit(1)
    import uvicorn
    parser = argparse.ArgumentParser(description="Tantrium API Sunucusu")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    print(f"Tantrium API başlatılıyor: http://{args.host}:{args.port}")
    uvicorn.run("tantrium.serve:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
