"""KATMAN 1 — koordinat birleştirme + RDKit karantina.

İki koordinat kodu (exact Fraction `universe_coordinate` ve float `compute_coord_91`)
iyi-koşullu girdide AYNI sonucu vermeli (eskiden float yol momentleri 16'ya sıfır-pad
edip near-degenerate Hankel'da pozitifliği YANLIŞ ölçüyordu — düzeltildi). Ayrıca tüm
DB depolama/sorgu yolları TEK koordinat tanımını (compute_coord_91) kullanmalı.
"""
import inspect

import numpy as np

from tantrium.core.mini_space import build_mini_space, compute_coord_91


def test_iki_koordinat_ayni():
    """İyi-koşullu girdide universe_coordinate ≈ compute_coord_91 (pozitiflik-pad bug'ı düzeldi)."""
    for nums in ([3.2, 1.8, 0.9, 0.4, 0.2, 0.1, 0.05], [5, 2.5, 1.25, 0.6, 0.3, 0.15]):
        ms = build_mini_space(nums)
        uc = ms.universe_coordinate()
        cc = compute_coord_91(ms.eigenvalues)[0]
        assert np.allclose(uc, cc, atol=1e-6), f"{nums}: maxd={np.abs(np.array(uc)-np.array(cc)).max():.2e}"


def test_koordinat_91_boyut():
    """Her iki yol da tam 91 boyut üretir."""
    nums = [3.2, 1.8, 0.9, 0.4, 0.2]
    assert len(compute_coord_91(nums)[0]) == 91
    assert len(build_mini_space(nums).universe_coordinate()) == 91


def test_depolama_yollari_tutarli(tmp_path):
    """Numbers-yolu (_compute_record) artık compute_coord_91 kullanır → query yolu ile birebir."""
    from tantrium.core.molecule_memory import MoleculeMemory

    nums = [3.2, 1.8, 0.9, 0.4, 0.2, 0.1, 0.05]
    mem = MoleculeMemory(str(tmp_path / "m.db"))
    rec = mem._compute_record(nums)
    coord_direct, _, mom_direct = compute_coord_91(nums)
    assert np.allclose(rec.coord_91, coord_direct)       # tek koordinat tanımı
    assert np.allclose(rec.moments_8, mom_direct)        # tek moment tanımı


def test_cekirdek_olcumde_rdkit_descriptor_yok():
    """smiles_to_numbers çekirdek ölçümünde RDKit descriptor enjeksiyonu yok (oku, çevirme)."""
    from tantrium.core.molecule_memory import smiles_to_numbers

    src = inspect.getsource(smiles_to_numbers)
    assert "rdMolDescriptors" not in src
    assert "CalcNum" not in src
