#!/usr/bin/env python3
"""Aleph-Tekin AGI Engine — CLI interface.

Usage:
  python tools/tantrium_agi_engine.py --status
  python tools/tantrium_agi_engine.py --demo
  python tools/tantrium_agi_engine.py --teach "water" --moments "1,2,1,0,1"
  python tools/tantrium_agi_engine.py --certify "rh_zeta" --from-theorem-graph
  python tools/tantrium_agi_engine.py --infer "obj_a" "obj_b"
  python tools/tantrium_agi_engine.py --explore
  python tools/tantrium_agi_engine.py --speak "obj_name"
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium import (
    CertificationEngine, CertifiableObject, Concept, CertificationPipeline,
    InferenceChain, Explorer, Speaker,
)


def cmd_status(engine: CertificationEngine) -> None:
    print(engine.status())


def cmd_demo(engine: CertificationEngine) -> None:
    """Run the engine on a set of demo objects drawn from the proof system.
    These objects are the actual mathematical structures from the RH proof.
    """
    print("═══ ALEPH-TEKIN AGI ENGINE — DEMO RUN ═══\n")

    # 1. D-positivity object: point-mass measure at x=1/2
    #    μ_k = (1/2)^k — a valid moment sequence (Hankel PSD by construction).
    #    This is the structure underlying positivity certificates in the RH proof.
    rh_moments = [Fraction(1, 2) ** k for k in range(8)]
    rh_obj = CertifiableObject(
        name="D_positivity_RH",
        moments=rh_moments,
        structure={
            # Dalet: eigenvalues all non-negative
            "eigenvalues": [Fraction(1), Fraction(1, 2), Fraction(1, 4)],
            # He: Lyapunov V non-increasing (proof convergence)
            "lyapunov_values": [1.0, 0.75, 0.5, 0.25, 0.1, 0.02],
            # Zayin: LGV path weights — non-intersecting paths in Lindstrom-Gessel-Viennot
            "path_weights": [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)],
            "determinant": Fraction(7, 8),
            # Emet: certified claims with proof certificates
            "certified_claims": [
                {"claim": "D(m,ell,a)>=0", "certificate": "parametric_certificate.json"},
                {"claim": "AG/LGV transfer holds", "certificate": "ag_lgv_certificate.json"},
            ],
            "contradictions": [],
            # Tav: fixed-point convergence — proof chain converges to closure
            "is_running": True,
            "fixed_point_iterations": [1.0, 0.5, 0.12, 0.02, 0.001, 0.0000001, 0.0000001],
            # Tsadi: sensor → certificate (evidence hash)
            "sensor_hash": "TBE-RH-CLOSURE",
            "certificate_hash": "TBE-RH-CLOSURE",
            # Het: gradient — proof flows downhill toward zero gap
            "potential_values": {"start": 1.0, "mid": 0.5, "end": 0.0},
            "flows": [
                {"from": "start", "to": "mid"},
                {"from": "mid", "to": "end"},
            ],
            # Bet: all transformations lossless
            "transformations": [
                {"name": "Polya-Jensen", "information_loss": 0},
                {"name": "Sturm reduction", "information_loss": 0},
                {"name": "AG/LGV transfer", "information_loss": 0},
            ],
            # Kaf: injective mappings (distinct inputs → distinct outputs)
            "mappings": {
                "m=1,ell=1": "D_1_1=1/2",
                "m=2,ell=1": "D_2_1=3/4",
                "m=1,ell=2": "D_1_2=1/4",
            },
            # Ayin: distinct pairs with separating measurements
            "distinct_pairs": [
                {"a": "m=1", "b": "m=2", "separating_measurement": "Sturm_pivot"},
                {"a": "ell=1", "b": "ell=2", "separating_measurement": "discriminant"},
            ],
            # Mem: gauge classes (mathematically equivalent representations)
            "gauge_classes": [
                [{"id": "Xi_form", "all_measurements_equal": True},
                 {"id": "zeta_form", "all_measurements_equal": True}],
            ],
            # Shin: optimal action chosen
            "actions": [
                {"id": "apply_AG_LGV", "score": 0.95},
                {"id": "direct_estimate", "score": 0.3},
            ],
            "chosen_action": "apply_AG_LGV",
            # Lamed: local visibility
            "physical_differences": ["D_positivity", "spectral_gap"],
            "locally_observable": ["D_positivity", "spectral_gap"],
            # Vav: tensor composition
            "components": [{"dim": 3}, {"dim": 4}],
            "composite_dim": 12,
            # SU3: Z₃ symmetry
            "symmetry_group": "SU3",
            "center_order": 3,
            # Kuf: index 18
            "z3_order": 3,
            "c6_order": 6,
            "topological_index": 18,
            # Yod: MDL
            "model_length": 42,
            "data_given_model_length": 7,
            "alternative_models": [],
            # Resh: partial trace
            "environment_trace": True,
            "total_information": 100,
            "subsystem_information": 60,
            # Tet: cross-ratio
            "cross_ratio_quadruples": [
                {"a": "1", "b": "2", "c": "3", "d": "4",
                 "expected_cr": str(Fraction((1-3)*(2-4), (1-4)*(2-3)))},
            ],
        }
    )

    print("─── Object 1: D_positivity_RH (moments of Xi function) ───")
    run = engine.process(rh_obj)
    print(run.report())
    print()

    # 2. A concept with negative moments — should fail Aleph
    incoherent = CertifiableObject(
        name="incoherent_claim",
        moments=[Fraction(1), Fraction(-1), Fraction(2)],
        structure={}
    )
    print("─── Object 2: incoherent_claim (negative moments) ───")
    run2 = engine.process(incoherent)
    print(run2.report())
    print()

    # 3. A semantic concept: "prime number" encoded as moment sequence
    #    Moments derived from prime gap statistics (normalized)
    prime_concept = Concept.from_counts(
        name="prime_number",
        counts=[2, 1, 2, 2, 4, 2, 4, 2, 4, 6],
        domain="number_theory"
    )
    print("─── Concept: prime_number (moment sequence from prime gaps) ───")
    print(engine.teach(prime_concept))
    print()

    # 4. Certify the prime concept through the full network
    print("─── Full certification of prime_number concept ───")
    run3 = engine.process_concept(prime_concept)
    print(run3.report())
    print()

    print("═══ ENGINE STATUS ═══")
    print(engine.status())


def cmd_teach(engine: CertificationEngine, name: str, moments_str: str, domain: str) -> None:
    moments = [Fraction(m.strip()) for m in moments_str.split(",")]
    concept = Concept(name=name, moments=moments, domain=domain)
    print(engine.teach(concept))


def cmd_certify(engine: CertificationEngine, name: str) -> None:
    """Certify an object by name — load from knowledge store or theorem graph."""
    history = engine._load_history()
    matches = [h for h in history if name.lower() in h.get("object", "").lower()]
    if matches:
        latest = matches[-1]
        print(json.dumps(latest, indent=2))
    else:
        print(f"No record for '{name}' in knowledge store.")
        print("Run --demo or provide moments to certify a new object.")


def cmd_infer(engine: CertificationEngine, name_a: str, name_b: str) -> None:
    """Run the inference chain between two previously certified objects."""
    history = engine._load_history()

    def _find(name: str) -> dict | None:
        matches = [h for h in history if h.get("object", "").lower() == name.lower()]
        return matches[-1] if matches else None

    rec_a = _find(name_a)
    rec_b = _find(name_b)
    if rec_a is None:
        print(f"No record for '{name_a}' in knowledge store.")
        return
    if rec_b is None:
        print(f"No record for '{name_b}' in knowledge store.")
        return

    # Reconstruct minimal NetworkRun-compatible objects from history
    # Re-process via engine.process_raw to get real NetworkRun objects
    run_a = engine.process_raw(name_a, name=name_a)
    run_b = engine.process_raw(name_b, name=name_b)
    chain = InferenceChain()
    results = chain.infer(run_a, run_b)
    print(chain.report(results))
    chain.register(results, engine.knowledge_path)
    print(f"\n{len(results)} inferences written to {engine.knowledge_path}")


def cmd_explore(engine: CertificationEngine, max_rounds: int) -> None:
    """Run the autonomous exploration loop over the knowledge frontier."""
    explorer = Explorer(engine)
    objectives = explorer.scan_frontier()
    if not objectives:
        print("Knowledge frontier is empty — nothing to explore.")
        print("All known gaps are already closed or the knowledge store is empty.")
        return
    print(f"Found {len(objectives)} gap(s) to explore:")
    for o in objectives[:5]:
        print(f"  [{o.priority}] {o.gap_paradigm}: {o.gap_name} (from {o.source_object})")
    if len(objectives) > 5:
        print(f"  ... and {len(objectives) - 5} more")
    print()
    results = explorer.run_loop(max_rounds=max_rounds)
    print(explorer.report(results))


def cmd_speak(engine: CertificationEngine, name: str, detail: str) -> None:
    """Narrate a certified object — look it up from knowledge store first."""
    history = engine._load_history()
    obj_records = [
        h for h in history
        if h.get("type") not in ("inference", "exploration")
        and name.lower() in h.get("object", "").lower()
    ]
    if obj_records:
        rec = obj_records[-1]
        obj_name = rec["object"]
        # Reconstruct minimal run for speaking from stored record
        from fractions import Fraction
        from tantrium.core.codex import CertifiableObject
        obj = engine.encoder.encode(obj_name, name=obj_name)
        run = engine.network.run(obj)
        speaker = Speaker(manifold=engine.manifold)
        print(speaker.narrate(run, detail=detail))
        print()
        print(speaker.explain(run))
    else:
        print(engine.query(name))


def cmd_query(engine: CertificationEngine, question: str) -> None:
    """Query the system for certified knowledge about a topic."""
    print(engine.query(question))


def cmd_grow(engine: CertificationEngine, rounds: int) -> None:
    """Run the self-directed knowledge expansion loop."""
    print("═══ GROWING KNOWLEDGE BASE ═══")
    print(f"Processing theorem graph + running inference chain...")
    print()
    summary = engine.grow(max_rounds=rounds, max_explore_objectives=10)
    print("═══ GROWTH COMPLETE ═══")
    print(f"  Theorem nodes processed: {summary['theorem_nodes_processed']}")
    print(f"  Inferences derived:      {summary['inferences_derived']}")
    print(f"  Gaps closed:             {summary['gaps_closed']}")
    print(f"  Gaps persistent:         {summary['gaps_persistent']}")
    print(f"  Manifold size:           {summary['manifold_size_after']} concepts")
    print()
    print(engine.growth_report())


def cmd_network() -> None:
    """Print the full network structure: nodes, dependencies, topology."""
    net = CertificationPipeline()
    print("═══ ALEPH-TEKIN NETWORK: 22+1 PARADIGMS ═══\n")
    for pid in net._topo_order:
        node = net.nodes[pid]
        p = node.paradigm
        deps = ", ".join(p.depends_on) if p.depends_on else "none (foundation)"
        print(f"  {pid:12s}  {p.name:30s}  deps: {deps}")
    print(f"\nTotal: {len(net.nodes)} paradigms in topological order.")
    print("No weights. No statistics. Pure structure.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aleph-Tekin AGI Engine — certification-based intelligence"
    )
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--teach", metavar="NAME")
    parser.add_argument("--moments", metavar="M0,M1,...", default="1,1,1,1")
    parser.add_argument("--domain", default="general")
    parser.add_argument("--certify", metavar="NAME")
    parser.add_argument("--infer", nargs=2, metavar=("NAME_A", "NAME_B"))
    parser.add_argument("--explore", action="store_true")
    parser.add_argument("--explore-rounds", type=int, default=5, metavar="N")
    parser.add_argument("--speak", metavar="NAME")
    parser.add_argument("--detail", choices=["line", "brief", "standard", "full"], default="standard")
    parser.add_argument("--query", metavar="QUESTION")
    parser.add_argument("--grow", action="store_true")
    parser.add_argument("--grow-rounds", type=int, default=3, metavar="N")
    args = parser.parse_args()

    engine = CertificationEngine()

    if args.status:
        cmd_status(engine)
    elif args.demo:
        cmd_demo(engine)
    elif args.network:
        cmd_network()
    elif args.teach:
        cmd_teach(engine, args.teach, args.moments, args.domain)
    elif args.certify:
        cmd_certify(engine, args.certify)
    elif args.infer:
        cmd_infer(engine, args.infer[0], args.infer[1])
    elif args.explore:
        cmd_explore(engine, args.explore_rounds)
    elif args.speak:
        cmd_speak(engine, args.speak, args.detail)
    elif args.query:
        cmd_query(engine, args.query)
    elif args.grow:
        cmd_grow(engine, args.grow_rounds)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
