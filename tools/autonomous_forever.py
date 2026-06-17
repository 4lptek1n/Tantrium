"""Sürekli özerklik koşucusu — çekirdek insan eli olmadan SONSUZ döner (zeka gelişimi).

9-halka native cognition döngüsünü (network=True) durmadan tur tur koşar:
  öz-hedef · merak-araştırma · hipotez üret+tasarla+doğrula · corrigibility/relearn ·
  çelişki-tarama · kod-büyüme · üretim→geri-yut · köprü-keşfi · ispat · büyüme.

Dayanıklılık (ephemeral konteyner için):
  - Her tur PersistPhase ile manifold/tau/growth_state DİSKE yazılır (resumable).
  - Her N turda git add/commit/push results/agi → konteyner reclaim olsa bile
    yeniden başlatılınca kaldığı yerden devam eder.
  - .tantrium/autonomy_status.json = canlı ilerleme (kontrol için).
  - .tantrium/STOP_AUTONOMY dosyası oluşturulursa düzgün durur.

Kullanım:  nohup python -u tools/autonomous_forever.py > .tantrium/autonomy.log 2>&1 &
Durdurma:  touch .tantrium/STOP_AUTONOMY
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import tantrium

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".tantrium"
STOP_FILE = STATE_DIR / "STOP_AUTONOMY"
STATUS_FILE = STATE_DIR / "autonomy_status.json"
HYP_FILE = STATE_DIR / "autonomy_hypotheses.jsonl"

COMMIT_EVERY = 3          # kaç turda bir git'e dayanıklılık commit'i
CYCLES_PER_ROUND = 2      # tur başına cognition batch döngüsü (ağsız akıl/self)
ROUND_BUDGET_S = 1200     # tur başına süre tavanı (sonsuz döngü, tur sınırlı)
FOCUS = "oncology"        # ODAKLI büyüme: genişlik-spam yerine tek-domain UZMAN derinlik
BRANCH = "claude/seninle-agi-yapacagiz-XwJRz"


def _git(*args: str) -> None:
    try:
        subprocess.run(["git", *args], cwd=str(ROOT), check=False,
                       capture_output=True, timeout=180)
    except Exception:
        pass


def _commit_growth(round_n: int, totals: dict) -> None:
    _git("add", "results/agi")
    msg = (f"Autonomous growth (forever runner round {round_n}): "
           f"+{totals['concepts']} concepts, {totals['hypotheses']} hyps, "
           f"{totals['bridges']} bridges cum. — durability checkpoint")
    _git("commit", "-q", "-m", msg)
    _git("push", "origin", f"HEAD:{BRANCH}")


def main() -> None:
    STATE_DIR.mkdir(exist_ok=True)
    print(f"[{time.strftime('%H:%M:%S')}] özerklik koşucusu başlıyor — SONSUZ (STOP: {STOP_FILE})",
          flush=True)
    ai = tantrium.AI()
    e = ai._engine
    t_start = time.time()
    totals = {"concepts": 0, "edges": 0, "hypotheses": 0, "hyp_tested": 0,
              "curiosity": 0, "relearn": 0, "bridges": 0, "reingest": 0,
              "proofs": 0, "contradictions": 0}
    round_n = 0
    seen_hyps: set[str] = set()

    while not STOP_FILE.exists():
        round_n += 1
        t0 = time.time()
        # FAZ 1 — ODAKLI VERİ: onkoloji-yoğun büyüme (yalnız onkoloji kaynakları +
        # 8-boyut enrichment + corrigibility temizlik). Genişlik-spam'i yerine derinlik.
        grow_added = 0
        try:
            grp = ai.grow(focus=FOCUS, time_limit_s=ROUND_BUDGET_S * 0.6,
                          network=True, verbose=False)
            grow_added = int(getattr(grp, "concepts_end", 0) - getattr(grp, "concepts_start", 0))
        except Exception as exc:
            print(f"[{time.strftime('%H:%M:%S')}] tur {round_n} grow hata: {exc} — devam", flush=True)

        # FAZ 2 — AĞSIZ AKIL/SELF: odaklı veri ÜSTÜNDE reasoning/self/hipotez
        # (ağ=False → yeni odaksız spam çekmez; yalnız var olan onkoloji çekirdeğini işler).
        try:
            rep = ai.cognition(mode="batch", max_cycles=CYCLES_PER_ROUND,
                               time_limit_s=ROUND_BUDGET_S * 0.4, network=False)
        except Exception as exc:  # fail-open: bir tur çökse de SONSUZ döngü durmaz
            print(f"[{time.strftime('%H:%M:%S')}] tur {round_n} cognition hata: {exc} — devam", flush=True)
            time.sleep(5)
            continue

        totals["concepts"] += grow_added
        totals["concepts"] += rep.concepts_added
        totals["edges"] += rep.edges_added
        totals["hypotheses"] += rep.hypotheses_generated
        totals["hyp_tested"] += rep.hypotheses_tested
        totals["curiosity"] += rep.curiosity_researched
        totals["relearn"] += rep.relearned
        totals["bridges"] += rep.bridges_discovered
        totals["reingest"] += rep.artifacts_reingested
        totals["proofs"] += rep.proofs_completed
        totals["contradictions"] += rep.contradictions_resolved

        # YENİ sertifikalı hipotezleri kalıcı günlüğe (denetlenebilir bilim birikimi)
        new_h = 0
        for h in getattr(e, "_cognition_hypotheses", []):
            s = h.get("statement", "")
            if s and s not in seen_hyps:
                seen_hyps.add(s)
                new_h += 1
                with HYP_FILE.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(h, ensure_ascii=False) + "\n")

        gm = getattr(e, "_goal_manifold", None)
        goals = [g.name for g in gm.goals] if gm else []
        status = {
            "round": round_n,
            "uptime_min": round((time.time() - t_start) / 60, 1),
            "round_s": round(time.time() - t0, 1),
            "concepts_total": len(e.manifold.concepts),
            "cumulative": totals,
            "new_hypotheses_this_round": new_h,
            "self_goals": goals[-5:],
            "last_narration": (rep.narrations[-1][:240] if rep.narrations else ""),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{time.strftime('%H:%M:%S')}] tur {round_n}: +{rep.concepts_added} kavram, "
              f"+{new_h} yeni hipotez, merak={rep.curiosity_researched}, hedef={goals[-1] if goals else '-'}, "
              f"köprü={rep.bridges_discovered}, kanıt={rep.proofs_completed} "
              f"(toplam kavram {len(e.manifold.concepts)}, uptime {status['uptime_min']}dk)", flush=True)

        if round_n % COMMIT_EVERY == 0:
            _commit_growth(round_n, totals)
            print(f"[{time.strftime('%H:%M:%S')}] dayanıklılık commit'i (tur {round_n})", flush=True)

        time.sleep(2)

    print(f"[{time.strftime('%H:%M:%S')}] STOP dosyası bulundu — düzgün durduruldu (tur {round_n}).",
          flush=True)
    _commit_growth(round_n, totals)


if __name__ == "__main__":
    main()
