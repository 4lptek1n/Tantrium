"""Tantrium komut satırı arayüzü (CLI) — saf-matematik yüzeyini terminalden çalıştır.

Kullanım:
  tantrium fingerprint EGFR                 # 46-boyutlu sertifika parmak izi
  tantrium compare CCO CCCO                 # iki girdi arası 46-dim mesafe
  tantrium transport CCO "CC(=O)O"          # sertifikalı dyadic+Sturm+Zeta geçiş
  tantrium discover-law 1 1 2 3 5 8 13 21   # ham veriden yönetici yasa (→ φ)
  tantrium reconstruct EGFR                 # momentlerden ölçü geri-çıkarımı
  tantrium certify EGFR                     # tam 4-eksenli birleşik sertifika + mühür
  tantrium rh aspirin                       # tam RH sertifikası (özet)
  tantrium rh-distance CCO CCCO             # RH-sertifika mesafesi
  tantrium ask "EGFR nedir?"                # paradigma sertifikası + cevap
  tantrium status                           # makine durumu

Her komut `--json` ile makine-okunur çıktı verebilir. Dil yok, öğrenme yok,
istatistik yok — yalnız spektral moment → sertifika.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import tantrium


def _emit(result: Any, as_json: bool) -> None:
    """Bir result nesnesini insan-okunur (summary) veya JSON olarak yazdır."""
    if as_json:
        print(json.dumps(_jsonable(result), ensure_ascii=False, default=str, indent=2))
        return
    summary = getattr(result, "summary", None)
    if callable(summary):
        print(summary())
    else:
        print(result)


def _jsonable(result: Any) -> Any:
    """Result'u JSON-serileştirilebilir bir yapıya indirge (best-effort)."""
    if isinstance(result, (str, int, float, bool)) or result is None:
        return result
    if isinstance(result, (list, tuple)):
        return [_jsonable(x) for x in result]
    if isinstance(result, dict):
        return {str(k): _jsonable(v) for k, v in result.items()}
    asdict = getattr(result, "_asdict", None)  # namedtuple
    if callable(asdict):
        return _jsonable(asdict())
    data = getattr(result, "__dict__", None)
    if data:
        return {k: _jsonable(v) for k, v in data.items() if not k.startswith("_")}
    return str(result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tantrium",
        description="Tantrium — durumsuz saf-matematik yapısal ölçüm makinesi.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--version", action="version", version=f"tantrium {tantrium.__version__}"
        if hasattr(tantrium, "__version__") else "tantrium",
    )
    sub = parser.add_subparsers(dest="command", metavar="<komut>")

    def _add(name: str, help_: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_)
        p.add_argument("--json", action="store_true", help="JSON çıktı")
        return p

    p = _add("fingerprint", "46-boyutlu sertifika parmak izi")
    p.add_argument("query")

    p = _add("compare", "iki girdi arası 46-dim sertifika mesafesi")
    p.add_argument("a")
    p.add_argument("b")

    p = _add("transport", "sertifikalı dyadic+Sturm+Zeta geçiş")
    p.add_argument("source")
    p.add_argument("target")
    p.add_argument("--smiles", action="store_true", help="girdileri SMILES olarak yorumla")

    p = _add("discover-law", "ham sayı dizisinden yönetici yasa keşfi")
    p.add_argument("numbers", nargs="+", type=float, help="gözlem dizisi")
    p.add_argument("--name", default="veri", help="dizi adı (etiket)")

    p = _add("reconstruct", "momentlerden ölçü geri-çıkarımı")
    p.add_argument("query")
    p.add_argument("--max-atoms", type=int, default=4, help="kuadratür atom sayısı")

    p = _add("certify", "tam 4-eksenli birleşik sertifika + SHA-256 mühür")
    p.add_argument("query")

    p = _add("rh", "tam Riemann-Hipotezi sertifikası")
    p.add_argument("query")

    p = _add("rh-distance", "iki nesne arası RH-sertifika mesafesi")
    p.add_argument("a")
    p.add_argument("b")

    p = _add("ask", "paradigma sertifikası + yapısal cevap")
    p.add_argument("query")

    _add("status", "makine durumu özeti")

    return parser


def _run(args: argparse.Namespace) -> int:
    ai = tantrium.AI()
    cmd = args.command
    as_json = getattr(args, "json", False)

    if cmd == "fingerprint":
        vec = ai.fingerprint(args.query)
        if as_json:
            print(json.dumps(vec))
        else:
            print(f"{args.query} → 46-dim parmak izi:")
            print("  [" + ", ".join(f"{x:.6g}" for x in vec) + "]")
    elif cmd == "compare":
        dist = ai.compare(args.a, args.b)
        print(json.dumps({"a": args.a, "b": args.b, "distance": dist}) if as_json
              else f"mesafe({args.a}, {args.b}) = {dist:.12g}")
    elif cmd == "transport":
        _emit(ai.transport(args.source, args.target, use_smiles=args.smiles), as_json)
    elif cmd == "discover-law":
        _emit(ai.discover_law(args.numbers, name=args.name), as_json)
    elif cmd == "reconstruct":
        _emit(ai.reconstruct(args.query, max_atoms=args.max_atoms), as_json)
    elif cmd == "certify":
        _emit(ai.certify_all(args.query), as_json)
    elif cmd == "rh":
        _emit(ai.rh_certificate(args.query), as_json)
    elif cmd == "rh-distance":
        dist = ai.rh_distance(args.a, args.b)
        print(json.dumps({"a": args.a, "b": args.b, "rh_distance": dist}) if as_json
              else f"rh_mesafe({args.a}, {args.b}) = {dist:.12g}")
    elif cmd == "ask":
        _emit(ai.ask(args.query), as_json)
    elif cmd == "status":
        print(ai.status())
    else:  # pragma: no cover — argparse zaten yakalar
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI giriş noktası (`tantrium` konsol komutu)."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    try:
        return _run(args)
    except KeyboardInterrupt:  # pragma: no cover
        print("kesildi", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
