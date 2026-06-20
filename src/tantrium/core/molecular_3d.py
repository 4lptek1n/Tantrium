"""3D konformasyon üretimi — TEK kanonik SDF util (gerçek tekrar #7).

`inverse._make_3d` ve `certifier._smiles_to_sdf` ikisi de SMILES → RDKit
ETKDGv3 (randomSeed=42) + MMFF94 → SDF yapıyordu. Çekirdek aynı; farklar
parametrelerde (dosya öneki, ekstra SDF alanları, H atomu temizleme).

Determinizm: randomSeed=42 HER ZAMAN (ETKDGv3 ve fallback ETKDG) — aynı SMILES
aynı 3D konformeri verir. Bu, üretim sertifikasının denetlenebilirliği için kritik.
"""

from __future__ import annotations

import pathlib


def embed_3d_sdf(
    smiles: str,
    name: str,
    out_dir: str,
    *,
    prefix: str = "",
    props: dict[str, str] | None = None,
    remove_hs: bool = False,
    enforce_chirality: bool = True,
) -> str:
    """SMILES → 3D SDF (ETKDGv3 seed=42 + MMFF94). Başarısızlıkta boş string.

    prefix          : dosya adı öneki ("EGFR_" gibi); yoksa düz güvenli-ad.sdf
    props           : ekstra SDF alanları (SMILES/Target/Source ...)
    remove_hs       : embed sonrası eksplisit H'leri çıkar (görsel sadelik)
    enforce_chirality: ETKDGv3 kiralite zorlaması (varsayılan True)
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""

        mol = Chem.AddHs(mol)
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        params.enforceChirality = enforce_chirality
        if AllChem.EmbedMolecule(mol, params) == -1:
            # Fallback: klasik ETKDG (yine deterministik seed=42)
            fallback = AllChem.ETKDG()
            fallback.randomSeed = 42
            AllChem.EmbedMolecule(mol, fallback)

        AllChem.MMFFOptimizeMolecule(mol)
        if remove_hs:
            mol = Chem.RemoveHs(mol)

        out = pathlib.Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40]
        path = out / f"{prefix}{safe_name}.sdf"

        mol.SetProp("_Name", name[:64])
        for k, v in (props or {}).items():
            mol.SetProp(k, v)

        writer = Chem.SDWriter(str(path))
        writer.write(mol)
        writer.close()
        return str(path)
    except Exception:
        return ""
