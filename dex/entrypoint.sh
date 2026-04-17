#!/bin/sh
# Entrypoint for Dex on Railway.
#
# Dex's built-in DEX_EXPAND_ENV feature has been unreliable on Railway,
# so we do the env var substitution here via sed before starting Dex.

set -e

TEMPLATE=/etc/dex/config.template.yaml
CONFIG=/tmp/dex-config.yaml

sed \
  -e "s|\${DEX_ISSUER}|${DEX_ISSUER:-http://localhost:5556/dex}|g" \
  -e "s|\${DEX_REDIRECT_URI}|${DEX_REDIRECT_URI:-http://localhost:5173/auth/callback}|g" \
  -e "s|\${PORT}|${PORT:-5556}|g" \
  "$TEMPLATE" > "$CONFIG"

exec dex serve "$CONFIG"
