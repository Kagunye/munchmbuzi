#!/bin/bash
# Vercel build step (run by @vercel/static-build, see vercel.json).
# Produces staticfiles_build/, which Vercel serves from its CDN:
#   staticfiles_build/static/  -> /static/   (CSS, JS, images, videos)
#   staticfiles_build/media/   -> /media/    (branch, dish and news images, branch reels)
set -euo pipefail

PY="$(command -v python3.12 || command -v python3)"
echo "Using $($PY --version)"
$PY -m pip install --disable-pip-version-check -r requirements.txt

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
