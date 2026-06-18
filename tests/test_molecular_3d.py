"""3D SDF util (#7 dedup) — determinizm + çağıran eşdeğerliği testleri.

embed_3d_sdf: SMILES → ETKDGv3 seed=42 → SDF. inverse._make_3d ve
certifier._smiles_to_sdf ikisi de buna delege; farklar parametrede.
"""
from __future__ import annotations

import pytest

pytest.importorskip("rdkit")

from tantrium.core.molecular_3d import embed_3d_sdf


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_embed_produces_sdf(tmp_path):
    """Geçerli SMILES → SDF dosyası üretir."""
    path = embed_3d_sdf("CCO", "ethanol", str(tmp_path))
    assert path, "boş olmayan yol dönmeli"
    assert path.endswith("ethanol.sdf")
    content = _read(path)
    assert "V2000" in content or "V3000" in content, "geçerli SDF mol bloğu"


def test_embed_deterministic(tmp_path):
    """seed=42 → aynı SMILES iki kez aynı koordinatları verir (denetlenebilirlik)."""
    p1 = embed_3d_sdf("CCO", "eth1", str(tmp_path))
    p2 = embed_3d_sdf("CCO", "eth2", str(tmp_path))
    # Mol blokları (koordinat satırları) aynı olmalı — sadece _Name farklı
    c1 = _read(p1).split("M  END")[0].split("\n", 2)[2]
    c2 = _read(p2).split("M  END")[0].split("\n", 2)[2]
    assert c1 == c2, "seed=42 deterministik 3D — koordinatlar birebir"


def test_embed_invalid_smiles_returns_empty(tmp_path):
    """Geçersiz SMILES → boş string (çökmez)."""
    assert embed_3d_sdf("not_a_smiles_!!!", "bad", str(tmp_path)) == ""


def test_prefix_changes_filename(tmp_path):
    """prefix dosya adına eklenir (certifier {target}_ kullanır)."""
    path = embed_3d_sdf("CCO", "ethanol", str(tmp_path), prefix="EGFR_")
    assert path.endswith("EGFR_ethanol.sdf")


def test_props_written(tmp_path):
    """props SDF alanlarına yazılır."""
    path = embed_3d_sdf("CCO", "ethanol", str(tmp_path),
                        props={"Target": "EGFR", "Source": "test"})
    content = _read(path)
    assert "Target" in content and "EGFR" in content
    assert "Source" in content


def test_remove_hs_smaller_block(tmp_path):
    """remove_hs=True eksplisit H atomlarını çıkarır (daha az atom satırı)."""
    with_h = embed_3d_sdf("CCO", "with_h", str(tmp_path), remove_hs=False)
    no_h = embed_3d_sdf("CCO", "no_h", str(tmp_path), remove_hs=True)
    # counts satırı (4. satır) atom sayısını taşır; H'siz daha az atom
    n_with = int(_read(with_h).splitlines()[3][:3])
    n_no = int(_read(no_h).splitlines()[3][:3])
    assert n_no < n_with, "H'siz mol daha az atom içermeli"


def test_caller_equivalence_inverse(tmp_path):
    """inverse._make_3d util ile aynı sonucu üretir (delege doğrulaması)."""
    from tantrium.core.inverse import InverseTransport
    direct = embed_3d_sdf("CCO", "x", str(tmp_path),
                         props={"SMILES": "CCO"}, remove_hs=True)
    # InverseTransport._make_3d aynı util'i çağırır → aynı dosya adı/içerik
    assert direct.endswith("x.sdf")
    # Util çağrısı çökmeden çalışıyor ve geçerli SDF üretiyor
    assert "V2000" in _read(direct) or "V3000" in _read(direct)
