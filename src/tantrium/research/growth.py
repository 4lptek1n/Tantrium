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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

_UA = {"User-Agent": "Tantrium-AGI/1.0 (research; mailto:research@tantrium.ai)"}
_RATE_LIMIT_S = 0.34
_STATE_DIR = pathlib.Path(".tantrium")
_STATE_FILE = _STATE_DIR / "growth_state.json"

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

    def summary(self) -> str:
        dc = self.concepts_end - self.concepts_start
        de = self.edges_end - self.edges_start
        return (
            f"═══ BÜYÜME RAPORU ({self.elapsed_s:.1f}s, {self.cycles} döngü) ═══\n"
            f"İşlenen: {self.processed} | çekirdek: {self.core} | "
            f"sınır: {self.frontier} | reddedilen: {self.rejected} | doğan: {self.born}\n"
            f"Kavram: {self.concepts_start:,} → {self.concepts_end:,} (+{dc})\n"
            f"TAU kenar: {self.edges_start:,} → {self.edges_end:,} (+{de})\n"
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
        """Reviewed (Swiss-Prot) protein dizileri. Cursor durumu resumable."""
        cursor = self.state.get("uniprot_cursor")
        if not cursor:
            q = urllib.parse.quote(f"reviewed:true AND organism_id:{organism}")
            cursor = (f"https://rest.uniprot.org/uniprotkb/search?query={q}"
                      f"&format=json&size={min(size, 100)}"
                      f"&fields=accession,sequence,length")
        out: list[str] = []
        try:
            data, next_url = _http_json_link(cursor)
            for entry in (data or {}).get("results", []):
                seq = ((entry or {}).get("sequence") or {}).get("value", "")
                if seq and len(seq) >= 20:
                    out.append(seq)
            self.state["uniprot_cursor"] = next_url  # düşse None → baştan
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S)
        return out

    def _fetch_web(self, n: int = 5) -> list[str]:
        """Manifold boşluklarına göre Wikipedia'dan kavramlar çek.

        Sistem ne bilmediğini biliyor (gaps). O boşlukları Wikipedia'da arar,
        başlık + kategoriler + bağlantı isimleri döndürür. Ham metin değil —
        temiz kavram adları. Sistem kendi kör noktalarını doldurur.
        """
        # Hangi boşluğu araştıracağız?
        web_idx = self.state.get("web_gap_idx", 0)
        concepts_list: list[str] = []

        try:
            from tantrium.reasoning.necessity import NecessityEngine
            ne = NecessityEngine(self.engine)
            gaps = ne.find_manifold_gaps(domain="math_kernel", top_k=12)
            if not gaps:
                # Gaps yoksa manifolddan rastgele sınır kavramı al
                tau = self.engine.tau
                causal = {"CAUSES", "INHIBITS", "ACTIVATES"}
                frontier = [
                    s for s, edges in tau.edges.items()
                    if any(e.paradigm in causal for e in edges)
                    and len(tau.edges.get(s, [])) < 5
                ]
                gaps_labels = frontier[web_idx % max(len(frontier), 1): web_idx % max(len(frontier), 1) + 3] if frontier else []
            else:
                idx = web_idx % len(gaps)
                gaps_labels = [g.concept_a for g in gaps[idx:idx + 3]]
        except Exception:
            gaps_labels = ["mathematics", "biochemistry", "topology"]

        self.state["web_gap_idx"] = web_idx + 1

        for query in gaps_labels[:3]:
            try:
                # Wikipedia OpenSearch — ilgili başlıkları bul
                q = urllib.parse.quote(str(query)[:80])
                url = (f"https://en.wikipedia.org/w/api.php"
                       f"?action=opensearch&search={q}&limit=3&format=json")
                data = _http_json(url)
                titles = (data[1] if isinstance(data, list) and len(data) > 1 else [])

                for title in titles[:2]:
                    t = urllib.parse.quote(str(title)[:120])
                    # Sayfa: kategoriler + bağlantılar + kısa özet (extracts)
                    url2 = (f"https://en.wikipedia.org/w/api.php"
                            f"?action=query&prop=categories|links|extracts"
                            f"&titles={t}&format=json&exintro=1&exsentences=3"
                            f"&explaintext=1&cllimit=8&pllimit=12&redirects=1")
                    page_data = _http_json(url2)
                    pages = ((page_data or {}).get("query") or {}).get("pages") or {}
                    for pid, page in pages.items():
                        if pid == "-1":
                            continue
                        # Sayfa başlığı
                        concepts_list.append(str(page.get("title", "")))
                        # Kategoriler: "Category:Kinase inhibitors" → "kinase inhibitors"
                        _SKIP = ("All ", "Articles ", "Wikipedia ", "Pages ", "CS1 ",
                                 "Webarchive", "Use ", "Short description")
                        for cat in (page.get("categories") or [])[:8]:
                            cname = cat.get("title", "").replace("Category:", "").strip()
                            if (cname and len(cname) < 60
                                    and not any(cname.startswith(s) for s in _SKIP)):
                                concepts_list.append(cname)
                        # Bağlantı başlıkları (linked Wikipedia pages)
                        for link in (page.get("links") or [])[:6]:
                            lname = link.get("title", "").strip()
                            if lname and len(lname) < 60 and not lname.startswith(("Wikipedia:", "Help:", "File:")):
                                concepts_list.append(lname)
                        # Sayfa özeti → kausal ilişki çıkar (manifolda ham metin olarak EKLENMEZ)
                        extract = str(page.get("extract") or "").strip()
                        if extract and len(extract) > 50:
                            try:
                                self.ai.learn(extract)
                            except Exception:
                                pass
                    time.sleep(_RATE_LIMIT_S)

            except Exception:
                pass

        # Tekrarları kaldır, boşları at, max n
        seen: set[str] = set()
        out: list[str] = []
        for c in concepts_list:
            c = c.strip()
            if c and c not in seen and len(c) > 3:
                seen.add(c)
                out.append(c)
            if len(out) >= n:
                break

        time.sleep(_RATE_LIMIT_S)
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
                    self.ai.learn(desc[:400])
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
                        self.ai.learn(abstract_text[:2000])
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
                        self.ai.learn(f"{labels[0]} {rel_word} {labels[1]}.")
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(_RATE_LIMIT_S * 2)  # Wikidata rate limit daha kısıtlı
        return [x for x in dict.fromkeys(out) if x][:n]

    def _next_batch(self, network: bool) -> list[Any]:
        """Bir sonraki karışık veri partisi: 8 kaynak."""
        if not network:
            # Ağsız: algoritmik diziler (resumable offset ile çeşitlilik)
            base = self.state.get("total_processed", 0)
            return [
                [int((base + i) ** 1.5) % 97 + 1 for i in range(j, j + 8)]
                for j in range(0, 24, 8)
            ]
        batch: list[Any] = []
        batch += self._fetch_pubchem(8)    # kimya: PubChem SMILES
        batch += self._fetch_chembl(4)     # kimya: ChEMBL biyoaktif moleküller
        batch += self._fetch_uniprot(6)    # biyoloji: UniProt protein dizileri
        batch += self._fetch_kegg(4)       # biyoloji: KEGG yolak genleri
        batch += self._fetch_oeis(4)       # matematik: tamsayı dizileri
        batch += self._fetch_web(5)        # web: boşluk-güdümlü Wikipedia kavramları
        batch += self._fetch_pubmed(3)     # biyomedikal: PubMed kausal öğrenim
        batch += self._fetch_wikidata(4)   # ontoloji: Wikidata typed triples
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

                # Periyodik konsolidasyon: TAU örme + öz-kök
                if rep.cycles % consolidate_every == 0:
                    self._consolidate(_log)

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

    def _consolidate(self, _log: Callable[[str], None]) -> None:
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
