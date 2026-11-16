#!/bin/bash
# Vercel build step (run by @vercel/static-build, see vercel.json).
# Produces staticfiles_build/, which Vercel serves from its CDN:
#   staticfiles_build/static/  -> /static/   (CSS, JS, images, videos)
#   staticfiles_build/media/   -> /media/    (branch, dish and news images, branch reels)
set -euo pipefail

SYS_PY="$(command -v python3.12 || command -v python3)"
echo "Using $($SYS_PY --version)"

# Vercel's build Python is "externally managed" (PEP 668), so install the
# packages into a throwaway virtualenv outside the project folder.
VENV="${TMPDIR:-/tmp}/mbuzimunch-build-venv"
$SYS_PY -m venv "$VENV"
PY="$VENV/bin/python"
[ -x "$PY" ] || PY="$VENV/Scripts/python.exe"   # Windows layout, for testing locally
$PY -m pip install --quiet --disable-pip-version-check -r requirements.txt

if [ -n "${DATABASE_URL:-}" ]; then
  echo "Applying database migrations and loading content..."
  $PY manage.py migrate --noinput
  $PY manage.py seed_site          # only adds what's missing; never touches bookings
else
  echo "WARNING: DATABASE_URL is not set. Add a Postgres database in Vercel (Storage tab)."
fi

$PY manage.py collectstatic --noinput --clear

mkdir -p staticfiles_build/media
cp -r media/. staticfiles_build/media/
rm -rf staticfiles_build/media/applications   # never publish uploaded CVs
echo "Build output ready."
