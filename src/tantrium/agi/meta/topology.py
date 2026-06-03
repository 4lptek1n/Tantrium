"""Moment Uzayı Topolojisi — MomentTopology.

27k kavramın 8-boyutlu moment vektörleri bir manifold oluşturur.
Bu manifoldun haritasını çıkar: yoğun bölgeler, frontier'lar, void'ler.

Üç bölge türü:
  dense    — bilinen matematik (kavram yoğun)
  frontier — keşfedilebilir boşluk (komşuları sertifikalı → konveks hull PSD)
  void     — matematiksel imkansızlık (Aleph bu koordinatlarda tutmuyor)

"Bilmediğini bilmek":
  Frontier = yapısal bilinmeyen — isim verilmiş, keşfedilebilir
  Void      = yapısal imkansızlık — Hankel PSD'nin bu bölgeyi reddettiği alan
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine


@dataclass
class MathRegion:
    """Moment uzayının bir hücresi (grid bölgesi)."""

    region_id: str              # "R_{i}_{j}"
    center: list[float]         # bölge merkezinin moment koordinatları (μ₁, μ₂)
    concept_count: int          # bu hücredeki kavram sayısı
    concept_names: list[str]    # bu hücredeki / en yakın kavramlar
    density_class: str          # "dense" | "sparse" | "frontier" | "void"
    certifiable: bool           # konveks hull argümanıyla PSD türetilebilir mi?

    @property
    def is_unknown(self) -> bool:
        return self.concept_count == 0

    @property
    def named_unknown(self) -> str:
        """Boş bölgenin yapısal adı — sistematik gap ismi."""
        if not self.is_unknown:
            return ""
        tag = "FRONTIER" if self.certifiable else "VOID"
        c = ",".join(f"{v:.2f}" for v in self.center[:3])
        return f"MOMENT_{tag}[{c}]"


class MomentTopology:
    """Moment uzayının topolojik haritacısı.

    Manifold'daki 8-boyutlu moment noktalarını 2D grid'e projekte eder
    (μ₁ × μ₂). Her hücre için yoğunluk ve sertifikalanabilirlik hesaplar.

    Bu, sistemin kendi bilgi sınırlarının matematiksel haritasıdır.
    """

    def __init__(self, engine: "AGIEngine") -> None:
        self.engine = engine

    # ─── Ana analiz ───────────────────────────────────────────────────────────

    def analyze(self, grid_n: int = 12) -> list[MathRegion]:
        """Moment uzayını grid_n × grid_n hücreye böl.

        Projeksiyon: μ₁ (x-eksen) × μ₂ (y-eksen).
        Yoğunluk eşikleri: toplamın 2×ortalaması = dense, 0.3×ortalaması = sparse.
        """
        concepts = self.engine.manifold.concepts
        if not concepts:
            return []

        # μ₁ her zaman 1.0 (normalize edilmiş ölçü) → varyans yok.
        # Gerçek topoloji μ₂ × μ₃ (indeks 1 ve 2) üzerinde.
        _i1, _i2 = 1, 2
        vals1 = [float(c.moments[_i1]) for c in concepts.values() if len(c.moments) > _i2]
        vals2 = [float(c.moments[_i2]) for c in concepts.values() if len(c.moments) > _i2]
        if not vals1:
            return []

        min1, max1 = min(vals1), max(vals1)
        min2, max2 = min(vals2), max(vals2)
        step1 = max((max1 - min1) / grid_n, 1e-9)
        step2 = max((max2 - min2) / grid_n, 1e-9)

        grid: dict[tuple[int, int], list[str]] = {}
        for name, c in concepts.items():
            if len(c.moments) <= _i2:
                continue
            i = min(int((float(c.moments[_i1]) - min1) / step1), grid_n - 1)
            j = min(int((float(c.moments[_i2]) - min2) / step2), grid_n - 1)
            grid.setdefault((i, j), []).append(name)

        avg_density = len(concepts) / (grid_n * grid_n)
        dense_thr = avg_density * 2.0
        sparse_thr = avg_density * 0.3

        regions: list[MathRegion] = []
        for i in range(grid_n):
            for j in range(grid_n):
                cell = grid.get((i, j), [])
                count = len(cell)
                cx = min1 + (i + 0.5) * step1
                cy = min2 + (j + 0.5) * step2

                if count >= dense_thr:
                    density = "dense"
                elif count >= sparse_thr:
                    density = "sparse"
                elif count > 0:
                    density = "sparse"
                else:
                    # Boş hücre — komşu var mı?
                    has_neighbor = any(
                        (i + di, j + dj) in grid
                        for di in (-1, 0, 1)
                        for dj in (-1, 0, 1)
                        if (di, dj) != (0, 0)
                    )
                    density = "frontier" if has_neighbor else "void"

                # Komşu kavramlar
                nearby = list(cell[:4])
                if len(nearby) < 4:
                    for di in (-1, 0, 1):
                        for dj in (-1, 0, 1):
                            if (di, dj) == (0, 0):
                                continue
                            for n in grid.get((i + di, j + dj), [])[:2]:
                                if n not in nearby:
                                    nearby.append(n)
                            if len(nearby) >= 4:
                                break

                regions.append(MathRegion(
                    region_id=f"R_{i}_{j}",
                    center=[cx, cy],
                    concept_count=count,
                    concept_names=nearby[:4],
                    density_class=density,
                    certifiable=density in ("dense", "sparse", "frontier"),
                ))

        return regions

    # ─── Özel sorgular ────────────────────────────────────────────────────────

    def named_frontiers(self, top_n: int = 8) -> list[MathRegion]:
        """Keşfedilebilir boş bölgeler — en çok komşusu olanlar önce."""
        regions = self.analyze()
        frontiers = [r for r in regions if r.density_class == "frontier"]
        frontiers.sort(key=lambda r: len(r.concept_names), reverse=True)
        return frontiers[:top_n]

    def void_regions(self) -> list[MathRegion]:
        """Matematiksel imkansızlık bölgeleri — Aleph bu koordinatlarda tutmuyor."""
        return [r for r in self.analyze() if r.density_class == "void"]

    def densest_region(self) -> MathRegion | None:
        """En yoğun bölge — bilinen matematiğin kalbi."""
        regions = self.analyze()
        dense = [r for r in regions if r.density_class == "dense"]
        return max(dense, key=lambda r: r.concept_count) if dense else None

    # ─── Görselleştirme ───────────────────────────────────────────────────────

    def summary_map(self, grid_n: int = 20) -> str:
        """ASCII art moment uzayı haritası (μ₂ × μ₃ projeksiyonu).

        μ₁ = 1.0 her zaman (normalize ölçü) — topoloji μ₂ × μ₃ üzerinde.
        """
        concepts = self.engine.manifold.concepts
        if not concepts:
            return "(manifold boş)"

        _i1, _i2 = 1, 2
        vals1 = [float(c.moments[_i1]) for c in concepts.values() if len(c.moments) > _i2]
        vals2 = [float(c.moments[_i2]) for c in concepts.values() if len(c.moments) > _i2]
        if not vals1:
            return "(moment yok)"

        min1, max1 = min(vals1), max(vals1)
        min2, max2 = min(vals2), max(vals2)
        step1 = max((max1 - min1) / grid_n, 1e-9)
        step2 = max((max2 - min2) / grid_n, 1e-9)

        grid: dict[tuple[int, int], int] = {}
        for c in concepts.values():
            if len(c.moments) <= _i2:
                continue
            i = min(int((float(c.moments[_i1]) - min1) / step1), grid_n - 1)
            j = min(int((float(c.moments[_i2]) - min2) / step2), grid_n - 1)
            grid[(i, j)] = grid.get((i, j), 0) + 1

        max_count = max(grid.values()) if grid else 1

        def _char(n: int) -> str:
            if n == 0:
                return "·"
            r = n / max_count
            if r > 0.55:
                return "█"
            if r > 0.30:
                return "▓"
            if r > 0.10:
                return "▒"
            return "░"

        # frontier detection
        frontier_cells: set[tuple[int, int]] = set()
        for i in range(grid_n):
            for j in range(grid_n):
                if (i, j) not in grid:
                    for di, dj in ((-1,0),(1,0),(0,-1),(0,1)):
                        if (i+di, j+dj) in grid:
                            frontier_cells.add((i, j))
                            break

        void_count = sum(
            1 for i in range(grid_n) for j in range(grid_n)
            if (i, j) not in grid and (i, j) not in frontier_cells
        )

        lines = [
            f"  ══ MOMENT UZAYI HARİTASI ══  [{len(concepts):,} kavram]",
            f"  μ₂ ekseni: [{min1:.4f} → {max1:.4f}]  (yatay)",
            f"  μ₃ ekseni: [{min2:.4f} → {max2:.4f}]  (dikey)",
            f"  █ yoğun   ▓ orta   ▒░ seyrek   · boş (frontier/void)",
            "  ┌" + "─" * grid_n + "┐",
        ]

        for j in range(grid_n - 1, -1, -1):
            row = "  │"
            for i in range(grid_n):
                row += _char(grid.get((i, j), 0))
            row += "│"
            lines.append(row)

        lines.append("  └" + "─" * grid_n + "┘")
        lines.append(
            f"  Dolu: {len(grid)}  Frontier: {len(frontier_cells)}  "
            f"Void: {void_count}  Toplam hücre: {grid_n*grid_n}"
        )
        return "\n".join(lines)

    def gap_report(self) -> str:
        """Bilinmeyen bölgelerin yapısal adları ve keşif potansiyeli."""
        regions = self.analyze()
        by_class = {"dense": [], "sparse": [], "frontier": [], "void": []}
        for r in regions:
            by_class[r.density_class].append(r)

        lines = [
            "  ══ GAP ANALİZİ: Yapısal Bilinmeyenler ══",
            f"  Yoğun bölge:    {len(by_class['dense']):4}  — bilinen matematik",
            f"  Seyrek bölge:   {len(by_class['sparse']):4}  — keşfedilmiş ama ince",
            f"  Frontier:       {len(by_class['frontier']):4}  — keşfedilebilir boşluk",
            f"  Void:           {len(by_class['void']):4}  — matematiksel imkansızlık",
            "",
            "  İlk Frontier Bölgeleri (HankelGeneralizer ile doldurun):",
        ]
        for r in by_class["frontier"][:6]:
            nb = ", ".join(r.concept_names[:2]) if r.concept_names else "—"
            lines.append(f"    {r.named_unknown:<45}  yakın: {nb}")

        if by_class["void"]:
            lines.append(
                f"\n  {len(by_class['void'])} void bölge — Hankel PSD bu koordinatlarda sağlanamıyor."
            )
            lines.append(
                "  Bunlar matematiksel imkansızlık alanları — Aleph bu bölgeleri reddeder."
            )
        return "\n".join(lines)
