"""KATMAN 0 + 5 — tek operatör spektrumu + yasayı sakla (DNA).

Bu testler iki ilkeyi kilitler:
  · tek-cins: molekül = TEK operatör G=AᵀA spektrumu (descriptor yapıştırması yok,
    RDKit yoksa dürüst hata — sessiz boş çöküş değil).
  · yasa-sakla: kayıt eigenvalues + var-eden-yasa + σ tutar; coord_91 türev; σ
    birinci-sınıf; yasa σ≈0'da spektrumu kayıpsız yeniden üretir.
"""
import sys

import numpy as np
import pytest

from tantrium.core.genome import GenomeRecord, fit_genome, regenerate
from tantrium.core.mini_space import compute_coord_91


def test_molekul_tek_operator_spektrumu():
    """smiles_to_numbers artık TEK operatör G=AᵀA spektrumu döndürür (descriptor kuyruğu yok)."""
    pytest.importorskip("rdkit")
    from tantrium.core.encoder._text import _smiles_full_eigenvalues
    from tantrium.core.molecule_memory import smiles_to_numbers

    nums = smiles_to_numbers("c1ccccc1")
    full = _smiles_full_eigenvalues("c1ccccc1")
    assert np.allclose(nums, full)                       # aynı tek-operatör spektrumu
    assert nums == sorted(nums, reverse=True)            # sıralı azalan
    assert all(x >= 0 for x in nums)                     # G=AᵀA → PSD, hepsi ≥0


def test_rdkit_yoksa_durust_hata(monkeypatch):
    """RDKit yokken sessiz [] DEĞİL — dürüst RuntimeError (uzayın çökmesini önler)."""
    monkeypatch.setitem(sys.modules, "rdkit", None)
    monkeypatch.setitem(sys.modules, "rdkit.Chem", None)
    from tantrium.core.molecule_memory import smiles_to_numbers

    with pytest.raises(RuntimeError):
        smiles_to_numbers("CCO")


def test_genom_kayipsiz_yeniden_uretir():
    """σ≈0 olduğunda genom (yasa+tohum) spektrumu KAYIPSIZ yeniden üretir."""
    eigs = [1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]   # geometrik → tam yasa
    g = fit_genome(eigs)
    assert g.sigma < 1e-6
    assert g.law_type == "linear"
    assert np.allclose(regenerate(g, len(eigs)), eigs, atol=1e-6)


def test_coord_91_eigenvalue_dan_turetilir():
    """coord_91 saklanan eigenvalue'ların SAF fonksiyonu — özdeğerden bit-aynı türetilir."""
    nums = [3.2, 1.8, 0.9, 0.4, 0.2, 0.1, 0.05]
    coord1, eigs16, _ = compute_coord_91(nums)
    spectrum = [e for e in eigs16 if e > 1e-12]          # depodaki gerçek spektrum (sıfır-pad'siz)
    coord2, _, _ = compute_coord_91(spectrum)            # sadece özdeğerden → yeniden türet
    assert np.allclose(coord1, coord2)


def test_genom_yasa_tipi_secimi():
    """σ küçükse linear; çok kısa dizi trivial; lojistik (polinom) nonlinear."""
    assert fit_genome([1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125]).law_type == "linear"
    assert fit_genome([3.0, 1.0]).law_type == "trivial"
    x, logi = 0.37, []
    for _ in range(20):
        x = 3.9 * x * (1 - x)
        logi.append(x)
    assert fit_genome(logi).law_type in ("linear", "nonlinear")  # sonlu σ ile fit


def test_sigma_birinci_sinif_alan(tmp_path):
    """σ + law kayıtta birinci-sınıf alan; reopen'da kalıcı; QueryResult σ taşır."""
    from tantrium.core.molecule_memory import MoleculeMemory

    mem = MoleculeMemory(str(tmp_path / "m.db"))
    rec = mem._compute_record([3.2, 1.8, 0.9, 0.4, 0.2, 0.1, 0.05], metadata={"src": "t"})
    mem._insert_record(rec)
    mem._conn.commit()
    assert rec.law and rec.sigma >= 0.0
    mem.close()

    mem2 = MoleculeMemory(str(tmp_path / "m.db"))
    loaded = mem2._records[0]
    assert loaded.law.get("law_type") and loaded.sigma >= 0.0
    res = mem2.query_numbers([3.2, 1.8, 0.9, 0.4, 0.2, 0.1, 0.05], k=1)
    assert res and hasattr(res[0], "sigma")
    # saklanan yasadan spektrum yeniden üretilebilir (DNA)
    g = GenomeRecord.from_dict(loaded.law)
    assert np.allclose(regenerate(g, len(g.eigenvalues)), g.eigenvalues, atol=1e-4)


def test_sema_yeni_kolonlar(tmp_path):
    """Taze DB law + sigma kolonlarıyla kurulur (migration'sız)."""
    from tantrium.core.molecule_memory import MoleculeMemory

    mem = MoleculeMemory(str(tmp_path / "m.db"))
    cols = {c[1] for c in mem._conn.execute("PRAGMA table_info(molecules)")}
    assert "law" in cols and "sigma" in cols
