"""Tantrium ASI — Web API"""
from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys
import os

_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root / "src"))
os.chdir(str(_root))  # engine uses relative paths (results/agi/...)

import tantrium

_ai: tantrium.AI | None = None

def get_ai() -> tantrium.AI:
    global _ai
    if _ai is None:
        _ai = tantrium.AI()
    return _ai


app = FastAPI(title="Tantrium ASI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class CertifyRequest(BaseModel):
    input: str

class TransportRequest(BaseModel):
    source: str
    target: str
    use_smiles: bool = False

class CompareRequest(BaseModel):
    a: str
    b: str

class DiscoverRequest(BaseModel):
    target: str
    top_k: int = 6


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


@app.post("/api/discover")
async def discover(req: DiscoverRequest):
    t0 = time.monotonic()
    ai = get_ai()

    try:
        result = ai.discover(req.target, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    candidates = []
    for c in result.candidates:
        sdf_name = Path(c.sdf).name if c.sdf else None
        candidates.append({
            "name": c.name,
            "smiles": c.smiles,
            "certified": c.certified,
            "paradigms_passed": c.paradigms_passed,
            "paradigms_total": c.paradigms_total,
            "dyadic_score": float(c.dyadic_score) if c.dyadic_score else 0.0,
            "sdf_file": sdf_name,
            "has_3d": bool(c.sdf and Path(c.sdf).exists()),
        })

    best_name = result.best.name if result.best else None

    return {
        "target": req.target,
        "candidates": candidates,
        "best": best_name,
        "count": len(candidates),
        "certified_count": sum(1 for c in candidates if c["certified"]),
        "duration_s": round(result.duration_s, 2),
    }


@app.get("/api/download/{filename}")
async def download(filename: str):
    # Only allow .sdf files, no path traversal
    if "/" in filename or "\\" in filename or not filename.endswith(".sdf"):
        raise HTTPException(status_code=400, detail="Invalid filename")

    search_dirs = [
        _root / "results" / "molecules",
        _root / "results" / "agi",
    ]
    for d in search_dirs:
        f = d / filename
        if f.exists():
            return FileResponse(
                str(f),
                media_type="chemical/x-mdl-sdfile",
                filename=filename,
            )
    raise HTTPException(status_code=404, detail="File not found")


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

    certified = run.certified_count == run.total
    top_anchor = anchors[0][0] if anchors else "unknown"
    top_anchor_dist = anchors[0][1] if anchors else 0.0

    _anchor_meaning = {
        "ZETA_ZEROS":        "Prime number / Riemann zero family",
        "GUE_RANDOM_MATRIX": "Quantum-level complexity (GUE)",
        "PRIME_GAPS":        "Prime gap distribution",
        "POISSON_PROCESS":   "Independent random events (Poisson)",
        "GAUSSIAN_BELL":     "Normal distribution family",
        "PERIODIC_LATTICE":  "Periodic / wave structure",
        "UNIFORM_MEASURE":   "Flat / uniform structure",
        "EXPONENTIAL_DECAY": "Exponential decay",
        "LINEAR_RAMP":       "Linear / arithmetic structure",
        "GEOMETRIC_GROWTH":  "Geometric / exponential scaling",
    }
    anchor_meaning = _anchor_meaning.get(top_anchor, top_anchor)

    rank = spec.effective_rank()
    gaps = [pid for pid, r in paradigm_results.items() if r["status"] == "BLOCKED"]

    if certified:
        verdict = f'"{req.input}" is a verified mathematical structure.'
        finding = (
            f"Mathematical family: {anchor_meaning} (distance {top_anchor_dist:.3f}). "
            f"Dimensionality: {rank:.1f} effective dimensions. "
            f"All 23 paradigms certified."
        )
        if nearest:
            finding += f" Nearest known: {', '.join(nearest[:3])}."
    else:
        verdict = f'"{req.input}" has {len(gaps)} open mathematical question(s).'
        finding = (
            f"Partially certified ({run.certified_count}/{run.total} paradigms). "
            f"Open: {', '.join(gaps)}. "
            f"Closest family: {anchor_meaning}."
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
        verdict = f'Certified path: "{req.source}" → "{req.target}"'
        finding = (
            f"Mathematically proven connection. "
            f"Dyadic mass: exact. Sturm chain: positive. "
            f"Riemann zero distance: {zeta}."
        )
    elif not tc.dyadic_verified:
        verdict = f'No certified path: "{req.source}" → "{req.target}"'
        finding = "Dyadic transport failed — incompatible mathematical structures."
    else:
        verdict = f'Path exists but outside the real-measure manifold.'
        finding = f"Dyadic OK but Sturm chain breaks. Connection is not certifiable."

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
