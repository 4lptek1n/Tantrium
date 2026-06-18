"""Çok-boyutlu fitsiz büyüme koşucusu — dil + molekül + sayı + protein, hepsi AYNI moment uzayı.

Kullanıcı: 'sadece dili büyütme, diğer boyutları da dahil et, köklenme/grounding olsun.'
F24 yasası: her boyut kendi GERÇEK ölçümünden girer (metin değil):
  - molekül (PubChem SMILES) → atom-bağ Laplacian spektrumu  [observe = tam kapı + grounding]
  - sayı dizisi (OEIS)        → power moment                  [observe]
  - protein (UniProt)         → dizi/spektrum                 [observe]
  - dil (Wikipedia)           → ortak-geçiş + SVO             [absorb = hızlı, fitsiz]

observe tam evren-kapısını (truth+grounding+aleph) çalıştırır → GERÇEK köklenme (sadece dil
değil). Çok-boyut = aynı kavram birden çok boyutta → çapraz-boyut grounding (F8).

Resumable (GrowthEngine.state + manifold disk-persist). STOP_MULTIDIM ile durur.
TEK-YAZAR: absorb_forever / autonomous_forever ile AYNI ANDA çalıştırma.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import tantrium
from tantrium.research.autonomous import AutonomousObserver
from tantrium.research.growth import GrowthEngine
from tantrium.research.text_source import fetch_random_titles, fetch_wikipedia

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"
STOP = STATE / "STOP_MULTIDIM"
STATUS = STATE / "multidim_status.json"
GE_STATE = STATE / "multidim_state.json"


def main() -> None:
    STATE.mkdir(exist_ok=True)
    ai = tantrium.AI()
    eng = ai._engine
    eng._ai = ai
    obs = AutonomousObserver(eng)
    ge = GrowthEngine(eng, obs)
    if GE_STATE.exists():
        try:
            ge.state.update(json.loads(GE_STATE.read_text()))
        except Exception:
            pass
    # HEDEF-GÜDÜM (ASI Pilar B): cognition GoalPhase hedef yoksa NO-OP — sürekli hedef koy ki
    # döngü goal-directed olsun (hedef→boşluk→araştır→öz-doğrula→eylem→ilerleme). Eksiksiz ASI.
    GOALS = ["understand connections across all domains",
             "discover hidden cross-domain structure",
             "find the laws governing observed data"]
    try:
        for g in GOALS:
            ai.set_goal(g)
    except Exception as exc:
        print(f"[{time.strftime('%H:%M:%S')}] set_goal hata: {str(exc)[:60]}", flush=True)
    t0 = time.time()
    dims = {"molecule": 0, "number": 0, "protein": 0, "text": 0, "law": 0, "rejected": 0}
    asi = {"bridges": 0, "hypotheses": 0, "corrected": 0, "proofs": 0,
           "curiosity": 0, "relearn": 0}
    cyc = 0
    COGNITION_EVERY = 4   # ASI bilişi: gizli-bağlantı keşfi + hipotez + öz-düzeltme + ispat
    print(f"[{time.strftime('%H:%M:%S')}] çok-boyutlu büyüme — SONSUZ (STOP: {STOP})", flush=True)

    def _obs(x):
        try:
            o = obs.observe(x)
            if getattr(o, "admitted_as", None) == "rejected":
                dims["rejected"] += 1
                return False
            return True
        except Exception:
            return False

    while not STOP.exists():
        cyc += 1
        # 1) MOLEKÜL — gerçek atom-bağ yapısı (F24)
        for smi in ge._fetch_pubchem(10):
            if _obs(smi):
                dims["molecule"] += 1
        # 2) SAYI — gerçek power moment + VAR EDEN YASA (IS_GOVERNED_BY)
        for seq in ge._fetch_oeis(4):
            try:
                o = obs.observe(seq)
            except Exception:
                continue
            if getattr(o, "admitted_as", None) == "rejected":
                dims["rejected"] += 1
                continue
            dims["number"] += 1
            nm = getattr(o, "name", None)
            # var eden yasa: dizinin yönetici yineleme yasasını KEŞFET → IS_GOVERNED_BY kenarı
            if nm:
                try:
                    law = ai.discover_law(seq)
                    if getattr(law, "law_holds", False):
                        ai.ground_full(nm, law=f"recurrence_order_{law.order}")
                        dims["law"] += 1
                except Exception:
                    pass
        # 3) PROTEIN
        try:
            prots = ge._fetch_uniprot(6)
        except Exception:
            prots = []
        for name in prots:
            if _obs(name):
                dims["protein"] += 1
        # 4) DİL — hızlı fitsiz absorb (ortak-geçiş + SVO)
        for title in fetch_random_titles(4):
            if STOP.exists():
                break
            txt = fetch_wikipedia(title)
            if txt:
                try:
                    ai.absorb(txt, persist=False)
                    dims["text"] += 1
                except Exception:
                    pass
            time.sleep(0.8)
        # ASI BİLİŞİ (her COGNITION_EVERY turda): gizli-bağlantı keşfi (quantum_bridges) +
        # hipotez üretimi + öz-düzeltme (corrigibility) + ispat. Beslemenin üstüne ASI döngüsü.
        if cyc % COGNITION_EVERY == 0:
            try:
                rep = ai.cognition(mode="batch", max_cycles=1, network=False)
                asi["bridges"] += int(getattr(rep, "bridges_discovered", 0) or 0)
                asi["hypotheses"] += int(getattr(rep, "hypotheses_generated", 0) or 0)
                asi["corrected"] += int(getattr(rep, "contradictions_resolved", 0) or 0)
                asi["proofs"] += int(getattr(rep, "proofs_completed", 0) or 0)
                asi["curiosity"] += int(getattr(rep, "curiosity_researched", 0) or 0)
                asi["relearn"] += int(getattr(rep, "relearned", 0) or 0)
            except Exception as exc:
                print(f"[{time.strftime('%H:%M:%S')}] cognition hata: {str(exc)[:60]}",
                      flush=True)
        # persist + durum
        try:
            eng.auto_persist()
            GE_STATE.write_text(json.dumps(ge.state), encoding="utf-8")
        except Exception:
            pass
        status = {
            "cycle": cyc, "dims": dims, "asi": asi,
            "concepts_total": len(eng.manifold.concepts),
            "uptime_min": round((time.time() - t0) / 60, 1),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{time.strftime('%H:%M:%S')}] tur {cyc}: molekül={dims['molecule']} "
              f"sayı={dims['number']} yasa={dims['law']} protein={dims['protein']} "
              f"metin={dims['text']} red={dims['rejected']} | ASI köprü={asi['bridges']} "
              f"hipotez={asi['hypotheses']} merak={asi['curiosity']} düzelt={asi['corrected']} "
              f"ispat={asi['proofs']} | kavram {len(eng.manifold.concepts)} "
              f"({status['uptime_min']}dk)", flush=True)

    print(f"[{time.strftime('%H:%M:%S')}] STOP — durduruldu (tur {cyc}).", flush=True)
    try:
        eng.auto_persist()
    except Exception:
        pass


if __name__ == "__main__":
    main()
