#!/usr/bin/env python3
"""Build Research OS v2 certificates."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.certificates import build_research_os_certificates


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium certificate builder v2")
    parser.add_argument("--campaign", default="subresultant_recurrence")
    args = parser.parse_args()
    result = build_research_os_certificates(args.campaign)
    subprocess.run(
        [sys.executable, "tools/tantrium_artifact_manifest.py", "--command-used", f"python tools/tantrium_certificate_builder_v2.py --campaign {args.campaign}"],
        cwd=REPO_ROOT,
        check=False,
    )
    print("TANTRIUM CERTIFICATE BUILDER V2")
    print(f"CAMPAIGN: {args.campaign}")
    print(f"CERTIFICATES: {result['certificate_count']}")
    print("RESULT: CERTIFICATES_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
