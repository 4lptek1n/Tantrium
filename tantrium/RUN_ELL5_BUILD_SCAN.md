# Run ELL5 Build and Auto Scan

This file triggers the self-running GitHub Actions workflow:

```bash
python -u tools/build_kernel.py --ell 5
python -u tools/tantrium.py certify --scan all --max-ell 5 --model auto
```

Triggered from ChatGPT connector so the user does not need a PC or terminal.
