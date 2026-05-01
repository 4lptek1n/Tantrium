# Platform Compatibility

## Tested Platform

```text
Windows local
Python 3.14.2
SymPy 1.14.0
```

The Windows run exposed two real issues that are now part of the compatibility
policy:

```text
python3 launcher mismatch on Windows
cp1252 encoding failure on non-ASCII certificate text
```

## Policy

```text
Python subprocesses must use sys.executable.
All text file writes must use encoding="utf-8".
JSON output should use indent=2 and sort_keys=True where stable ordering helps.
Path handling should use pathlib.
Python tools should avoid shell-only assumptions.
```

## Linux/Replit

Linux and Replit runs should use:

```bash
python tools/tantrium_rh_machine.py --full
python tools/independent_verifier.py
```

## Windows

Windows PowerShell runs should use:

```powershell
python tools\tantrium_rh_machine.py --full
python tools\independent_verifier.py
```

## GitHub Auth / Push

Do not paste GitHub tokens into chat. Authenticate locally:

```powershell
gh auth login -h github.com --with-token
```

Push remains blocked until the active GitHub account has write access to the
repository.
