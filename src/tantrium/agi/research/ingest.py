"""Gerçek Veri Ingestion — Manifoldu Dünya Verisiyle Büyütme.

Sentetik dizi değil. Gerçek bilimsel veritabanlarından akan veri:

  UniProt   → gerçek protein dizileri (amino asit)      → biology
  PubChem   → gerçek ilaç/bileşik SMILES                → chemistry
  OEIS      → gerçek matematiksel tamsayı dizileri      → math
  RCSB PDB  → gerçek protein yapı metadatası            → biology

Her kayıt AutonomousObserver'dan geçer:
  encode → Aleph sertifika (gerçek mi?) → çapa sınıflandırma →
  manifolda ekle → cross-domain köprü keşfi → kalıcı kayıt

Resumable: ingest durumu .tantrium/ingest_state.json içinde tutulur.
Oturum yeniden başlasa bile kaldığı yerden devam eder.
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine

_UA = {"User-Agent": "Tantrium-AGI/1.0 (research; mailto:research@tantrium.ai)"}
_RATE_LIMIT_S = 0.34          # ~3 req/s — UniProt/PubChem dostu
_STATE_DIR = pathlib.Path(".tantrium")
_STATE_FILE = _STATE_DIR / "ingest_state.json"


# ─── HTTP yardımcı ────────────────────────────────────────────────────────────

def _http_json(url: str, timeout: float = 20.0):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_json_with_link(url: str, timeout: float = 20.0):
    """JSON döndür + Link header'daki 'next' cursor URL'sini (varsa) döndür."""
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        link = resp.headers.get("Link", "") or ""
    # Link: <https://...cursor=XXX>; rel="next"
    # URL içinde virgül olabilir (fields=a,b,c) — regex ile <...>; rel="next" yakala
    import re
    next_url = None
    m = re.search(r'<([^>]+)>\s*;\s*rel="next"', link)
    if m:
        next_url = m.group(1)
    return body, next_url


# ─── Ingest sonucu ────────────────────────────────────────────────────────────

@dataclass
class IngestBatch:
    """Tek bir ingestion partisinin sonucu."""
    source: str
    fetched: int
    certified: int
    new_concepts: int
    bridges: int
    duration_s: float

    def line(self) -> str:
        return (
            f"  {self.source:<10} fetched={self.fetched:<4} "
            f"certified={self.certified:<4} new={self.new_concepts:<4} "
            f"bridges={self.bridges:<4} ({self.duration_s:.1f}s)"
        )


@dataclass
class IngestReport:
    batches: list[IngestBatch] = field(default_factory=list)
    total_new: int = 0
    total_bridges: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def summary(self) -> str:
        lines = ["═══ GERÇEK VERİ INGESTION RAPORU ═══"]
        for b in self.batches:
            lines.append(b.line())
        lines.append(f"  {'─'*54}")
        lines.append(f"  TOPLAM yeni kavram: {self.total_new}  |  köprü: {self.total_bridges}")
        return "\n".join(lines)


# ─── Veri Ingestor ────────────────────────────────────────────────────────────

class DataIngestor:
    """Gerçek bilimsel veritabanlarından manifoldu büyütür.

    Örnek:
        ing = DataIngestor(engine)
        report = ing.run(uniprot=200, pubchem=100, oeis_keywords=["L-function"])
        print(report.summary())
    """

    def __init__(
        self,
        engine: "AGIEngine",
        bridge_threshold: float = 3e-2,
        persist_every: int = 50,
        verbose: bool = True,
    ) -> None:
        self.engine = engine
        self.verbose = verbose
        from tantrium.agi.research.autonomous import AutonomousObserver
        self.observer = AutonomousObserver(
            engine, bridge_threshold=bridge_threshold, persist_every=persist_every
        )
        self.state = self._load_state()

    # ── Durum (resumable) ─────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if _STATE_FILE.exists():
            try:
                return json.loads(_STATE_FILE.read_text())
            except Exception:
                pass
        return {"uniprot_offset": 0, "pubchem_cid": 1, "ingested": {}}

    def _save_state(self) -> None:
        _STATE_DIR.mkdir(exist_ok=True)
        _STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def _seen(self, source: str, key: str) -> bool:
        return key in self.state["ingested"].get(source, [])

    def _mark(self, source: str, key: str) -> None:
        self.state["ingested"].setdefault(source, [])
        # bellek için son 5000 ID'yi tut
        lst = self.state["ingested"][source]
        lst.append(key)
        if len(lst) > 5000:
            self.state["ingested"][source] = lst[-5000:]

    # ── Ortak observe + sayım ─────────────────────────────────────────────────

    def _observe_all(
        self, items: list[tuple[str, object, str]], source: str
    ) -> IngestBatch:
        """items: (name, encodable_input, domain) listesi → observer'dan geçir."""
        t0 = time.monotonic()
        certified = new = bridges = 0
        for name, raw, domain in items:
            try:
                obs = self.observer.observe(raw, name=name)
            except Exception:
                continue
            # domain'i düzelt (observe "observed" atıyor)
            c = self.engine.manifold.concepts.get(obs.name)
            if c is not None and getattr(c, "domain", None) == "observed":
                c.domain = domain
                node = self.engine.tau.nodes.get(obs.name)
                if node is not None:
                    node.domain = domain
            if obs.certified:
                certified += 1
            if obs.is_new:
                new += 1
            bridges += len(obs.bridges)
            self._mark(source, name)
        self.engine.auto_persist()
        self._save_state()
        return IngestBatch(
            source=source, fetched=len(items), certified=certified,
            new_concepts=new, bridges=bridges, duration_s=time.monotonic() - t0,
        )

    # ── UniProt: gerçek protein dizileri ──────────────────────────────────────

    def fetch_uniprot(self, size: int = 100, organism: int = 9606) -> list[tuple[str, object, str]]:
        """Reviewed (Swiss-Prot) protein dizileri çek. Resumable offset ile.

        Amino asit dizisi → bigram geçiş matrisi → moment uzayı.
        """
        # Cursor-based pagination: bir önceki turdan kalan 'next' URL'sini kullan
        cursor_url = self.state.get("uniprot_cursor")
        if not cursor_url:
            q = urllib.parse.quote(f"reviewed:true AND organism_id:{organism}")
            cursor_url = (
                f"https://rest.uniprot.org/uniprotkb/search?query={q}"
                f"&format=json&size={min(size, 500)}"
                f"&fields=accession,protein_name,sequence,length"
            )
        items: list[tuple[str, object, str]] = []
        try:
            data, next_url = _http_json_with_link(cursor_url)
            for entry in data.get("results", []):
                acc = entry.get("primaryAccession")
                seq = (entry.get("sequence") or {}).get("value", "")
                if not acc or not seq or len(seq) < 20:
                    continue
                key = f"uniprot:{acc}"
                if self._seen("uniprot", key):
                    continue
                # amino asit dizisini metin olarak encode et (bigram yapısı)
                items.append((key, seq, "biology"))
            # next cursor'ı sakla → sonraki tur yeni sayfadan başlar
            self.state["uniprot_cursor"] = next_url
            time.sleep(_RATE_LIMIT_S)
        except Exception as e:
            if self.verbose:
                print(f"  UniProt hata: {e}")
        return items

    # ── PubChem: gerçek molekül SMILES ────────────────────────────────────────

    def fetch_pubchem(self, count: int = 100) -> list[tuple[str, object, str]]:
        """CID sırasıyla gerçek bileşik SMILES çek. Resumable cid ile.

        SMILES → Morgan fingerprint → moment uzayı.
        """
        from tantrium.agi.core.encoder import encode_smiles

        start_cid = self.state.get("pubchem_cid", 1)
        cids = list(range(start_cid, start_cid + count))
        cid_str = ",".join(str(c) for c in cids)
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid_str}"
            f"/property/SMILES,MolecularFormula/JSON"
        )
        items: list[tuple[str, object, str]] = []
        try:
            data = _http_json(url)
            props = (data.get("PropertyTable") or {}).get("Properties") or []
            for p in props:
                cid = p.get("CID")
                smiles = p.get("SMILES", "")
                formula = p.get("MolecularFormula", "")
                if not cid or not smiles:
                    continue
                key = f"pubchem:{cid}"
                if self._seen("pubchem", key):
                    continue
                try:
                    obj = encode_smiles(smiles, name=key)
                    if obj.moments and len(obj.moments) >= 4:
                        # encode edilmiş moment'leri doğrudan ver
                        items.append((key, [float(m) for m in obj.moments], "chemistry"))
                except Exception:
                    continue
            time.sleep(_RATE_LIMIT_S)
        except Exception as e:
            if self.verbose:
                print(f"  PubChem hata: {e}")
        self.state["pubchem_cid"] = start_cid + count
        return items

    # ── OEIS: gerçek matematiksel diziler ─────────────────────────────────────

    def fetch_oeis(self, keyword: str, max_results: int = 8) -> list[tuple[str, object, str]]:
        q = urllib.parse.quote(keyword)
        url = f"https://oeis.org/search?q={q}&fmt=json&start=0"
        items: list[tuple[str, object, str]] = []
        try:
            data = _http_json(url)
            entries = data if isinstance(data, list) else (data.get("results") or [])
            for entry in entries[:max_results]:
                num = entry.get("number")
                raw = entry.get("data", "")
                if num is None or not raw:
                    continue
                key = f"oeis:A{int(num):06d}"
                if self._seen("oeis", key):
                    continue
                try:
                    vals = [float(x) for x in str(raw).split(",")[:32]
                            if x.strip().lstrip("-").replace(".", "", 1).isdigit()]
                    if len(vals) >= 6:
                        items.append((key, vals, "math"))
                except Exception:
                    continue
            time.sleep(_RATE_LIMIT_S)
        except Exception as e:
            if self.verbose:
                print(f"  OEIS hata: {e}")
        return items

    # ── Tam ingestion oturumu ─────────────────────────────────────────────────

    def run(
        self,
        uniprot: int = 0,
        pubchem: int = 0,
        oeis_keywords: list[str] | None = None,
    ) -> IngestReport:
        """Gerçek veri çek, certify et, manifolda ekle, köprüleri keşfet."""
        report = IngestReport()

        if uniprot > 0:
            items = self.fetch_uniprot(size=uniprot)
            b = self._observe_all(items, "uniprot")
            report.batches.append(b)
            if self.verbose:
                print(b.line())

        if pubchem > 0:
            items = self.fetch_pubchem(count=pubchem)
            b = self._observe_all(items, "pubchem")
            report.batches.append(b)
            if self.verbose:
                print(b.line())

        for kw in (oeis_keywords or []):
            items = self.fetch_oeis(kw)
            b = self._observe_all(items, "oeis")
            b.source = f"oeis:{kw[:12]}"
            report.batches.append(b)
            if self.verbose:
                print(b.line())

        report.total_new = sum(b.new_concepts for b in report.batches)
        report.total_bridges = sum(b.bridges for b in report.batches)
        return report

    # ── Sürekli ölçekleme döngüsü ─────────────────────────────────────────────

    def scale(
        self,
        rounds: int = 10,
        per_round_uniprot: int = 100,
        per_round_pubchem: int = 100,
        time_limit_s: float = 600.0,
    ) -> IngestReport:
        """Çoklu tur — manifoldu büyütmek için sürekli akış.

        Her tur UniProt + PubChem'den yeni kayıt çeker. Resumable durum
        sayesinde her tur farklı kayıtlar gelir. time_limit dolunca durur.
        """
        t_start = time.monotonic()
        full = IngestReport()
        for r in range(rounds):
            if time.monotonic() - t_start >= time_limit_s:
                break
            if self.verbose:
                n = len(self.engine.manifold.concepts)
                print(f"\n  ── Tur {r+1}/{rounds}  (manifold: {n:,} kavram) ──")
            rep = self.run(
                uniprot=per_round_uniprot,
                pubchem=per_round_pubchem,
            )
            full.batches.extend(rep.batches)
        full.total_new = sum(b.new_concepts for b in full.batches)
        full.total_bridges = sum(b.bridges for b in full.batches)
        return full
