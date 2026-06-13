"""İngilizce Dil Topolojisi — TAU'ya semantik omurga olarak inject.

İngilizce grameri bir manifold topolojisidir:
  - İsimler → IS_A zinciri (hiyerarşi)
  - Eylemler → ACHIEVES (ne elde ediyor)
  - Sıfatlar → DEFINES (özellik tanımlar)
  - Edatlar → REQUIRES (bağımlılık)

Bu dosya ~200 temel İngilizce semantik ilişkiyi TAU kenarı olarak içerir.
Her kenar certified: Aleph filtresi geçirilmiş kavramlar arasında.

Kullanım:
  injector = EnglishTopology(engine)
  n = injector.inject()
  print(f"{n} İngilizce kenar TAU'ya eklendi.")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


# ─── Temel İngilizce semantik ilişkiler ────────────────────────────────────
# (source, paradigm, target)
# Tüm bu kenarlar: İngilizce anlam topolojisinin omurgası

_ENGLISH_CORE: list[tuple[str, str, str]] = [
    # ── Ontoloji kökü ──
    ("entity",      "IS_A", "thing"),
    ("object",      "IS_A", "entity"),
    ("process",     "IS_A", "entity"),
    ("property",    "IS_A", "entity"),
    ("relation",    "IS_A", "entity"),
    ("event",       "IS_A", "process"),
    ("action",      "IS_A", "process"),
    ("state",       "IS_A", "entity"),
    ("structure",   "IS_A", "entity"),
    ("system",      "COMPOSED", "entity"),
    ("pattern",     "IS_A", "structure"),
    ("form",        "IS_A", "structure"),

    # ── Zihin / biliş ──
    ("cognition",       "IS_A", "process"),
    ("thinking",        "IS_A", "cognition"),
    ("learning",        "IS_A", "cognition"),
    ("understanding",   "IS_A", "cognition"),
    ("perception",      "IS_A", "cognition"),
    ("memory",          "IS_A", "cognition"),
    ("reasoning",       "IS_A", "cognition"),
    ("creativity",      "IS_A", "cognition"),
    ("imagination",     "IS_A", "cognition"),
    ("attention",       "IS_A", "cognition"),
    ("inference",       "IS_A", "reasoning"),
    ("judgment",        "IS_A", "reasoning"),
    ("decision",        "IS_A", "reasoning"),
    ("intention",       "IS_A", "state"),
    ("belief",          "IS_A", "state"),
    ("desire",          "IS_A", "state"),
    ("knowledge",       "IS_A", "state"),
    ("awareness",       "IS_A", "state"),
    ("consciousness",   "IS_A", "state"),
    ("intelligence",    "IS_A", "cognition"),
    ("wisdom",          "IS_A", "knowledge"),
    ("intuition",       "IS_A", "cognition"),

    # ── Dil ──
    ("language",        "IS_A", "system"),
    ("word",            "IS_A", "symbol"),
    ("sentence",        "COMPOSED", "word"),
    ("grammar",         "DEFINES", "language"),
    ("meaning",         "IS_A", "relation"),
    ("symbol",          "IS_A", "entity"),
    ("sign",            "IS_A", "symbol"),
    ("communication",   "USES", "language"),
    ("text",            "COMPOSED", "sentence"),
    ("discourse",       "COMPOSED", "text"),
    ("narrative",       "IS_A", "discourse"),
    ("argument",        "IS_A", "discourse"),
    ("metaphor",        "IS_A", "language"),
    ("abstraction",     "IS_A", "process"),
    ("representation",  "IS_A", "entity"),
    ("context",         "IS_A", "entity"),
    ("meaning",         "REQUIRES", "context"),

    # ── Bilgi / epistemoloji ──
    ("truth",           "IS_A", "property"),
    ("evidence",        "REQUIRES", "knowledge"),
    ("proof",           "IS_A", "evidence"),
    ("theorem",         "IS_A", "proof"),
    ("axiom",           "REQUIRES", "mathematics"),
    ("hypothesis",      "IS_A", "belief"),
    ("theory",          "IS_A", "system"),
    ("theory",          "REQUIRES", "evidence"),
    ("observation",     "IS_A", "process"),
    ("experiment",      "USES", "observation"),
    ("prediction",      "IS_A", "process"),
    ("verification",    "ACHIEVES", "certainty"),
    ("certainty",       "IS_A", "state"),
    ("uncertainty",     "IS_A", "state"),
    ("inference",       "USES", "reasoning"),
    ("analogy",         "IS_A", "relation"),

    # ── Matematik ──
    ("mathematics",         "IS_A", "system"),
    ("number",              "IS_A", "mathematical_object"),
    ("function",            "IS_A", "mathematical_object"),
    ("set",                 "IS_A", "mathematical_object"),
    ("mathematical_object", "IS_A", "entity"),
    ("proof",               "ACHIEVES", "certainty"),
    ("computation",         "IS_A", "process"),
    ("algorithm",           "IS_A", "process"),
    ("optimization",        "IS_A", "process"),
    ("geometry",            "IS_A", "mathematics"),
    ("algebra",             "IS_A", "mathematics"),
    ("calculus",            "IS_A", "mathematics"),
    ("probability",         "IS_A", "mathematics"),
    ("statistics",          "USES", "probability"),
    ("logic",               "IS_A", "mathematics"),
    ("symmetry",            "IS_A", "property"),
    ("transformation",      "IS_A", "process"),
    ("invariant",           "IS_A", "property"),
    ("limit",               "IS_A", "mathematical_object"),
    ("continuity",          "IS_A", "property"),
    ("convergence",         "ACHIEVES", "limit"),

    # ── Fizik ──
    ("matter",      "IS_A", "entity"),
    ("energy",      "IS_A", "entity"),
    ("space",       "IS_A", "entity"),
    ("time",        "IS_A", "entity"),
    ("motion",      "IS_A", "process"),
    ("force",       "ACHIEVES", "motion"),
    ("field",       "IS_A", "entity"),
    ("wave",        "IS_A", "process"),
    ("particle",    "IS_A", "entity"),
    ("entropy",     "IS_A", "property"),
    ("equilibrium", "IS_A", "state"),
    ("chaos",       "IS_A", "state"),
    ("order",       "IS_A", "property"),
    ("emergence",   "IS_A", "process"),
    ("complexity",  "IS_A", "property"),

    # ── Biyoloji / yaşam ──
    ("life",            "IS_A", "process"),
    ("organism",        "IS_A", "entity"),
    ("cell",            "IS_A", "entity"),
    ("evolution",       "IS_A", "process"),
    ("adaptation",      "IS_A", "process"),
    ("growth",          "IS_A", "process"),
    ("reproduction",    "IS_A", "process"),
    ("metabolism",      "IS_A", "process"),
    ("genetics",        "IS_A", "system"),
    ("brain",           "IS_A", "entity"),
    ("nervous_system",  "IS_A", "system"),
    ("perception",      "USES", "nervous_system"),

    # ── Toplum / insan ──
    ("person",          "IS_A", "entity"),
    ("society",         "IS_A", "system"),
    ("culture",         "IS_A", "system"),
    ("value",           "IS_A", "property"),
    ("goal",            "IS_A", "state"),
    ("cooperation",     "USES", "communication"),
    ("competition",     "IS_A", "process"),
    ("power",           "IS_A", "relation"),
    ("institution",     "IS_A", "system"),
    ("norm",            "DEFINES", "society"),
    ("ethics",          "DEFINES", "value"),
    ("justice",         "IS_A", "property"),
    ("freedom",         "IS_A", "state"),
    ("responsibility",  "IS_A", "relation"),

    # ── Sanat / yaratıcılık ──
    ("art",             "IS_A", "process"),
    ("beauty",          "IS_A", "property"),
    ("aesthetics",      "DEFINES", "beauty"),
    ("expression",      "IS_A", "communication"),
    ("creation",        "IS_A", "process"),
    ("design",          "IS_A", "process"),
    ("music",           "IS_A", "art"),
    ("story",           "IS_A", "narrative"),
    ("image",           "IS_A", "representation"),
    ("emotion",         "IS_A", "state"),
    ("feeling",         "IS_A", "state"),
    ("experience",      "IS_A", "process"),

    # ── Hesaplama / yapay zeka ──
    ("data",            "IS_A", "entity"),
    ("information",     "IS_A", "entity"),
    ("model",           "IS_A", "representation"),
    ("neural_network",  "IS_A", "model"),
    ("training",        "IS_A", "learning"),
    ("classification",  "IS_A", "process"),
    ("prediction",      "USES", "model"),
    ("feature",         "IS_A", "property"),
    ("gradient",        "IS_A", "mathematical_object"),
    ("optimization",    "USES", "gradient"),
    ("network",         "IS_A", "system"),
    ("graph",           "IS_A", "mathematical_object"),
    ("search",          "IS_A", "process"),
    ("planning",        "IS_A", "process"),
    ("decision",        "USES", "planning"),

    # ── Nedensellik / ilişki ──
    ("cause",       "IS_A", "relation"),
    ("effect",      "IS_A", "entity"),
    ("cause",       "ACHIEVES", "effect"),
    ("correlation", "IS_A", "relation"),
    ("dependency",  "IS_A", "relation"),
    ("interaction", "IS_A", "process"),
    ("feedback",    "IS_A", "process"),
    ("constraint",  "IS_A", "relation"),
    ("boundary",    "IS_A", "entity"),
    ("interface",   "IS_A", "relation"),
]

# ─── İngilizce dil metni (bootstrap için) ──────────────────────────────────
# Temel kavramları bağlamda öğrenmek için kısa certified metinler

_ENGLISH_BOOTSTRAP_TEXT = """
Knowledge is a state of justified belief. Evidence supports knowledge. Proof achieves certainty.
Reasoning is a cognitive process. Inference uses reasoning. Logic defines valid inference.
Language is a symbolic system. Grammar defines the structure of language. Meaning requires context.
Mathematics is a formal system. Theorems are proven results. Algorithms are computational processes.
Intelligence is a cognitive capacity. Learning achieves knowledge. Perception uses attention.
Creativity is a cognitive process. Imagination enables creativity. Art expresses emotion.
Systems are composed of entities. Emergence is a process within complex systems. Order and chaos are opposite states.
Energy and matter are fundamental entities. Force achieves motion. Space and time are physical entities.
Evolution is a biological process. Adaptation enables survival. Growth is a natural process.
Society is a human system. Culture defines values. Communication uses language.
Beauty is an aesthetic property. Design is a creative process. Music is an art form.
Data is an entity processed by algorithms. Models are representations learned from data.
Truth is a property of valid knowledge. Certainty is achieved through verification.
Thinking is a cognitive process. Decision uses planning. Goal is a desired state.
"""


@dataclass
class InjectionResult:
    """TAU injection sonucu."""
    concepts_added: int
    edges_added: int
    bootstrap_concepts: int
    bootstrap_relations: int

    def summary(self) -> str:
        return (
            f"  İngilizce topoloji enjekte edildi:\n"
            f"  Çekirdek: {self.concepts_added} kavram, {self.edges_added} kenar\n"
            f"  Bootstrap: +{self.bootstrap_concepts} kavram, +{self.bootstrap_relations} ilişki"
        )


class EnglishTopology:
    """İngilizce semantik topolojiyi TAU graph'a inject eder.

    İngilizce grameri = semantik manifold topolojisi:
      - İsim hiyerarşisi → IS_A zinciri
      - Eylem → ACHIEVES
      - Özellik → DEFINES
      - Bağımlılık → REQUIRES
      - Bileşim → COMPOSED

    inject() çalıştırılınca:
      1. ~200 çekirdek İngilizce ilişki TAU'ya kenar olarak eklenir
      2. LanguageBootstrap ile İngilizce metin işlenir → ek kenarlar
      3. TauReasoner ile transitif kapatma → yeni çıkarımlar
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    def inject(self, run_bootstrap: bool = True, run_reasoner: bool = False) -> InjectionResult:
        """Tüm İngilizce semantik ilişkileri TAU'ya ekle."""
        from tantrium.graph.relations import certify_and_add_edge
        from tantrium.core.semantic import Concept
        from tantrium.core.encoder import encode

        manifold = self.engine.manifold
        tau = self.engine.tau

        concepts_added = 0
        edges_added = 0

        # 1. Çekirdek ilişkileri inject et
        for src, paradigm, tgt in _ENGLISH_CORE:
            # Kavramları manifolda ekle (yoksa)
            for name in (src, tgt):
                if name not in manifold.concepts:
                    raw = encode(name)
                    c = Concept(
                        name=name,
                        moments=list(raw.moments),
                        domain="english",
                        source="lang_topology",
                    )
                    if c.is_real():
                        manifold.add_unchecked(c)
                        tau.add_node(c)
                        concepts_added += 1

            # Kenarı ekle (certify_and_add_edge ile)
            added = certify_and_add_edge(self.engine, src, tgt, paradigm)
            if added:
                edges_added += 1

        tau._dirty = True

        # 2. Bootstrap: İngilizce metin üzerinden öğren
        bootstrap_concepts = 0
        bootstrap_relations = 0

        if run_bootstrap:
            from tantrium.language.bootstrap import LanguageBootstrap
            bootstrapper = LanguageBootstrap(self.engine, window=4, min_freq=1)
            result = bootstrapper.from_text(_ENGLISH_BOOTSTRAP_TEXT)
            bootstrap_concepts = result.new_concepts
            bootstrap_relations = result.relations_added

        # 3. Reasoner: transitif kapatma (yeni çıkarımlar)
        if run_reasoner:
            from tantrium.reasoning.reasoner import GraphReasoner
            reasoner = GraphReasoner(self.engine)
            # Sadece yeni eklenen İngilizce kavramlar üzerinde çalıştır
            eng_concepts = [src for src, _, _ in _ENGLISH_CORE[:50]]
            new_edges = 0
            for name in set(eng_concepts):
                r = reasoner.query(name, depth=2)
                new_edges += r.new_edges
            edges_added += new_edges

        # Kalıcı kaydet
        self.engine.auto_persist()

        return InjectionResult(
            concepts_added=concepts_added,
            edges_added=edges_added,
            bootstrap_concepts=bootstrap_concepts,
            bootstrap_relations=bootstrap_relations,
        )
