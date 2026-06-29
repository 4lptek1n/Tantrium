"""Tantrium AI — sertifikasyon yüzeyi (CertifyMixin).

ask / certify / certify_all / paradigms / sturm / positivity / status / save /
grounding / truth / confidence / collisions.
"""
from __future__ import annotations

from ._results import AskResult, MolResult


class CertifyMixin:
    """23-paradigma sertifikasyon + 4-eksen + polinom pozitifliği metotları."""

    # ── Evrensel giriş noktası ───────────────────────────────────────────────

    def grounding(self, token: str) -> "object":
        """Topraklama sertifikası — token bilinen referanslara bağlı mı?

        Yapısal sertifika (23 paradigma) her şeyi geçirir; bu eksen ELER:
        GROUNDED (köklü/rezonans) | WEAKLY_GROUNDED | UNGROUNDED (anlamsız).
        """
        return self._engine.grounder.certify(token)

    def truth(self, name: str, n_neighbors: int = 6) -> "object":
        """Doğruluk ekseni (3.) — kavram komşularıyla TUTARLI mı, çelişiyor mu?

        Topraklama "bağlı mı?" der; doğruluk "çevresiyle tutarlı mı?" der.
        Transport tutarlılığı + EMET çapraz-kontrol → CONSISTENT/CONTESTED/CONTRADICTORY.

        Döner: TruthCertificate
        """
        from tantrium.core.truth import TruthCertifier
        return TruthCertifier(self._engine).certify(name, n_neighbors=n_neighbors)

    def confidence(self, query: str) -> "object":
        """Kalibre edilmiş tek güven — 4 ekseni (kapsama+margin+topraklama+doğruluk) birleştir.

        "23/23 ama margin 0.001" ile "23/23 margin 0.4" farkını tek sayıya indirir.
        Ağırlıklı geometrik ortalama: herhangi bir eksen çökerse güven çöker.

        Döner: Confidence (value, level, weakest_axis, ...)
        """
        from tantrium.core.confidence import calibrate
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.process(obj)
        gcert = self._engine.grounder.certify(query[:64], moments=list(obj.moments))
        try:
            from tantrium.core.truth import TruthCertifier
            tcert = TruthCertifier(self._engine).certify(query[:64], moments=list(obj.moments))
            truth_score = tcert.truth_score
        except Exception:
            truth_score = 0.5
        coverage = run.certified_count / run.total if run.total else 0.0
        margin = float(obj.structure.get("achilles_margin", 0.0) or 0.0)
        return calibrate(coverage, margin, gcert.score, truth_score)

    def collisions(
        self,
        n_samples: int = 200,
        epsilon: float = 1e-4,
        seed: int = 0,
    ) -> "object":
        """Çakışma avı — çekirdek iddianın ampirik testi.

        İki YAPISAL FARKLI girdi aynı 8 momente çöküyor mu? Sistemin kendi
        ayırt-etme gücünü saldırarak test eder. Çakışma → adaptif derinlik
        gereken nokta; çakışma yok → vaadin kanıtı.

        Döner: CollisionReport (collisions, collision_rate, claim_holds, ...)
        """
        from tantrium.core.collision import CollisionHunter
        return CollisionHunter(self._engine).hunt(
            n_samples=n_samples, epsilon=epsilon, seed=seed
        )

    def ask(self, query: str) -> AskResult:
        """Herhangi bir girdi → CoreMachine (tek geçiş, 4 eksen) → AskResult."""
        from tantrium.core.concept import Concept

        # ONE PASS: CoreMachine — encode, process, 4 axes all from shared state
        ucert = self._engine.core.certify(query, name=query[:64])
        run = ucert.evidence.get("run")

        concept = Concept(name=query[:64], moments=ucert.moments, domain="input")

        # Sertifika özeti — düz matematik özeti (dil katmanı yok)
        if run is not None:
            cert_summary = (
                f"'{query[:64]}' işlendi: "
                f"{ucert.paradigms_passed}/{ucert.paradigms_total} paradigma geçti"
                + (f"; boşluklar: {', '.join(ucert.gaps[:6])}" if ucert.gaps else "")
            )
        else:
            cert_summary = f"'{query[:64]}' işlendi."

        # Manifold konumu
        nearest: list[str] = []
        location_text = ""
        if self._engine.manifold.concepts:
            neighbors = self._engine.manifold.nearest(concept, n=5)
            nearest = [name for name, _ in neighbors]
            if nearest:
                location_text = f"Manifold komşuları: {', '.join(nearest[:3])}"

        answer = cert_summary
        if location_text:
            answer = f"{cert_summary}\n{location_text}"

        # Topraklama özeti — CoreMachine'in zaten hesapladığı sertifikayı yeniden kullan
        # (çift grounding hesabı YOK; gcert evidence'tan gelir)
        gcert = ucert.evidence.get("grounding_cert")
        if gcert is not None:
            answer = f"{answer}\n{gcert.summary()}"

        return AskResult(
            query=query,
            answer=answer,
            # certified = yapısal (geriye dönük uyumlu: paradigm coverage)
            certified=(ucert.paradigms_passed >= ucert.paradigms_total - 1),
            paradigms_passed=ucert.paradigms_passed,
            paradigms_total=ucert.paradigms_total,
            gaps=ucert.gaps,
            nearest=nearest,
            grounding=ucert.grounding,
            grounding_score=ucert.grounding_score,
            truth=ucert.truth,
            truth_score=ucert.truth_score,
            confidence=ucert.confidence,
            confidence_level=ucert.confidence_level,
            coherent=ucert.coherent,
        )

    def certify(
        self,
        name: str,
        smiles: str,
        target: str | None = None,
        save_3d: bool = True,
    ) -> MolResult:
        """Tek SMILES → Aleph sertifika + 3D SDF."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.core.encoder import encode_smiles
        from tantrium.core.transport import CertifiedTransport

        certifier = self._get_certifier()
        raw = encode_smiles(smiles, name=name)
        run = self._engine.network.run(raw)
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]

        # Dyadic transport score: use eigenvalue-based cells via full CertifiableObject
        ct = CertifiedTransport(self._engine)
        if target and target in self._engine.manifold.concepts:
            tgt_concept = self._engine.manifold.concepts[target]
            tc = ct.certify(raw, tgt_concept)
            dyadic = tc.transport_cost if tc.certified else 0.0
            transport_certified = tc.certified
        else:
            dyadic = certifier._dyadic_transport_score(raw.moments)
            transport_certified = dyadic > 0

        sdf = ""
        if save_3d:
            sdf = certifier._smiles_to_sdf(smiles, name, target or name, "results/molecules")

        # certified = all paradigms pass AND transport succeeds (if target given)
        pipeline_ok = run.certified_count == run.total
        certified = pipeline_ok and (transport_certified if target else True)

        return MolResult(
            name=name,
            smiles=smiles,
            certified=certified,
            paradigms_passed=run.certified_count,
            paradigms_total=run.total,
            dyadic_score=dyadic,
            sdf=sdf,
            gaps=gaps,
        )

    def certify_all(self, query: str, adaptive: bool = True) -> "object":
        """CoreMachine ile tam 4-eksenli sertifikasyon — UnifiedCertificate döner."""
        return self._engine.core.certify(query, adaptive=adaptive)

    def sturm(self, poly_str: str, var: str = "x") -> "object":
        """Polinom için Sturm zinciri — gerçek kök sayısı."""
        from tantrium.algebra.sturm import normalized_sturm_chain
        try:
            from sympy import symbols, sympify
            x = symbols(var)
            poly = sympify(poly_str)
            return normalized_sturm_chain([float(c) for c in poly.as_poly(x).all_coeffs()])
        except Exception as e:
            return {"error": str(e)}

    def positivity(self, poly_str: str, var: str = "x") -> dict:
        """Polinom pozitifliği — Hankel PSD kontrolü."""
        try:
            from sympy import symbols, sympify
            x = symbols(var)
            poly = sympify(poly_str)
            coeffs = [float(c) for c in poly.as_poly(x).all_coeffs()]
            obj = self._engine.encoder.encode(coeffs, name=poly_str[:32])
            run = self._engine.network.run(obj)
            return {"certified": run.certified_count == run.total,
                    "paradigms": run.certified_count, "coeffs": coeffs}
        except Exception as e:
            return {"error": str(e)}

    def paradigms(self, query: str) -> dict:
        """Her paradigmanın durumunu ve kanıt detayını döndür.

        Döner: dict — 23 paradigma her biri için:
          {paradigm_id: {"status": "CERTIFIED"|"BLOCKED"|"UNKNOWN",
                         "evidence": [...], "gap_name": str|None}}

        Örnek:
            result = ai.paradigms("EGFR")
            blocked = [p for p, v in result.items() if v["status"] == "BLOCKED"]
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        out: dict = {}
        for pid, node in run.nodes.items():
            result = node.result
            out[pid] = {
                "status": node.status,
                "evidence": list(result.evidence) if result else [],
                "gap_name": result.gap_name if result else None,
                "certificate": (
                    {k: str(v) for k, v in result.certificate.items()} if result else {}
                ),
            }
        return out

    def status(self) -> str:
        """Kısa durum özeti."""
        return (
            "Tantrium AI  |  durumsuz saf-matematik makinesi  |  "
            "Aleph-Tekin 23 paradigma"
        )

    def save(self) -> int:
        """Durumsuz makine — kalıcı manifold yok. Geriye dönük uyum için no-op (0)."""
        saver = getattr(self._engine, "save_manifold", None)
        if callable(saver):
            return saver()
        return 0
