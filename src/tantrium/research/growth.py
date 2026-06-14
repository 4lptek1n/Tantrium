"""Büyüme Motoru — GrowthEngine.

Sınırsız, kendi kendine büyüyen çekirdek akışı. Bu, sistemin son mimari
parçası: insan tetiği OLMADAN sürekli çalışan döngü.

  ağ kaynağı (resumable) → evren kapısı (Aleph+truth+grounding) →
  çekirdek nabzı (veri + yerel genesis aynı anda) →
  periyodik konsolidasyon (close + reflect + persist) → tekrar

Klasik run() fazlı ve sonludur. GrowthEngine süreklidir:
  - Kaynaklar döner: PubChem (CID ilerler) + OEIS (anahtar kelime rotasyonu)
  - Her veri tek nabızda girer ve büyür (parça parça değil)
  - Durum diske yazılır (.tantrium/growth_state.json) → kap yeniden başlasa
    bile kaldığı CID'den devam eder (resumable)
  - time_limit_s=None → SINIRSIZ (durana/kapatılana dek)
  - Hata toleranslı: bir kaynak düşse akış durmaz

ÖNEMLİ: Bu motor "zeka" değildir — zeka, neyi besleyeceğine karar veren
sensin. Motor sadık bir kalp: girdiyi yasal yapıya çevirir, çelişeni eler,
gerçeği manifolda örer, kendini hatırlar.
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

_UA = {"User-Agent": "Tantrium-AGI/1.0 (research; mailto:research@tantrium.ai)"}
_RATE_LIMIT_S = 0.34
_STATE_DIR = pathlib.Path(".tantrium")
_STATE_FILE = _STATE_DIR / "growth_state.json"

# Corrigibility eşikleri (yanlış-tespit)
_DEGEN_SPREAD = 0.02     # moment yayılımı (max-min) bunun altında = dejenere encoding
                         # (protein/glucose çöküşü μ_k≡1 → yayılım 0; GIMEL göremez)
_COLLISION_EPS = 0.001   # iki FARKLI kavram bu L1 mesafenin altında = çakışma şüphesi
                         # (sıkı: 48k doymuş manifoldda saturasyon yoğunluğunu DEĞİL,
                         #  neredeyse-tam çakışmayı = gerçek encoder ayırma hatasını yakala)
_VERIFY_MAX = 60         # döngü başına denetlenen kavram (maliyet sınırı)
_VERIFY_COLLISION_MAX = 20  # çakışma taraması O(N) — daha sıkı sınır

# OEIS anahtar kelime rotasyonu — matematik gövdesini geniş tarar
_OEIS_KEYWORDS = [
    "prime", "fibonacci", "catalan", "partition", "bernoulli", "euler",
    "triangular", "perfect number", "mersenne", "factorial", "lucas",
    "stirling", "harmonic", "totient", "divisor", "binomial",
]


@dataclass
class GrowthReport:
    """Bir büyüme oturumunun toplam bilançosu."""
    cycles: int = 0
    processed: int = 0
    core: int = 0
    frontier: int = 0
    rejected: int = 0
    born: int = 0
    concepts_start: int = 0
    concepts_end: int = 0
    edges_start: int = 0
    edges_end: int = 0
    elapsed_s: float = 0.0
    stopped_reason: str = ""
    # Anlam kanalı entegrasyonu (TopologyEncoder) bilançosu
    meaning_enriched: int = 0  # anlam imzası hesaplanan (semantik-köklü) kavram
    bridges_found: int = 0     # keşfedilen çapraz-boyutlu kuantum köprü
    # Corrigibility (yanlıştan-dön) bilançosu
    suspect_flagged: int = 0   # dejenere/çakışma şüphesiyle işaretlenen (düzeltilemeyen)
    corrected: int = 0         # dejenere encoding adaptif re-encode ile düzeltilen
    windows_deduped: int = 0   # aile-içi exact-moment pencere-kopyası silinen

    def summary(self) -> str:
        dc = self.concepts_end - self.concepts_start
        de = self.edges_end - self.edges_start
        return (
            f"═══ BÜYÜME RAPORU ({self.elapsed_s:.1f}s, {self.cycles} döngü) ═══\n"
            f"İşlenen: {self.processed} | çekirdek: {self.core} | "
            f"sınır: {self.frontier} | reddedilen: {self.rejected} | doğan: {self.born}\n"
            f"Kavram: {self.concepts_start:,} → {self.concepts_end:,} (+{dc})\n"
            f"TAU kenar: {self.edges_start:,} → {self.edges_end:,} (+{de})\n"
            f"Anlam zenginleştirme: {self.meaning_enriched} kavram | "
            f"kuantum köprü: {self.bridges_found}\n"
            f"Corrigibility: {self.corrected} düzeltildi | "
            f"{self.suspect_flagged} şüpheli | {self.windows_deduped} pencere-kopya silindi\n"
            f"Durma sebebi: {self.stopped_reason}"
        )


def _http_json(url: str, timeout: int = 12) -> Any:
    """Kanonik `net.http_get_json`'a delege (#9). Toleranslı decode (replace)."""
    from tantrium.research.net import http_get_json
    return http_get_json(url, timeout=timeout, user_agent=_UA["User-Agent"], errors="replace")


def _http_json_link(url: str, timeout: int = 15) -> tuple[Any, str | None]:
    """JSON + Link header 'next' URL (UniProt cursor). `net.http_get_json_link`'e delege."""
    from tantrium.research.net import http_get_json_link
    return http_get_json_link(url, timeout=timeout, user_agent=_UA["User-Agent"], errors="replace")


class GrowthEngine:
    """Sınırsız kendi kendine büyüme döngüsü.

    stream(): ağdan resumable veri çek → çekirdek nabzı → konsolide → tekrar.
    """

    def __init__(self, engine: "CertificationEngine", observer: Any = None) -> None:
        self.engine = engine
        if observer is None:
            from tantrium.research.autonomous import AutonomousObserver
            observer = AutonomousObserver(engine)
        self.observer = observer
        self.state = self._load_state()
        self._gap_cache: list[str] = []  # _fetch_web için önceden hesaplanmış boşluklar
        self._gap_cache_cycle: int = -1  # cache'in güncellendiği döngü
        # Anlam kanalı entegrasyonu (TopologyEncoder) — konsolidasyonda lazy kurulur.
        self._topo_encoder: Any = None
        self._meaning_seen: set[str] = set()  # anlam-zenginleştirmesi yapılmış kavramlar
        self._verify_seen: set[str] = set()   # corrigibility-denetimi yapılmış kavramlar
        self._family_reps: dict[tuple, str] = {}  # (aile, moment) → temsilci (pencere-dedup)
        self._fam_seen: set[str] = set()      # aile-dedup taranan pencere adları

    # ─── Resumable durum ─────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        try:
            if _STATE_FILE.exists():
                return json.loads(_STATE_FILE.read_text())
        except Exception:
            pass
        return {"pubchem_cid": 1, "oeis_idx": 0, "total_processed": 0}

    def _save_state(self) -> None:
        try:
            _STATE_DIR.mkdir(parents=True, exist_ok=True)
            _STATE_FILE.write_text(json.dumps(self.state))
        except Exception:
            pass

    # ─── Ağ kaynakları (hata toleranslı, resumable) ──────────────────────────

    def _fetch_pubchem(self, count: int = 12) -> list[str]:
        """İlerleyen CID'den gerçek SMILES. Durum kalıcı → resumable."""
        start = self.state.get("pubchem_cid", 1)
        cids = ",".join(str(c) for c in range(start, start + count))
        url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cids}"
               f"/property/SMILES/JSON")
        out: list[str] = []
        try:
            data = _http_json(url)
            props = (data or {}).get("PropertyTable") or {}
            for p in props.get("Properties") or []:
                smi = p.get("SMILES", "") or p.get("CanonicalSMILES", "")
                if smi:
                    out.append(smi)
        except Exception:
            pass
        self.state["pubchem_cid"] = start + count  # düşse bile ilerle (resumable)
        time.sleep(_RATE_LIMIT_S)
        return out

    def _fetch_oeis(self, n: int = 4) -> list[list[int]]:
        """Dönen anahtar kelimeden gerçek tamsayı dizileri."""
        idx = self.state.get("oeis_idx", 0)
        kw = _OEIS_KEYWORDS[idx % len(_OEIS_KEYWORDS)]
        self.state["oeis_idx"] = idx + 1
        url = f"https://oeis.org/search?q={urllib.parse.quote(kw)}&fmt=json&start=0"
        out: list[list[int]] = []
        try:
            data = _http_json(url)
            entries = data if isinstance(data, list) else ((data or {}).get("results") or [])
            for e in (entries or [])[:n]:
                raw = (e or {}).get("data", "")
                vals = [int(x) for x in str(raw).split(",")[:24]
                        if x.strip().lstrip("-").isdigit()]
                if len(vals) >= 6:
                    out.append(vals)
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return out

    def _fetch_uniprot(self, size: int = 8, organism: int = 9606) -> list[str]:
        """UniProt protein adları + gen isimleri. Diziler yerine kısa isimler → hızlı encode."""
        cursor = self.state.get("uniprot_cursor")
        if not cursor:
            q = urllib.parse.quote(f"reviewed:true AND organism_id:{organism}")
            cursor = (f"https://rest.uniprot.org/uniprotkb/search?query={q}"
                      f"&format=json&size={min(size, 100)}"
                      f"&fields=accession,gene_names,protein_name,cc_function")
        out: list[str] = []
        try:
            data, next_url = _http_json_link(cursor)
            for entry in (data or {}).get("results", []):
                # Gen isimleri (kısa: TP53, BRCA1, EGFR...)
                genes = (entry or {}).get("genes") or []
                for g in genes[:2]:
                    gname = (g.get("geneName") or {}).get("value", "")
                    if gname:
                        out.append(gname)
                # Protein adı (kısa)
                pname_obj = ((entry or {}).get("proteinDescription") or {})
                rec = (pname_obj.get("recommendedName") or {})
                pname = (rec.get("fullName") or {}).get("value", "")
                if pname and len(pname) < 80:
                    out.append(pname)
                # Fonksiyon metni → kausal kenar öğrenimi
                comments = (entry or {}).get("comments") or []
                for c in comments[:1]:
                    if c.get("commentType") == "FUNCTION":
                        texts = c.get("texts") or []
                        for t in texts[:1]:
                            val = t.get("value", "")
                            if val and len(val) > 50:
                                try:
                                    self.observer.observe(val[:600])
                                except Exception:
                                    pass
            self.state["uniprot_cursor"] = next_url
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return [x for x in out if x]

    def _refresh_gap_cache(self) -> None:
        """Manifold boşluklarını döngü başında bir kez hesapla (paralel fetch'te bottleneck önlenir)."""
        try:
            from tantrium.reasoning.necessity import NecessityEngine
            ne = NecessityEngine(self.engine)
            gaps = ne.find_manifold_gaps(domain="math_kernel", top_k=12)
            if gaps:
                self._gap_cache = [g.concept_a for g in gaps]
                return
        except Exception:
            pass
        # Fallback: kausal sınır kavramları
        try:
            tau = self.engine.tau
            causal = {"CAUSES", "INHIBITS", "ACTIVATES"}
            frontier = [
                s for s, edges in tau.edges.items()
                if any(e.paradigm in causal for e in edges) and len(edges) < 5
            ]
            self._gap_cache = frontier[:20] if frontier else ["mathematics", "biochemistry", "topology"]
        except Exception:
            self._gap_cache = ["mathematics", "biochemistry", "topology"]

    def _fetch_web(self, n: int = 5) -> list[str]:
        """Manifold boşluklarına göre Wikipedia'dan kavramlar çek.

        Boşluklar _refresh_gap_cache() ile döngü başında hesaplanır;
        _fetch_web() sadece HTTP yapar (NecessityEngine çağırmaz → hız).
        """
        web_idx = self.state.get("web_gap_idx", 0)
        cache = self._gap_cache or ["mathematics", "biochemistry", "topology"]
        idx = web_idx % max(len(cache), 1)
        gaps_labels = cache[idx:idx + 3]
        self.state["web_gap_idx"] = web_idx + 1

        concepts_list: list[str] = []
        _SKIP = ("All ", "Articles ", "Wikipedia ", "Pages ", "CS1 ",
                 "Webarchive", "Use ", "Short description")

        def _fetch_one_wiki(query: str) -> list[str]:
            local: list[str] = []
            try:
                q = urllib.parse.quote(str(query)[:80])
                url = (f"https://en.wikipedia.org/w/api.php"
                       f"?action=opensearch&search={q}&limit=3&format=json")
                data = _http_json(url)
                titles = (data[1] if isinstance(data, list) and len(data) > 1 else [])
                for title in titles[:2]:
                    t = urllib.parse.quote(str(title)[:120])
                    url2 = (f"https://en.wikipedia.org/w/api.php"
                            f"?action=query&prop=categories|links|extracts"
                            f"&titles={t}&format=json&exintro=1&exsentences=3"
                            f"&explaintext=1&cllimit=8&pllimit=12&redirects=1")
                    page_data = _http_json(url2)
                    pages = ((page_data or {}).get("query") or {}).get("pages") or {}
                    for pid, page in pages.items():
                        if pid == "-1":
                            continue
                        local.append(str(page.get("title", "")))
                        for cat in (page.get("categories") or [])[:8]:
                            cname = cat.get("title", "").replace("Category:", "").strip()
                            if cname and len(cname) < 60 and not any(cname.startswith(s) for s in _SKIP):
                                local.append(cname)
                        for link in (page.get("links") or [])[:6]:
                            lname = link.get("title", "").strip()
                            if lname and len(lname) < 60 and not lname.startswith(("Wikipedia:", "Help:", "File:")):
                                local.append(lname)
                        extract = str(page.get("extract") or "").strip()
                        if extract and len(extract) > 50:
                            try:
                                self.observer.observe(extract)
                            except Exception:
                                pass
            except Exception:
                pass
            return local

        # 3 Wikipedia sorgusu paralel
        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = [pool.submit(_fetch_one_wiki, q) for q in gaps_labels[:3]]
            for fut in as_completed(futs):
                try:
                    concepts_list += fut.result()
                except Exception:
                    pass

        seen: set[str] = set()
        out: list[str] = []
        for c in concepts_list:
            c = c.strip()
            if c and c not in seen and len(c) > 3:
                seen.add(c)
                out.append(c)
            if len(out) >= n:
                break
        return out

    def _fetch_kegg(self, n: int = 4) -> list[str]:
        """KEGG REST API: sinyal yolağı genleri + bileşik isimleri."""
        _KEGG_PATHWAYS = [
            "hsa04010",  # MAPK signaling pathway
            "hsa04151",  # PI3K-Akt signaling pathway
            "hsa04210",  # Apoptosis
            "hsa04110",  # Cell cycle
            "hsa04012",  # ErbB signaling pathway
            "hsa04350",  # TGF-beta signaling
            "hsa04630",  # JAK-STAT signaling
            "hsa04310",  # Wnt signaling pathway
        ]
        kegg_idx = self.state.get("kegg_idx", 0)
        topic = _KEGG_PATHWAYS[kegg_idx % len(_KEGG_PATHWAYS)]
        self.state["kegg_idx"] = kegg_idx + 1
        out: list[str] = []
        try:
            url = f"https://rest.kegg.jp/get/{topic}"
            req = urllib.request.Request(url, headers=_UA)
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            for line in text.split("\n"):
                stripped = line.strip()
                if not stripped:
                    continue
                # NAME satırı: yolak ismi
                if line.startswith("NAME"):
                    name_val = stripped.split(None, 1)[1] if " " in stripped else ""
                    if name_val:
                        out.append(name_val[:80])
                # GENE satırları: gen isimleri
                elif line.startswith("GENE") or (line.startswith(" ") and out):
                    # "  7157      TP53; tumor protein p53" biçimi
                    parts = stripped.split(";")
                    for part in parts:
                        tokens = part.strip().split()
                        for tok in tokens:
                            tok = tok.strip(".,;()")
                            if 2 < len(tok) < 20 and tok.replace("-", "").isalpha():
                                out.append(tok)
                                break
            # Öğrenme: NAME + kısa açıklama var mı?
            desc = "\n".join(l for l in text.split("\n")
                             if l.startswith("DESCRIPTION") or l.startswith("NAME"))
            if desc:
                try:
                    self.observer.observe(desc[:400])
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return [x for x in dict.fromkeys(out) if x][:n]

    def _fetch_chembl(self, n: int = 5) -> list[str]:
        """ChEMBL REST API: biyoaktif küçük molekül SMILES."""
        chembl_offset = self.state.get("chembl_offset", 0)
        url = (f"https://www.ebi.ac.uk/chembl/api/data/molecule"
               f"?format=json&limit={n}&offset={chembl_offset}"
               f"&molecule_properties__mw_freebase__lte=500"
               f"&molecule_type=Small+molecule")
        out: list[str] = []
        try:
            data = _http_json(url)
            for mol in (data or {}).get("molecules", []):
                smiles = ((mol or {}).get("molecule_structures") or {}).get(
                    "canonical_smiles", ""
                )
                if smiles and len(smiles) < 200:
                    out.append(smiles)
            self.state["chembl_offset"] = chembl_offset + n
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return out

    def _fetch_pubmed(self, n: int = 3) -> list[str]:
        """PubMed E-utilities: makale başlıkları + kausal kenar öğrenimi.

        ai.learn() ile özetten CAUSES/INHIBITS/ACTIVATES kenarları çıkarılır.
        Kavram listesi olarak makale başlıkları döner.
        """
        _PUBMED_QUERIES = [
            "EGFR+inhibitor+cancer",
            "kinase+signaling+pathway",
            "protein+phosphorylation+mechanism",
            "drug+target+interaction",
            "tumor+suppressor+gene",
            "mTOR+inhibitor+rapamycin",
            "BRCA1+DNA+repair",
            "p53+apoptosis+cancer",
        ]
        pm_idx = self.state.get("pubmed_idx", 0)
        query = _PUBMED_QUERIES[pm_idx % len(_PUBMED_QUERIES)]
        self.state["pubmed_idx"] = pm_idx + 1
        out: list[str] = []
        try:
            search_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                f"?db=pubmed&term={query}&retmax={n}&retmode=json"
            )
            search_data = _http_json(search_url)
            pmids = ((search_data or {}).get("esearchresult") or {}).get("idlist", [])
            if pmids:
                ids_str = ",".join(pmids[:n])
                fetch_url = (
                    f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    f"?db=pubmed&id={ids_str}&rettype=abstract&retmode=text"
                )
                req = urllib.request.Request(fetch_url, headers=_UA)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    abstract_text = resp.read().decode("utf-8", errors="replace")
                if abstract_text and len(abstract_text) > 100:
                    # Kausal kenar öğrenimi
                    try:
                        self.observer.observe(abstract_text[:2000])
                    except Exception:
                        pass
                    # Başlık satırlarını kavram olarak döndür
                    for line in abstract_text.split("\n"):
                        line = line.strip()
                        if 10 < len(line) < 120 and not line.startswith("PMID"):
                            out.append(line)
                            if len(out) >= n:
                                break
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return out

    def _fetch_wikidata(self, n: int = 6) -> list[str]:
        """Wikidata SPARQL: biyomedikal typed triples → TAU'ya IS_A/PART_OF/TREATS kenarları.

        SPARQL sorgusu ilaç→hedef→hastalık üçlülerini çeker;
        kavram adları manifolda, ilişkiler TAU'ya CAUSES/INHIBITS olarak eklenir.
        """
        _WIKIDATA_SPARQL = (
            "https://query.wikidata.org/sparql?format=json&query="
        )
        # İlaçlar ve hedefleri: ilaç -tedavi eder→ hastalık
        _QUERIES = [
            # drug → treats → disease
            """SELECT ?drugLabel ?diseaseLabel WHERE {
  ?drug wdt:P31 wd:Q12140 .
  ?drug wdt:P2175 ?disease .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
} LIMIT 10""",
            # gene → associated_with → disease
            """SELECT ?geneLabel ?diseaseLabel WHERE {
  ?gene wdt:P31 wd:Q7187 .
  ?gene wdt:P2293 ?disease .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
} LIMIT 10""",
        ]
        wikidata_idx = self.state.get("wikidata_idx", 0)
        query = _QUERIES[wikidata_idx % len(_QUERIES)]
        self.state["wikidata_idx"] = wikidata_idx + 1
        out: list[str] = []
        try:
            url = _WIKIDATA_SPARQL + urllib.parse.quote(query)
            req = urllib.request.Request(
                url, headers={**_UA, "Accept": "application/sparql-results+json"}
            )
            import json as _json
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = _json.loads(resp.read().decode())
            bindings = (data or {}).get("results", {}).get("bindings", [])
            for b in bindings[:n]:
                vals = [v.get("value", "") for v in b.values()]
                for val in vals:
                    if val and len(val) < 60:
                        out.append(val)
                # Kausal kenar öğrenimi: "X treats Y" → ai.learn
                labels = [b.get(k, {}).get("value", "") for k in b.keys()]
                if len(labels) >= 2 and labels[0] and labels[1]:
                    try:
                        # Relation type from query index
                        rel_word = "treats" if "disease" in query else "associated with"
                        self.observer.observe(f"{labels[0]} {rel_word} {labels[1]}.")
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S * 2)  # Wikidata rate limit daha kısıtlı
        return [x for x in dict.fromkeys(out) if x][:n]

    # ─── Yapılandırılmış bilgi enjeksiyonu (ConceptNet + KEGG KGML) ─────────────

    def _ensure_in_manifold(self, name: str) -> bool:
        """Kavramı manifolda ekle (yoksa). NLP yok, hızlı."""
        if not name or len(name) > 80:
            return False
        if name in self.engine.manifold.concepts:
            return True
        try:
            from tantrium.core.semantic import Concept
            codex_obj = self.engine.encoder.encode(name)
            concept = Concept(
                name=name,
                moments=list(codex_obj.moments),
                domain="general",
                source="structured",
            )
            self.engine.manifold.add_unchecked(concept)
            self.engine.tau.add_node(concept)
            return True
        except Exception:
            return False

    def _inject_direct_edge(self, subj: str, paradigm: str, obj: str) -> bool:
        """Yapılandırılmış veri → doğrudan TAU kenarı (NLP yok, sertifikasyon yok).

        Her iki kavram manifolda yoksa ekle, sonra KnowledgeEdge ekle.
        ConceptNet/KEGG gibi küratörlü kaynaklardan gelen kenarlar için.
        """
        if not self._ensure_in_manifold(subj) or not self._ensure_in_manifold(obj):
            return False
        from tantrium.graph.relations import certify_and_add_edge
        return certify_and_add_edge(self.engine, subj, obj, paradigm)

    def _fetch_conceptnet(self, n: int = 20) -> list[str]:
        """ConceptNet API: 600k+ kavram, yapılandırılmış triples → doğrudan TAU.

        İngilizce ilişkiler paradigma haritası:
          Causes→CAUSES, IsA→IS_A, PartOf→COMPONENT_OF, MadeOf→COMPOSED ...
        NLP yok — ConceptNet zaten düzenlenmiş (kurallı) bilgi.
        """
        _CN_REL_MAP = {
            "Causes": "CAUSES",
            "IsA": "IS_A",
            "PartOf": "COMPONENT_OF",
            "UsedFor": "ACHIEVES",
            "CapableOf": "ACHIEVES",
            "HasA": "REQUIRES",
            "DefinedAs": "DEFINES",
            "MadeOf": "COMPOSED",
            "Entails": "CAUSES",
            "HasPrerequisite": "REQUIRES",
            "CausesDesire": "CAUSES",
            "ReceivesAction": "USES",
            "HasProperty": "DEFINES",
        }
        cn_idx = self.state.get("cn_idx", 0)
        # Seed kavramlar: manifold boşluklarından al (varsa), yoksa genel liste
        seeds = (self._gap_cache or [
            "cell", "protein", "enzyme", "inhibitor", "disease", "signal",
            "molecule", "gene", "reaction", "pathway", "cancer", "brain",
            "neuron", "antibody", "metabolism", "dna", "rna", "virus",
            "immune", "receptor",
        ])
        concept = seeds[cn_idx % len(seeds)].lower().replace(" ", "_")
        self.state["cn_idx"] = cn_idx + 1
        out: list[str] = []
        try:
            url = (f"https://api.conceptnet.io/c/en/{urllib.parse.quote(concept)}"
                   f"?limit=100")
            data = _http_json(url, timeout=15)
            edges = (data or {}).get("edges", [])
            for edge in edges:
                start = edge.get("start") or {}
                end = edge.get("end") or {}
                if start.get("language") != "en" or end.get("language") != "en":
                    continue
                rel_label = (edge.get("rel") or {}).get("label", "")
                paradigm = _CN_REL_MAP.get(rel_label)
                if not paradigm:
                    continue
                subj_raw = start.get("label", "")
                obj_raw = end.get("label", "")
                if not subj_raw or not obj_raw or subj_raw == obj_raw:
                    continue
                subj = subj_raw.lower().replace(" ", "_")
                obj = obj_raw.lower().replace(" ", "_")
                if len(subj) > 60 or len(obj) > 60:
                    continue
                if self._inject_direct_edge(subj, paradigm, obj):
                    out.append(subj_raw)
                    out.append(obj_raw)
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return [x for x in dict.fromkeys(out) if x][:n]

    def _fetch_kegg_kgml(self, n: int = 10) -> list[str]:
        """KEGG KGML XML: pathway ilişkileri → INHIBITS/ACTIVATES doğrudan.

        <relation entry1="X" entry2="Y" type="activation|inhibition|...">
        Onlarca yıllık biyokimya bilgisi yapılandırılmış XML olarak —
        NLP yok, yorum yok, doğrudan TAU kenarı.
        """
        _KGML_PATHWAYS = [
            "hsa04010", "hsa04151", "hsa04210", "hsa04110",
            "hsa04012", "hsa04350", "hsa04630", "hsa04310",
            "hsa04015", "hsa04014", "hsa04020", "hsa04022",
            "hsa04024", "hsa04064", "hsa04066", "hsa04068",
            "hsa04071", "hsa04072", "hsa04010", "hsa04370",
        ]
        _KGML_TYPE_MAP = {
            "activation": "ACTIVATES",
            "inhibition": "INHIBITS",
            "expression": "CAUSES",
            "repression": "INHIBITS",
            "indirect effect": "CAUSES",
            "state change": "CAUSES",
            "binding/association": "USES",
            "dissociation": "CAUSES",
            "phosphorylation": "ACTIVATES",
            "dephosphorylation": "INHIBITS",
            "ubiquitination": "CAUSES",
            "methylation": "CAUSES",
        }
        kgml_idx = self.state.get("kgml_idx", 0)
        pathway = _KGML_PATHWAYS[kgml_idx % len(_KGML_PATHWAYS)]
        self.state["kgml_idx"] = kgml_idx + 1
        out: list[str] = []
        try:
            import xml.etree.ElementTree as ET
            url = f"https://rest.kegg.jp/get/{pathway}/kgml"
            req = urllib.request.Request(url, headers=_UA)
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")
            root = ET.fromstring(xml_text)
            # entry_id → gen/bileşik ismi haritası
            entries: dict[str, str] = {}
            for entry in root.findall("entry"):
                eid = entry.get("id", "")
                graphics = entry.find("graphics")
                if graphics is not None:
                    gname = graphics.get("name", "").split(",")[0].strip()
                    if gname and 1 < len(gname) < 30:
                        entries[eid] = gname.lower()
                if eid not in entries:
                    raw = entry.get("name", "").split()[0]
                    short = raw.split(":")[-1].strip()
                    if 1 < len(short) < 20:
                        entries[eid] = short.lower()
            # relation → doğrudan TAU kenarı
            edges_added = 0
            for rel in root.findall("relation"):
                e1 = rel.get("entry1", "")
                e2 = rel.get("entry2", "")
                rel_type = rel.get("type", "")
                # Subtype daha spesifik (phosphorylation vs activation)
                subtypes = rel.findall("subtype")
                if subtypes:
                    rel_type = subtypes[0].get("name", rel_type)
                paradigm = _KGML_TYPE_MAP.get(rel_type)
                if not paradigm:
                    continue
                subj = entries.get(e1, "")
                obj = entries.get(e2, "")
                if not subj or not obj or subj == obj:
                    continue
                if self._inject_direct_edge(subj, paradigm, obj):
                    out.append(subj)
                    out.append(obj)
                    edges_added += 1
                    if edges_added >= n * 3:
                        break
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return [x for x in dict.fromkeys(out) if x][:n]

    def _next_batch(self, network: bool) -> list[Any]:
        """Bir sonraki karışık veri partisi: 10 kaynak (8 + ConceptNet + KEGG KGML)."""
        if not network:
            # Ağsız: algoritmik diziler (resumable offset ile çeşitlilik)
            base = self.state.get("total_processed", 0)
            return [
                [int((base + i) ** 1.5) % 97 + 1 for i in range(j, j + 8)]
                for j in range(0, 24, 8)
            ]
        # 10 kaynak paralel çekilir — her biri bağımsız HTTP, sıralı bekleme gerekmez
        sources = [
            (self._fetch_pubchem, 8),
            (self._fetch_chembl, 4),
            (self._fetch_uniprot, 6),
            (self._fetch_kegg, 4),
            (self._fetch_oeis, 4),
            (self._fetch_web, 5),
            (self._fetch_pubmed, 3),
            (self._fetch_wikidata, 4),
            (self._fetch_conceptnet, 20),   # ConceptNet: dil sorununun çözümü
            (self._fetch_kegg_kgml, 10),    # KEGG KGML: doğrudan INHIBITS/ACTIVATES
        ]
        batch: list[Any] = []
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(fn, n): fn.__name__ for fn, n in sources}
            for fut in as_completed(futures):
                try:
                    batch += fut.result()
                except Exception:
                    pass
        return batch

    # ─── Ana döngü: sınırsız kendi kendine büyüme ────────────────────────────

    def stream(
        self,
        time_limit_s: float | None = 300.0,
        max_cycles: int | None = None,
        persist_every: int = 20,
        consolidate_every: int = 3,
        network: bool = True,
        grow: bool = True,
        verbose: bool = True,
        should_stop: Callable[[], bool] | None = None,
    ) -> GrowthReport:
        """Sürekli büyüme akışı.

        time_limit_s=None VE max_cycles=None → SINIRSIZ (should_stop ya da
          dış kesinti durdurana dek).
        consolidate_every: kaç döngüde bir close()+reflect() (TAU örme + öz-kök).
        persist_every: kaç yeni işlemde bir diske yaz.
        should_stop: dışarıdan durdurma kancası (örn. bir dosya/bayrak kontrolü).
        """
        rep = GrowthReport()
        rep.concepts_start = len(self.engine.manifold.concepts)
        rep.edges_start = sum(len(v) for v in self.engine.tau.edges.values())
        t0 = time.monotonic()
        since_persist = 0

        def _log(msg: str) -> None:
            if verbose:
                print(f"  [{time.monotonic()-t0:6.1f}s] {msg}", flush=True)

        _log(f"Büyüme başladı — {rep.concepts_start:,} kavram. "
             f"Limit: {'SINIRSIZ' if time_limit_s is None and max_cycles is None else (f'{time_limit_s}s' if time_limit_s else f'{max_cycles} döngü')}")

        try:
            while True:
                # Durma koşulları
                if time_limit_s is not None and (time.monotonic() - t0) >= time_limit_s:
                    rep.stopped_reason = "zaman limiti"
                    break
                if max_cycles is not None and rep.cycles >= max_cycles:
                    rep.stopped_reason = "döngü limiti"
                    break
                if should_stop is not None:
                    try:
                        if should_stop():
                            rep.stopped_reason = "dış durdurma"
                            break
                    except Exception:
                        pass

                rep.cycles += 1
                if network:
                    self._refresh_gap_cache()  # NecessityEngine'i paralel fetch öncesi çalıştır
                batch = self._next_batch(network)
                if not batch:
                    _log("boş parti — kaynak geçici sustu, devam")
                    time.sleep(1.0)
                    continue

                for item in batch:
                    try:
                        obs, born = self.observer.pulse(item, grow=grow)
                    except Exception as e:
                        _log(f"nabız hatası (atlandı): {str(e)[:50]}")
                        continue
                    rep.processed += 1
                    rep.born += len(born)
                    if not obs.certified or obs.admitted_as == "rejected":
                        rep.rejected += 1
                    elif obs.admitted_as == "core":
                        rep.core += 1
                    else:
                        rep.frontier += 1
                    since_persist += 1
                    self.state["total_processed"] = self.state.get("total_processed", 0) + 1

                    if since_persist >= persist_every:
                        self.engine.auto_persist()
                        self._save_state()
                        since_persist = 0

                _log(f"döngü {rep.cycles}: +{len(batch)} işlendi "
                     f"(çek:{rep.core} sın:{rep.frontier} red:{rep.rejected} doğ:{rep.born})")

                # Periyodik konsolidasyon: TAU örme + öz-kök + anlam zenginleştirme
                if rep.cycles % consolidate_every == 0:
                    self._consolidate(_log, rep)

        except KeyboardInterrupt:
            rep.stopped_reason = "klavye kesintisi"
        except Exception as e:
            rep.stopped_reason = f"hata: {str(e)[:60]}"

        # Son konsolidasyon + kalıcılık
        try:
            self.engine.auto_persist()
            self._save_state()
        except Exception:
            pass
        rep.concepts_end = len(self.engine.manifold.concepts)
        rep.edges_end = sum(len(v) for v in self.engine.tau.edges.values())
        rep.elapsed_s = time.monotonic() - t0
        if not rep.stopped_reason:
            rep.stopped_reason = "tamamlandı"
        _log(rep.summary())
        return rep

    def _consolidate(self, _log: Callable[[str], None], rep: "GrowthReport | None" = None) -> None:
        """TAU geçişli kapanış + öz-model köklendirme (büyüdükçe kendini hatırla)."""
        try:
            from tantrium.reasoning.necessity import NecessityEngine
            ne = NecessityEngine(self.engine)
            nr = ne.run(domain="math_kernel", inject=True, find_gaps=False)
            _log(f"konsolidasyon: +{getattr(nr, 'edges_injected', 0)} zorunlu kenar")
        except Exception:
            pass
        try:
            from tantrium.meta.self_model import SelfModel
            SelfModel(self.engine).locate(persist=False)
            _log("öz-model köklendirildi (⟨SELF⟩ güncel)")
        except Exception:
            pass
        # Anlam kanalı (TopologyEncoder): yeni büyüyen semantik-köklü kavramların
        # ilişki-grafı imzasını hesapla + çapraz-boyutlu kuantum köprüleri ortaya çıkar.
        # F8 vizyonu: "Topoloji = bilgi" — büyüme yalnız node değil, ANLAM örer.
        self._meaning_consolidate(_log, rep)
        # Corrigibility: yanlışı TESPİT et (dejenere encoding + çakışma — GIMEL'in
        # göremediği üniform hata), düzeltmeyi DENE (adaptif re-encode), kalanı HATIRLA.
        self._verify_consolidate(_log, rep)
        # Aile-pencere dedup: kanonik dizilerin (lucas/tribonacci/ramanujan...) üreteç
        # tekrar-ürettiği exact-moment kopyalarını tek temsilciye indir (kök neden önlemi).
        self._dedup_family_windows(_log, rep)

    def _meaning_consolidate(
        self, _log: Callable[[str], None], rep: "GrowthReport | None" = None,
        *, max_per_pass: int = 40, quantum_per_pass: int = 12,
    ) -> None:
        """Anlam kanalını büyüme döngüsüne bağlar (additive, fail-open).

        Yeni büyümüş, semantik TAU kenarı (CAUSES/INHIBITS/ACTIVATES/IS_A/...) olan
        kavramlar için `TopologyEncoder.encode` (ilişkisel kodlama = "ne demek")
        çalıştırır ve `manifold.quantum_bridges` ile klasik-uzak/κ-yakın GİZLİ
        dolanıklığı KALICI `QUANTUM_BRIDGE` kenarına çevirir.

        SPECTRAL_BRIDGE (autonomous._discover_bridges) klasik-YAKIN köprüleri kurar;
        QUANTUM_BRIDGE bunların yapısal kaçırdığı klasik-uzak/κ-yakın gizli dolanıklığı
        yüzeye çıkarır (F8: "elma-DNA × Fibonacci"). Paradigma + kompakt kod (Q) +
        _SEMANTIC üyeliği zaten rezerve; tek eksik onu OLUŞTURAN kabloydu — burada
        bağlanıyor. ground_full/bind_percept dış duyusal veri ister (metin akışında
        yok) → büyümede doğal entegre olan anlam kanalı budur.

        quantum_per_pass: `quantum_bridges` O(N) (tüm manifoldu tarar) — köprü-tarama
        enrich'ten daha sıkı sınırlanır (büyük grafta maliyet kontrolü).
        """
        try:
            from tantrium.core.topology_encode import TopologyEncoder, _SEMANTIC_PARADIGMS
        except Exception:
            return
        if self._topo_encoder is None:
            try:
                self._topo_encoder = TopologyEncoder(self.engine)
            except Exception:
                return
        tau = self.engine.tau
        manifold = self.engine.manifold
        # Henüz zenginleştirilmemiş, en az 1 semantik kenarı olan kavramları seç.
        candidates: list[str] = []
        for name, edges in tau.edges.items():
            if name in self._meaning_seen:
                continue
            if any(getattr(e, "paradigm", None) in _SEMANTIC_PARADIGMS for e in edges):
                candidates.append(name)
            if len(candidates) >= max_per_pass:
                break
        if not candidates:
            return
        enriched = 0
        linked = 0
        quantum_scans = 0
        for name in candidates:
            self._meaning_seen.add(name)
            try:
                obj = self._topo_encoder.encode(name)  # anlam imzası (None = semantik-topraksız)
            except Exception:
                obj = None
            if obj is None:
                continue
            enriched += 1
            # Kuantum köprü taraması pahalı (O(N)) — yalnız ilk quantum_per_pass kavram.
            if quantum_scans >= quantum_per_pass:
                continue
            quantum_scans += 1
            try:
                br = manifold.quantum_bridges(name, top_k=3)
            except Exception:
                br = []
            for other, qdist in br:
                # Genesis yapay köprüleri çapa olamaz (CLAUDE.md pitfall #8 + wonder
                # self-grooming): ⟨bridge:...⟩ hedeflerini kuantum köprü saymayız.
                if other.startswith("⟨bridge:"):
                    continue
                if self._add_quantum_bridge_edge(name, other, qdist):
                    linked += 1
                    _log(f"kuantum köprü: {name} ⟷ {other} (κ-yakın {qdist:.3f}) → QUANTUM_BRIDGE")
        if enriched:
            _log(f"anlam kanalı: {enriched} kavram zenginleştirildi, "
                 f"{linked} kuantum köprü kenarı örüldü")
        if rep is not None:
            rep.meaning_enriched += enriched
            rep.bridges_found += linked

    def _dedup_family_windows(
        self, _log: Callable[[str], None], rep: "GrowthReport | None" = None,
        *, max_per_pass: int = 400,
    ) -> None:
        """Aile-içi exact-moment pencere-kopyalarını tek temsilciye indir.

        Kök neden önlemi: bazı kanonik üreteçler (lucas/tribonacci/ramanujan_tau)
        her batch'te encoder-normalizasyonu altında AYNI momente inen `algo:<aile>_b<N>`
        pencereleri üretir → tekrar birikir. Bu faz her (aile, tam-moment) için TEK
        temsilci tutar, sonraki özdeş pencereleri siler (kenarları temsilciye yönlendirir).
        `dedup_manifold.py` aracının döngü-içi, artımlı, sınırlı (max_per_pass) hâli.
        Gerçek kelime/teorem isimlerine (öneksiz) DOKUNMAZ.
        """
        import re
        fam_re = re.compile(r"^(.*?)_b\d+$")
        manifold = self.engine.manifold
        tau = self.engine.tau
        remap: dict[str, str] = {}
        processed = 0
        for name in list(manifold.concepts.keys()):
            if processed >= max_per_pass:
                break
            if name in self._fam_seen or ":" not in name:
                continue
            m = fam_re.match(name)
            if not m:
                continue
            c = manifold.concepts.get(name)
            if c is None:
                continue
            self._fam_seen.add(name)
            processed += 1
            key = (m.group(1), tuple(c.moments))  # (aile, tam-moment imzası)
            existing = self._family_reps.get(key)
            if existing is None or existing not in manifold.concepts:
                self._family_reps[key] = name  # temsilci
            elif existing != name:
                remap[name] = existing  # özdeş kopya → sil
        if not remap:
            return
        # silinenlere işaret eden kenarları temsilciye yönlendir
        for src, edges in list(tau.edges.items()):
            for e in edges:
                if e.target in remap:
                    e.target = remap[e.target]
        # silinen düğümlerin kenarlarını temsilciye taşı + düğümü kaldır
        for dead, repname in remap.items():
            dead_edges = tau.edges.pop(dead, [])
            for e in dead_edges:
                e.source = repname
            if dead_edges:
                tau.edges.setdefault(repname, []).extend(dead_edges)
            manifold.concepts.pop(dead, None)
            tau.nodes.pop(dead, None)
        # temsilcilerin kenarlarını tekilleştir (self-loop + (target,paradigm) tekrarı)
        for src in set(remap.values()):
            seen = set()
            uniq = []
            for e in tau.edges.get(src, []):
                k = (e.target, e.paradigm)
                if e.target == src or k in seen:
                    continue
                seen.add(k)
                uniq.append(e)
            tau.edges[src] = uniq
        tau._dirty = True
        _log(f"aile-dedup: {len(remap)} pencere-kopyası silindi")
        if rep is not None:
            rep.windows_deduped += len(remap)

    def _add_quantum_bridge_edge(self, a: str, b: str, qdist: float) -> bool:
        """TAU'ya çift yönlü KALICI QUANTUM_BRIDGE kenarı ekle (idempotent).

        SPECTRAL_BRIDGE'in (moment-yakın) yanındaki ikinci köprü tipi: klasik-uzak/
        κ-yakın gizli dolanıklık. `quantum_dist` alanına κ-mesafe yazılır (save/load
        Q koduyla zaten destekli). Yeni kenar örüldüyse True döner."""
        from tantrium.graph.knowledge_graph import KnowledgeEdge
        if a == b:
            return False
        created = False
        for src, tgt in ((a, b), (b, a)):
            edges = self.engine.tau.edges.setdefault(src, [])
            exists = any(
                e.target == tgt and e.paradigm == "QUANTUM_BRIDGE" for e in edges
            )
            if not exists:
                edges.append(KnowledgeEdge(
                    source=src, target=tgt,
                    distance=round(qdist, 6), paradigm="QUANTUM_BRIDGE",
                    quantum_dist=round(qdist, 6),
                ))
                created = True
        if created:
            self.engine.tau._dirty = True
        return created

    def _verify_consolidate(
        self, _log: Callable[[str], None], rep: "GrowthReport | None" = None,
    ) -> None:
        """Corrigibility — yanlışı TESPİT et, düzeltmeyi DENE, kalanı HATIRLA.

        GIMEL (`pipeline.stage_l5_gimel`) içsel GÖRELİ zayıflığı bulur
        (argmin_paradigma margin) ama hata ÜNİFORM olduğunda (protein/glucose:
        G=PᵀP=I → μ_k≡1, bütün marjinler tekdüze iyi) göreli zayıf halka yoktur —
        GIMEL temiz rapor verir, temsil yine de yanlıştır. Bu faz o kör noktayı
        kapatır; iki yapısal yanlış-sinyali GIMEL'den bağımsız okur:

          1. DEJENERE encoding: moment yayılımı (max−min) < _DEGEN_SPREAD
             (faithful Hausdorff dizisi azalır; tekdüze = temsil çökmüş).
          2. ÇAKIŞMA: en yakın FARKLI kavram L1 < _COLLISION_EPS
             (iki ayrı şey aynı noktaya düşmüş = encoder ayırmıyor).

        Tespit → adaptif derin re-encode (DÜZELT) → düzelmeyen suspect hafızaya
        (`state["suspect"]`, growth_state.json ile kalıcı → unutmaz, #4). Düzeltme
        yalnız düz isimlerde denenir (oeis:/algo:/theorem: önekli adlarda re-encode
        yanlış temsile 'düzeltebilir' — güvenli taraf: önekli/⟨⟩ ad → yalnız işaretle).
        """
        manifold = self.engine.manifold
        encoder = getattr(self.engine, "encoder", None)
        suspect = self.state.setdefault("suspect", [])
        suspect_set = set(suspect)
        checked = degen = collided = corrected = 0
        collision_scans = 0
        for name, c in list(manifold.concepts.items()):
            if checked >= _VERIFY_MAX:
                break
            if name in self._verify_seen or name.startswith("⟨"):
                continue
            mu = [float(m) for m in getattr(c, "moments", [])]
            if len(mu) < 2:
                continue
            self._verify_seen.add(name)
            checked += 1
            spread = max(mu) - min(mu)

            # 1) DEJENERE encoding (üniform moment = protein/glucose sınıfı)
            if spread < _DEGEN_SPREAD:
                degen += 1
                fixed = False
                # 2) DÜZELT: adaptif derin re-encode (yalnız düz/SMILES isimlerde)
                safe_name = (":" not in name) and encoder is not None
                if safe_name:
                    try:
                        new_enc = encoder.encode_adaptive(name)
                        nmu = [float(m) for m in getattr(new_enc, "moments", [])]
                        if nmu and (max(nmu) - min(nmu)) >= _DEGEN_SPREAD:
                            import fractions
                            c.moments = [
                                fractions.Fraction(m).limit_denominator(10 ** 9)
                                for m in new_enc.moments
                            ]
                            corrected += 1
                            fixed = True
                            _log(f"düzeltildi: {name} dejenere→ayrıştı "
                                 f"(yayılım {max(nmu) - min(nmu):.3f})")
                    except Exception:
                        pass
                if not fixed and name not in suspect_set:
                    suspect.append(name)
                    suspect_set.add(name)
                    _log(f"şüpheli (dejenere, düzeltilemedi): {name}")
                continue

            # 3) ÇAKIŞMA: en yakın FARKLI kavram çok yakınsa (O(N) — sınırlı)
            if collision_scans >= _VERIFY_COLLISION_MAX:
                continue
            collision_scans += 1
            try:
                hits = manifold.nearest(c, n=1, metric="l1")
            except Exception:
                hits = []
            if hits:
                other, d = hits[0]
                if other != name and float(d) < _COLLISION_EPS:
                    collided += 1
                    pair = f"{name}~{other}"
                    if pair not in suspect_set:
                        suspect.append(pair)
                        suspect_set.add(pair)
                        _log(f"şüpheli (çakışma): {name} ≈ {other} (L1 {float(d):.4f})")

        # suspect hafızayı sınırla (son 500 — kalıcı ama sınırsız büyümesin)
        if len(suspect) > 500:
            self.state["suspect"] = suspect[-500:]
        if checked:
            _log(f"doğrulama: {checked} denetlendi, {degen} dejenere "
                 f"({corrected} düzeltildi), {collided} çakışma şüphesi")
        if rep is not None:
            rep.corrected += corrected
            rep.suspect_flagged += (degen - corrected) + collided
