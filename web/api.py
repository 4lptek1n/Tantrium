"""Tantrium ASI — Web API

FastAPI wrapper around tantrium.AI()
Serves the web UI and REST endpoints.
"""
from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys
import os

_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root / "src"))
os.chdir(str(_root))  # engine uses relative paths (results/agi/...)

import tantrium

# ── Singleton AI instance ────────────────────────────────────────────────────

_ai: tantrium.AI | None = None

def get_ai() -> tantrium.AI:
    global _ai
    if _ai is None:
        _ai = tantrium.AI()
    return _ai


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Tantrium ASI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Request models ───────────────────────────────────────────────────────────

class CertifyRequest(BaseModel):
    input: str

class TransportRequest(BaseModel):
    source: str
    target: str
    use_smiles: bool = False

class CompareRequest(BaseModel):
    a: str
    b: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    html = (Path(__file__).parent / "static" / "index.html").read_text()
    return HTMLResponse(html)


@app.get("/api/status")
async def status():
    ai = get_ai()
    n = len(ai.manifold.concepts)
    edges = sum(len(v) for v in ai.tau.edges.values())
    return {
        "concepts": n,
        "tau_edges": edges,
        "paradigms": 23,
        "status": "OPERATIONAL",
    }


@app.post("/api/certify")
async def certify(req: CertifyRequest):
    t0 = time.monotonic()
    ai = get_ai()

    obj = ai.engine.encoder.encode(req.input, name=req.input[:64])
    run = ai.engine.network.run(obj)

    paradigm_results = {}
    for pid, node in run.nodes.items():
        paradigm_results[pid] = {
            "status": node.status,
            "gap": node.result.gap_name if node.result and node.status == "BLOCKED" else None,
        }

    spec = ai.spectrum(req.input)
    anchors = ai.anchor_of(req.input, top_n=3)

    from tantrium.core.semantic import Concept
    concept = Concept(name=req.input[:64], moments=list(obj.moments), domain="input")
    nearest = []
    if ai.manifold.concepts:
        nearest = [n for n, _ in ai.manifold.nearest(concept, n=5)]

    # ── Plain-language result ────────────────────────────────────────────────
    certified = run.certified_count == run.total
    top_anchor = anchors[0][0] if anchors else "unknown"
    top_anchor_dist = anchors[0][1] if anchors else 0.0

    _anchor_meaning = {
        "ZETA_ZEROS":        "Riemann zeta zeros — prime number structure",
        "GUE_RANDOM_MATRIX": "Random matrix (GUE) — quantum-level complexity",
        "PRIME_GAPS":        "Prime gap distribution — number theory",
        "POISSON_PROCESS":   "Poisson process — independent random events",
        "GAUSSIAN_BELL":     "Gaussian distribution — normal variation",
        "PERIODIC_LATTICE":  "Periodic / wave structure",
        "UNIFORM_MEASURE":   "Uniform distribution — flat structure",
        "EXPONENTIAL_DECAY": "Exponential decay — rapid convergence",
        "LINEAR_RAMP":       "Linear / arithmetic structure",
        "GEOMETRIC_GROWTH":  "Geometric growth — exponential scaling",
    }
    anchor_meaning = _anchor_meaning.get(top_anchor, top_anchor)

    rank = spec.effective_rank()
    gaps = [pid for pid, r in paradigm_results.items() if r["status"] == "BLOCKED"]

    if certified:
        verdict = f'"{req.input}" exists in mathematical reality.'
        finding = (
            f"Its structure belongs to the {anchor_meaning} family "
            f"(spectral distance {top_anchor_dist:.3f}). "
            f"It occupies {rank:.1f} effective dimensions in moment space. "
            f"All 23 mathematical paradigms are satisfied — no gaps."
        )
        if nearest:
            finding += f" Nearest known structures: {', '.join(nearest[:3])}."
    else:
        verdict = f'"{req.input}" has {len(gaps)} open mathematical question(s).'
        finding = (
            f"It partially certifies ({run.certified_count}/{run.total} paradigms). "
            f"Open gaps: {', '.join(gaps)}. "
            f"Closest mathematical family: {anchor_meaning}."
        )

    return {
        "input": req.input,
        "certified": certified,
        "verdict": verdict,
        "finding": finding,
        "paradigms_passed": run.certified_count,
        "paradigms_total": run.total,
        "paradigm_results": paradigm_results,
        "moments": [float(m) for m in obj.moments],
        "eigenvalues": spec.eigenvalues[:4],
        "entropy": round(spec.entropy(), 4),
        "effective_rank": round(rank, 2),
        "spectral_gap": round(spec.gap(), 4),
        "nearest_anchors": [{"name": n, "distance": round(d, 4)} for n, d in anchors],
        "nearest_concepts": nearest[:5],
        "duration_ms": round((time.monotonic() - t0) * 1000, 1),
    }


@app.post("/api/transport")
async def transport(req: TransportRequest):
    t0 = time.monotonic()
    ai = get_ai()
    tc = ai.transport(req.source, req.target, use_smiles=req.use_smiles)

    zeta = round(float(tc.zeta_distance), 4)

    if tc.certified:
        verdict = f"A mathematically certified path exists from \"{req.source}\" to \"{req.target}\"."
        finding = (
            f"The path stays entirely within the real-measure manifold. "
            f"Dyadic mass coverage: exact. Sturm chain: positive throughout. "
            f"Distance from Riemann zero family: {zeta}. "
            f"This connection is not a guess — it is proven."
        )
    elif not tc.dyadic_verified:
        verdict = f"No certified path from \"{req.source}\" to \"{req.target}\"."
        finding = (
            f"Dyadic transport failed: the mass distributions cannot be exactly covered. "
            f"These two structures live in incompatible regions of mathematical reality."
        )
    else:
        verdict = f"Path exists but leaves the real-measure manifold."
        finding = (
            f"Dyadic coverage succeeded but the Sturm chain breaks — "
            f"the interpolation path passes through non-real territory. "
            f"The connection is not certifiable."
        )

    return {
        "source": req.source,
        "target": req.target,
        "certified": tc.certified,
        "verdict": verdict,
        "finding": finding,
        "dyadic_verified": tc.dyadic_verified,
        "sturm_verified": tc.sturm_verified,
        "zeta_distance": zeta,
        "duration_ms": round((time.monotonic() - t0) * 1000, 1),
    }


@app.post("/api/compare")
async def compare(req: CompareRequest):
    ai = get_ai()
    result = ai.compare(req.a, req.b)
    return {"result": result}


@app.post("/api/anchor")
async def anchor(req: CertifyRequest):
    ai = get_ai()
    anchors = ai.anchor_of(req.input, top_n=5)
    return {
        "input": req.input,
        "anchors": [{"name": n, "distance": round(d, 4)} for n, d in anchors],
    }


@app.get("/api/topology")
async def topology():
    ai = get_ai()
    regions = ai.topology(grid_n=10)
    dense = sum(1 for r in regions if r.classification == "dense")
    frontier = sum(1 for r in regions if r.classification == "frontier")
    void = sum(1 for r in regions if r.classification == "void")
    return {
        "dense": dense,
        "frontier": frontier,
        "void": void,
        "total": len(regions),
    }
