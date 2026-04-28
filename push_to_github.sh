#!/usr/bin/env bash
# Standalone math repo'yu hazırlayıp GitHub'a push etme yardımcısı.
#
# Kullanım (Replit Shell'de):
#   bash push_to_github.sh init          # /tmp/math-export'u git repo yap & commit at
#   bash push_to_github.sh push REMOTE   # önceden eklediğin remote'a push (örn: origin)
#
# GitHub'a auth için:
#   - PAROLA KABUL EDİLMİYOR (GitHub 2021'de kapattı).
#   - Bir Personal Access Token (PAT) kullanmalısın:
#       https://github.com/settings/tokens?type=beta
#       Scope: "repo" (private için) veya "public_repo" (public için)
#   - Veya en kolayı: Replit workspace'inde sol panelden "Version Control"
#     → "Connect to GitHub" UI'sini kullan (OAuth otomatik halleder).

set -euo pipefail

EXPORT_DIR="/tmp/math-export"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)/math"

case "${1:-}" in
  init)
    if [ ! -d "$SRC_DIR" ]; then
      echo "ERROR: math/ source not found at $SRC_DIR"; exit 1
    fi
    rm -rf "$EXPORT_DIR"
    mkdir -p "$EXPORT_DIR"
    cp -r "$SRC_DIR"/. "$EXPORT_DIR"/
    rm -rf "$EXPORT_DIR/__pycache__"
    cd "$EXPORT_DIR"
    git init -b main
    git add .
    git -c user.email="${GIT_EMAIL:-you@example.com}" \
        -c user.name="${GIT_NAME:-Researcher}" \
        commit -m "Initial: P_lambda_d hyperbolicity symbolic investigation

- Ramp formula a_{T_j}(n) = 2^{T_j} prod_{m=1}^j (n+m)^m verified for j in {1..5}, d in {2..22}
- Schur-positivity verified for all coefficients
- Lah polynomial connection (leading-lambda shadow)
- Subresultant cross-ratio: rho_{d,j}(t) = C * t^k * H_{j-2}*H_j / H_{j-1}^2
- lambda^{-2} perturbation expansion (Gate A) - structural theorem verified"
    echo
    echo "OK: Repo hazır -> $EXPORT_DIR"
    echo "Şimdi GitHub'da yeni bir repo oluştur, sonra:"
    echo "  cd $EXPORT_DIR"
    echo "  git remote add origin https://github.com/USERNAME/REPO.git"
    echo "  bash $(realpath "$0") push origin"
    ;;
  push)
    REMOTE="${2:-origin}"
    cd "$EXPORT_DIR"
    if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
      echo "ERROR: '$REMOTE' remote yok. Önce git remote add $REMOTE <URL> ekle."; exit 1
    fi
    echo "Pushing to $REMOTE main..."
    echo "(Şifre soracak: GitHub username + PAT gir, normal şifreni DEĞİL.)"
    git push -u "$REMOTE" main
    ;;
  *)
    echo "Kullanım: bash $0 init|push [remote]"
    echo
    echo "Örnek tam akış:"
    echo "  bash $0 init"
    echo "  cd $EXPORT_DIR"
    echo "  git remote add origin https://github.com/USERNAME/REPO.git"
    echo "  bash $0 push origin"
    exit 1
    ;;
esac
