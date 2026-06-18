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

COMMIT_EVERY = 0          # 0 = runner git-commit KAPALI (kod-branch hijyeni; disk-persist resumable)
COGNITION_EVERY = 5       # her 5 turda bir akıl/self/dedup (pahalı, N ile büyür → seyrek tut)
CYCLES_PER_ROUND = 1      # cognition turunda batch döngü sayısı
ROUND_BUDGET_S = 600      # tur başına süre tavanı (sonsuz döngü, tur sınırlı)
FOCUS = None              # GENİŞ büyüme: tüm 10 kaynak (kimya+biyoloji+matematik+genel bilgi).
                          # ÖLÇÜLDÜ: focus=None ~5 kavram/sn akar; onkoloji-odağı kaynakları
                          # kurutup tur başına ~2 kavrama düşürüyordu. "Herşeyi anla" = genişlik.
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
        cog_round = (round_n % COGNITION_EVERY == 0)   # pahalı akıl/self yalnız periyodik
        # FAZ 1 — GENİŞ VERİ (her tur): tüm kaynaklardan akış + 8-boyut enrichment +
        # corrigibility temizlik. Throughput önce: cognition turunda biraz pay bırak.
        grow_added = 0
        grow_budget = ROUND_BUDGET_S * (0.7 if cog_round else 1.0)
        try:
            grp = ai.grow(focus=FOCUS, time_limit_s=grow_budget,
                          network=True, verbose=False)
            grow_added = int(getattr(grp, "concepts_end", 0) - getattr(grp, "concepts_start", 0))
        except Exception as exc:
            print(f"[{time.strftime('%H:%M:%S')}] tur {round_n} grow hata: {exc} — devam", flush=True)

        # FAZ 2 — AĞSIZ AKIL/SELF (her COGNITION_EVERY turda): reasoning/self/hipotez/dedup.
        # N ile pahalılaşır → seyrek; throughput'u boğmaz. Diğer turlarda boş rapor.
        rep = None
        if cog_round:
            try:
                rep = ai.cognition(mode="batch", max_cycles=CYCLES_PER_ROUND,
                                   time_limit_s=ROUND_BUDGET_S * 0.3, network=False)
            except Exception as exc:  # fail-open: bir tur çökse de SONSUZ döngü durmaz
                print(f"[{time.strftime('%H:%M:%S')}] tur {round_n} cognition hata: {exc} — devam",
                      flush=True)

        totals["concepts"] += grow_added
        if rep is not None:
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
        # büyümeyi her tur DİSKE yaz (ephemeral konteyner içinde resumable)
        try:
            e.auto_persist()
        except Exception:
            pass

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
            "last_narration": (rep.narrations[-1][:240] if (rep and rep.narrations) else ""),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        cog_str = (f"akıl: +{rep.concepts_added} kavram, +{new_h} hipotez, "
                   f"köprü={rep.bridges_discovered}, kanıt={rep.proofs_completed}"
                   if rep is not None else "akıl: — (ingestion turu)")
        print(f"[{time.strftime('%H:%M:%S')}] tur {round_n}: +{grow_added} veri-kavram, {cog_str}, "
              f"hedef={goals[-1] if goals else '-'} "
              f"(toplam kavram {len(e.manifold.concepts)}, uptime {status['uptime_min']}dk, "
              f"tur {status['round_s']}s)", flush=True)

        if COMMIT_EVERY and round_n % COMMIT_EVERY == 0:
            _commit_growth(round_n, totals)
            print(f"[{time.strftime('%H:%M:%S')}] dayanıklılık commit'i (tur {round_n})", flush=True)

        time.sleep(2)

    print(f"[{time.strftime('%H:%M:%S')}] STOP dosyası bulundu — düzgün durduruldu (tur {round_n}).",
          flush=True)
    try:
        e.auto_persist()
    except Exception:
        pass
    if COMMIT_EVERY:
        _commit_growth(round_n, totals)


if __name__ == "__main__":
    main()
