"""CLI yüzeyi (`tantrium` konsol komutu) — SDK ile aynı saf-matematik çıktıyı verir.

CLI yalnız ince bir kabuk: argümanları ayrıştırır, `tantrium.AI` çağırır, sonucu
yazdırır. Bu testler komutların çökmeden çalıştığını ve çıktının SDK ile tutarlı
olduğunu kilitler."""
import json

import pytest

from tantrium.cli import main


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "tantrium" in capsys.readouterr().out


def test_no_command_prints_help(capsys):
    code = main([])
    assert code == 1
    assert "tantrium" in capsys.readouterr().out


def test_compare_json_matches_sdk(capsys):
    import tantrium

    code = main(["compare", "CCO", "CCCO", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["distance"] == pytest.approx(tantrium.AI().compare("CCO", "CCCO"))


def test_fingerprint_json_is_46_dim(capsys):
    code = main(["fingerprint", "EGFR", "--json"])
    assert code == 0
    vec = json.loads(capsys.readouterr().out)
    assert isinstance(vec, list) and len(vec) >= 40


def test_discover_law_finds_golden_ratio(capsys):
    code = main(["discover-law", "1", "1", "2", "3", "5", "8", "13", "21"])
    assert code == 0
    out = capsys.readouterr().out
    assert "1.61803" in out  # altın oran φ


def test_status_runs(capsys):
    code = main(["status"])
    assert code == 0
    assert capsys.readouterr().out.strip()
