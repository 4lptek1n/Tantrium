"""Natural Language Output: certified speech.

The speaker maps certified NetworkRun paths to fluent natural language.
It only says what the system can prove. Silence is not failure — it is precision.

Every word the speaker emits is backed by a certificate.
Every gap is named, not silenced.

Architecture:
  - Paradigm templates: one sentence per certified paradigm
  - Gap templates: one sentence per named gap (no evasion)
  - Narrative modes: brief (one sentence), standard (paragraph), detailed (full report)
  - Comparison: what A and B share vs. where they diverge

The speaker does not invent. It reads the NetworkRun and translates certificates
to human language. The translation is lossless — every certified fact appears.

Language topology (Pe paradigm):
  - The manifold proximity determines which words are chosen
  - Nearest concepts in the SemanticManifold inform phrasing
  - This is not metaphor — it is the same geometry as the proof system
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tantrium.core.network import CertificationRun as NetworkRun
from tantrium.core.semantic import Concept, SemanticManifold


# ─── Paradigm sentence templates ──────────────────────────────────────────

_CERTIFIED_TEMPLATES: dict[str, str] = {
    "ALEPH":  "{name} gerçek manifoldda var. Moment dizisi pozitif yarı-tanımlı.",
    "BET":    "{name}'nin tüm dönüşümleri bilgi-yitirimsiz. Hiçbir şey kaybolmuyor.",
    "GIMEL":  "{name}'nin Aşil noktası belirlendi. Optimal hamle biliniyor.",
    "DALET":  "{name}'nin spektral yapısı negatif-olmayan. Özdeğerler ≥ 0.",
    "HE":     "{name} sisteminin bir Lyapunov çekicisi var. Kararlı duruma akıyor.",
    "VAV":    "{name}'nin tensör bileşimi boyutsal olarak tutarlı.",
    "ZAYIN":  "{name}'nin yol sistemi LGV lemmasını sağlıyor. Yollar kesişmiyor.",
    "HET":    "{name}'nin gradyanı aşağı akıyor. Potansiyel monoton azalıyor.",
    "TET":    "{name}'nin çapraz oranı korunuyor. Projektif değişmezlik sağlanıyor.",
    "YOD":    "{name}'nin minimum tanımlama uzunluğu sertifikalandı. MDL ilkesi sağlandı.",
    "KAF":    "{name}'nin haritası örten. Her elementin tek bir görüntüsü var.",
    "LAMED":  "{name}'nin gözlemlenebilir yapısı yerel olarak görünür. Gizli derece yok.",
    "MEM":    "{name}'nin ayar denklik sınıfları belirlendi. Ayırt edilemezler birleştirildi.",
    "NUN":    "{name}'nin boyutsal çoğulculuğu sertifikalandı.",
    "SHIN":   "{name} için optimal eylem seçildi. Maksimum skor elde edildi.",
    "AYIN":   "{name}'deki farklı çiftler ölçümle ayrılabilir.",
    "PE":     "{name}'nin anlamsal haritası tanımlı. Anlam geometrik olarak konumlandı.",
    "TSADI":  "{name}'nin sensör-sertifika zinciri doğrulandı. Hash bütünlüğü onaylandı.",
    "KUF":    "{name}'nin topolojik indeksi 18 (Z₃ × C₆). İndeks sertifikalandı.",
    "RESH":   "{name}'nin kısmi izi iyi tanımlı. Alt-sistem bilgisi sınırlı.",
    "EMET":   "{name} tutarlı. Tüm sertifikalı iddialar geçerli. Çelişki yok.",
    "TAV":    "{name}'nin sabit noktasına ulaşıldı. Sistem yakınsadı.",
    "SU3":    "{name}'nin SU(3) simetrisi sertifikalandı. Z₃ merkezi, mertebe 3.",
}

_GAP_TEMPLATES: dict[str, str] = {
    "ALEPH":  "{name} gerçek manifoldda yok. Boşluk: {gap}.",
    "BET":    "{name}'de bilgi kaybı tespit edildi. Boşluk: {gap}.",
    "GIMEL":  "{name}'nin Aşil noktası belirlenemedi. Boşluk: {gap}.",
    "DALET":  "{name}'nin spektral negatif-olmayanlığı sertifikalanmadı. Boşluk: {gap}.",
    "HE":     "{name} için Lyapunov çekicisi bulunamadı. Boşluk: {gap}.",
    "VAV":    "{name}'nin tensör bileşimi boyutluluk testinden geçemiyor. Boşluk: {gap}.",
    "ZAYIN":  "{name}'nin LGV yol sistemi doğrulanamadı. Boşluk: {gap}.",
    "HET":    "{name}'nin gradyan akışı yukarı gidiyor. Boşluk: {gap}.",
    "TET":    "{name}'nin çapraz oran değişmezliği sertifikalanmadı. Boşluk: {gap}.",
    "YOD":    "{name}'nin minimum tanımlama uzunluğu çözümsüz. Boşluk: {gap}.",
    "KAF":    "{name}'nin haritasında çakışma var. Örtenlik sertifikalanmadı. Boşluk: {gap}.",
    "LAMED":  "{name}'nin gözlemlenebilir yapısı yerel olarak görünmüyor. Boşluk: {gap}.",
    "MEM":    "{name}'nin ayar sınıfları belirlenemedi. Boşluk: {gap}.",
    "NUN":    "{name}'nin boyutsal çoğulculuğu sertifikalanmadı. Boşluk: {gap}.",
    "SHIN":   "{name} için optimal eylem seçilemedi. Boşluk: {gap}.",
    "AYIN":   "{name}'deki farklı çiftler ölçümle ayrılamıyor. Boşluk: {gap}.",
    "PE":     "{name}'nin anlamsal haritası tanımlanamadı. Boşluk: {gap}.",
    "TSADI":  "{name}'nin sensör-sertifika bütünlüğü bozuk. Boşluk: {gap}.",
    "KUF":    "{name}'nin topolojik indeksi 18 değil. Boşluk: {gap}.",
    "RESH":   "{name}'nin kısmi izi iyi tanımlı değil. Boşluk: {gap}.",
    "EMET":   "{name}'de çelişki var. Tutarlılık sertifikalanmadı. Boşluk: {gap}.",
    "TAV":    "{name}'nin sabit noktasına iterasyon bütçesi içinde ulaşılamadı. Boşluk: {gap}.",
    "SU3":    "{name}'nin SU(3) simetrisi sertifikalanmadı. Boşluk: {gap}.",
}

_DEFAULT_CERTIFIED = "{name}, {pid} paradigmasını sağlıyor."
_DEFAULT_GAP = "{name}, {pid} paradigmasını sağlamıyor. Boşluk: {gap}."
_DEP_BLOCKED = "{name}'nin {pid} paradigması bir üst boşlukla engellendi ({dep_gap})."


# ─── A single certified statement ────────────────────────────────────────

@dataclass
class CertifiedStatement:
    """One true sentence — backed by a certificate."""
    paradigm_id: str
    status: str       # CERTIFIED | GAP | DEP_BLOCKED
    text: str
    evidence: list[str] = field(default_factory=list)


# ─── The speaker ──────────────────────────────────────────────────────────

class Speaker:
    """Maps certified NetworkRuns to natural language.

    Only emits what is certified. Names every gap precisely.
    Never invents. Never guesses. Never omits a named gap.

    detail levels:
      "line"     — one sentence: "X is certified" or "X has gap Y"
      "brief"    — key facts only (ALEPH + frontier)
      "standard" — all certified paradigms + all genuine gaps
      "full"     — standard + cascade-blocked + evidence snippets
    """

    def __init__(self, manifold: SemanticManifold | None = None) -> None:
        self.manifold = manifold or SemanticManifold()

    # ─── Core: one statement per paradigm ────────────────────────────────

    def _certified_sentence(self, pid: str, name: str) -> str:
        template = _CERTIFIED_TEMPLATES.get(pid, _DEFAULT_CERTIFIED)
        return template.format(name=name, pid=pid)

    def _gap_sentence(self, pid: str, name: str, gap: str) -> str:
        template = _GAP_TEMPLATES.get(pid, _DEFAULT_GAP)
        return template.format(name=name, pid=pid, gap=gap)

    def _dep_blocked_sentence(self, pid: str, name: str, dep_gap: str) -> str:
        return _DEP_BLOCKED.format(pid=pid, name=name, dep_gap=dep_gap)

    def _build_statements(self, run: NetworkRun) -> list[CertifiedStatement]:
        stmts = []
        for pid, node in run.nodes.items():
            name = run.obj.name
            if node.status == "CERTIFIED" and node.result:
                stmts.append(CertifiedStatement(
                    paradigm_id=pid,
                    status="CERTIFIED",
                    text=self._certified_sentence(pid, name),
                    evidence=node.result.evidence[:2],
                ))
            elif node.blocked_by_dependency and node.result:
                dep_gap = node.result.gap_name or "UNKNOWN_DEP"
                stmts.append(CertifiedStatement(
                    paradigm_id=pid,
                    status="DEP_BLOCKED",
                    text=self._dep_blocked_sentence(pid, name, dep_gap),
                ))
            elif node.status == "BLOCKED" and node.result:
                gap = node.result.gap_name or "UNNAMED_GAP"
                stmts.append(CertifiedStatement(
                    paradigm_id=pid,
                    status="GAP",
                    text=self._gap_sentence(pid, name, gap),
                    evidence=node.result.evidence[:2],
                ))
        return stmts

    # ─── Narrate ─────────────────────────────────────────────────────────

    def narrate(self, run: NetworkRun, detail: str = "standard") -> str:
        """Narrate a NetworkRun in natural language.

        detail:
          "line"     — single-line summary
          "brief"    — key facts (existence + frontier)
          "standard" — all certified + genuine gaps
          "full"     — all statements including cascade-blocked
        """
        name = run.obj.name
        certified = run.certified_count
        total = run.total
        frontier = run.knowledge_frontier()

        if detail == "line":
            if certified == total:
                return f"{name} tamamen sertifikalandı ({certified}/{total} paradigma)."
            elif certified == 0:
                return f"{name} ilk paradigmada bloke. Bu manifoldda yok."
            else:
                gaps = ", ".join(frontier) if frontier else "yok"
                return f"{name}: {certified}/{total} paradigma sertifikalandı. Açık sorular: {gaps}."

        stmts = self._build_statements(run)
        certified_stmts = [s for s in stmts if s.status == "CERTIFIED"]
        gap_stmts = [s for s in stmts if s.status == "GAP"]
        dep_stmts = [s for s in stmts if s.status == "DEP_BLOCKED"]

        lines = []

        if detail in ("brief", "standard", "full"):
            # Açılış
            if certified == total:
                lines.append(
                    f"{name} tamamen sertifikalandı. {total} matematiksel paradigmanın tamamı sağlandı."
                )
            elif certified == 0:
                lines.append(
                    f"{name} sertifikalandırılamıyor. Varlık filtresinden geçemiyor."
                )
            else:
                lines.append(
                    f"{name} kısmen sertifikalandı: {total} paradigmanın {certified}'i sağlandı."
                )

        if detail == "brief":
            # Sadece ALEPH + sınır
            aleph = next((s for s in certified_stmts if s.paradigm_id == "ALEPH"), None)
            if aleph:
                lines.append(aleph.text)
            if frontier:
                lines.append("Açık sorular: " + "; ".join(
                    self._gap_sentence(pid, name,
                        run.nodes[pid].result.gap_name if run.nodes[pid].result else "BİLİNMİYOR")
                    for pid in frontier
                ))

        elif detail in ("standard", "full"):
            if certified_stmts:
                lines.append("")
                lines.append("Bilinenler:")
                for s in certified_stmts:
                    lines.append(f"  {s.text}")

            if gap_stmts:
                lines.append("")
                lines.append("Henüz bilinmeyenler (gerçek boşluklar):")
                for s in gap_stmts:
                    lines.append(f"  {s.text}")
                lines.append(
                    "Bunlar bilginin kesin sınırları — başarısızlık değil, "
                    "neyin açık kaldığının tam ifadesi."
                )

            if detail == "full" and dep_stmts:
                lines.append("")
                lines.append("Üst boşlukla engellenenler:")
                for s in dep_stmts:
                    lines.append(f"  {s.text}")

        return "\n".join(lines)

    # ─── Explain: readable paragraph ─────────────────────────────────────

    def explain(self, run: NetworkRun) -> str:
        """Generate a readable paragraph explaining what this object is.

        Uses only certified facts. Expresses the object's certified nature
        in plain language.
        """
        name = run.obj.name
        certified = run.certified_count
        total = run.total
        frontier = run.knowledge_frontier()

        certified_pids = [pid for pid, n in run.nodes.items() if n.status == "CERTIFIED"]

        if certified == 0:
            return (
                f"'{name}' nesnesi {total} matematiksel paradigmanın tamamına karşı test edildi "
                f"ve ilkinde başarısız oldu: varlık. Moment dizisi pozitif yarı-tanımlı değil. "
                f"Bu nesne hiçbir gerçek ölçüye karşılık gelmiyor — "
                f"manifoldda var olamaz. Bu bir hata değil. Kesin bir bilgidir."
            )

        # Sertifikalı paradigmalardan okunabilir özet
        highlights = []
        if "ALEPH" in certified_pids:
            highlights.append("var (Hankel PSD sertifikalı)")
        if "BET" in certified_pids:
            highlights.append("tüm dönüşümleri bilgi koruyucu")
        if "TAV" in certified_pids:
            highlights.append("sabit noktaya yakınsar")
        if "EMET" in certified_pids:
            highlights.append("içsel olarak tutarlı")
        if "HE" in certified_pids:
            highlights.append("Lyapunov çekicisi var")
        if "KAF" in certified_pids:
            highlights.append("haritaları örten")

        highlight_str = "; ".join(highlights) if highlights else f"{certified} paradigma sertifikalı"

        parts = [
            f"'{name}' sertifikalı bir matematiksel nesnedir.",
            f"{total} paradigmanın {certified}'ini sağlıyor: {highlight_str}.",
        ]

        if frontier:
            gap_names = [
                run.nodes[pid].result.gap_name if run.nodes[pid].result else "BİLİNMİYOR"
                for pid in frontier
            ]
            parts.append(
                f"Açık sorular: {', '.join(frontier)}. "
                f"Özellikle: {'; '.join(gap_names)}. "
                f"Bunlar sistemin bu nesne hakkında bildiğinin tam sınırlarıdır."
            )
        else:
            parts.append("Bu nesne hakkında açık soru yok.")

        return " ".join(parts)

    # ─── Compare two runs ─────────────────────────────────────────────────

    def compare(self, run_a: NetworkRun, run_b: NetworkRun) -> str:
        """Compare two objects: what they share and where they diverge."""
        name_a = run_a.obj.name
        name_b = run_b.obj.name

        cert_a = {pid for pid, n in run_a.nodes.items() if n.status == "CERTIFIED"}
        cert_b = {pid for pid, n in run_b.nodes.items() if n.status == "CERTIFIED"}

        shared = cert_a & cert_b
        only_a = cert_a - cert_b
        only_b = cert_b - cert_a

        gap_a = set(run_a.knowledge_frontier())
        gap_b = set(run_b.knowledge_frontier())
        shared_gaps = gap_a & gap_b

        lines = [
            f"═══ KARŞILAŞTIRMA: {name_a} ↔ {name_b} ═══",
            f"",
            f"Ortak sertifikalı paradigmalar ({len(shared)}): "
            f"{', '.join(sorted(shared)) or 'yok'}",
        ]

        if only_a:
            lines.append(
                f"Yalnızca {name_a}'da sertifikalı ({len(only_a)}): "
                f"{', '.join(sorted(only_a))}"
            )
        if only_b:
            lines.append(
                f"Yalnızca {name_b}'da sertifikalı ({len(only_b)}): "
                f"{', '.join(sorted(only_b))}"
            )
        if shared_gaps:
            lines.append(
                f"Ortak açık sorular ({len(shared_gaps)}): "
                f"{', '.join(sorted(shared_gaps))}"
            )

        if not only_a and not only_b:
            lines.append(
                f"\n{name_a} ve {name_b} tam olarak aynı paradigmalarda sertifikalı. "
                f"Aleph-Tekin ağı düzeyinde birbirinden ayırt edilemiyor."
            )
        else:
            lines.append(
                f"\n{name_a} ve {name_b}, {len(only_a) + len(only_b)} paradigmada farklılık gösteriyor."
            )

        return "\n".join(lines)

    # ─── Manifold proximity phrasing ──────────────────────────────────────

    def locate(self, concept: Concept, n: int = 3) -> str:
        """Describe where a concept sits on the semantic manifold.

        Uses Pe (semantic mapping) and the manifold's nearest-neighbor geometry.
        Only reports certified proximity — if the manifold is empty, says so.
        """
        if not self.manifold.concepts:
            return (
                f"'{concept.name}' manifoldda konumlandırılamıyor — "
                f"manifold boş. Önce sertifikalı kavramlar öğretilmeli."
            )

        if not concept.is_real():
            return (
                f"'{concept.name}' konumlandırılamıyor — Aleph filtresinden geçemiyor. "
                f"Gerçek manifoldda yok."
            )

        neighbors = self.manifold.nearest(concept, n)
        if not neighbors:
            return f"'{concept.name}' yalıtılmış — mevcut manifoldda komşu yok."

        parts = [f"'{concept.name}' anlamsal manifoldda konumlandı."]
        parts.append(f"En yakın sertifikalı kavramlar:")
        for name, dist in neighbors:
            parts.append(f"  {name} (mesafe: {dist:.4f})")
        return "\n".join(parts)

    # ─── Synthesize TAU facts into fluent Turkish paragraph ───────────────

    _TR_VERB: dict[str, str] = {
        "IS_A":         "bir {t} türüdür",
        "USES":         "{t} kullanır",
        "ACHIEVES":     "{t} elde eder",
        "REQUIRES":     "{t} gerektirir",
        "DEFINES":      "{t} tanımlar",
        "COMPOSED":     "bileşenlerinden biri {t}",
        "COMPONENT_OF": "{t}'nin bir parçasıdır",
        "INHIBITS":     "{t}'yi inhibe eder",
        "CAUSES":       "{t}'ye neden olur",
        "ACTIVATES":    "{t}'yi aktive eder",
        "HAS_SIGNAL":   "{t} sinyaliyle algılanır",
        "HAS_COMPOUND": "{t} bileşiğini içerir",
        "HAS_IMAGE":    "{t} görüntüsüyle temsil edilir",
    }

    def synthesize(
        self,
        concept_name: str,
        facts: dict[str, list[str]],
        max_per_paradigm: int = 3,
    ) -> str:
        """TAU kenarlarından akıcı Türkçe paragraf üret.

        facts: {"IS_A": ["tool", "method"], "ACHIEVES": ["stability"], ...}
        Döner: certified Türkçe paragraf (her cümle TAU'da kenar).
        """
        if not facts:
            return f"'{concept_name}' hakkında TAU'da yeterli bilgi yok."

        sentences: list[str] = []
        for paradigm, targets in facts.items():
            tops = targets[:max_per_paradigm]
            if not tops:
                continue
            tmpl = self._TR_VERB.get(paradigm)
            if tmpl is None:
                continue
            if len(tops) == 1:
                phrase = tmpl.format(t=tops[0])
            elif len(tops) == 2:
                phrase = tmpl.format(t=f"{tops[0]} ve {tops[1]}")
            else:
                joined = ", ".join(tops[:-1]) + " ve " + tops[-1]
                phrase = tmpl.format(t=joined)
            sentences.append(f"'{concept_name}' {phrase}.")

        if not sentences:
            return f"'{concept_name}' için TAU paradigmaları tanımsız."

        return " ".join(sentences)

    # ─── Algı → dil köprüsü ──────────────────────────────────────────────────

    @staticmethod
    def _concept_family(name: str) -> str:
        """Kavram adını ailesine indir: 'tribonacci_b100' → 'tribonacci'.

        TAU komşuları çoğunlukla tek bir ailenin indeksli parçalarıdır
        (algo:tribonacci_b0, _b1, _b10…). Dile dökerken tek aile sayılır.
        """
        import re
        base = name.split(":", 1)[-1]
        base = re.sub(r"_b?\d+$", "", base)
        return base or name

    _PERCEPT_BANDS: tuple[tuple[float, str], ...] = (
        (0.10, "saf ve yoğun bir yapı — spektrumu tek bir bölgeye odaklı, saf bir ton gibi"),
        (0.30, "yapılı ve çok-bileşenli — birkaç belirgin bileşen bir arada, bir akor gibi"),
        (0.55, "karmaşık bir doku — birçok bileşen iç içe, belirgin tek yapı yok"),
        (1.01, "neredeyse düz bir spektrum — gürültü gibi, ayırt edici yapı taşımıyor"),
    )

    _PERCEPT_VERB: dict[str, str] = {
        "signal": "Bir sinyal algıladım",
        "image":  "Bir görüntü gördüm",
        "matrix": "Bir yapı okudum",
    }

    def _spectral_character(self, mu1: float) -> str:
        for hi, phrase in self._PERCEPT_BANDS:
            if mu1 < hi:
                return phrase
        return self._PERCEPT_BANDS[-1][1]

    def describe_percept(
        self,
        run: "NetworkRun",
        modality: str = "signal",
        associations: list[str] | None = None,
    ) -> str:
        """Bir algı run'ını duyusal dile dök — görmek = anlatmak.

        Spektral karakter (saf ton ↔ gürültü), grounding (N/23) ve
        neyi hatırlattığı (TAU komşuları, çeşitlendirilmiş). Uydurmaz.
        """
        mu1 = float(run.obj.moments[1]) if len(run.obj.moments) > 1 else 0.0
        verb = self._PERCEPT_VERB.get(modality, "Bir yapı okudum")
        character = self._spectral_character(mu1)

        lines = [f"{verb}: {character} (spektral entropi μ₁ = {mu1:.3f})."]

        certified, total = run.certified_count, run.total
        if certified == total:
            lines.append(
                f"Tümüyle grounded — {certified}/{total} paradigma sertifikalı; "
                f"bu algı moment uzayında gerçek bir nokta."
            )
        elif certified == 0:
            lines.append(
                f"Bu algı varlık filtresinden geçmiyor (0/{total}) — moment "
                f"dizisi pozitif yarı-tanımlı değil."
            )
        else:
            lines.append(f"Kısmen grounded — {certified}/{total} paradigma sertifikalı.")

        assoc = [self._concept_family(a) for a in (associations or []) if a]
        if assoc:
            seen = list(dict.fromkeys(assoc))[:3]
            joined = ", ".join(seen[:-1]) + (" ve " + seen[-1] if len(seen) > 1 else seen[0])
            lines.append(
                f"Bu bana {joined} kavram(lar)ını hatırlatıyor — "
                f"moment geometrileri benzer olduğu için, etiketten değil yapıdan."
            )
        else:
            lines.append(
                "Şu an bu algının manifoldda yakın bir çağrışımı yok — yalnız bir nokta."
            )

        return "\n".join(lines)

    # ─── Express a single named gap ───────────────────────────────────────

    def name_gap(self, paradigm_id: str, gap_name: str, obj_name: str) -> str:
        """Adlandırılmış boşluğu kesin dille ifade et."""
        gap_sentence = self._gap_sentence(paradigm_id, obj_name, gap_name)
        return (
            f"{gap_sentence}\n"
            f"Bu adlandırılmış bir boşluktur: sistem bunu bilmediğini kesin olarak biliyor.\n"
            f"Adlandırılmış boşluk tahminden daha değerlidir — sınırın tam bilgisidir."
        )
