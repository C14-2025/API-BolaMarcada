#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?GITHUB_TOKEN ausente}"
: "${GITHUB_REPO:?GITHUB_REPO ausente (owner/repo)}"
: "${TAG:?TAG ausente}"
: "${ASSET_PATH:?ASSET_PATH ausente}"

if [ ! -f "$ASSET_PATH" ]; then
  echo "ERRO: asset não encontrado: $ASSET_PATH" >&2
  exit 2
fi

OWNER="${GITHUB_REPO%%/*}"
REPO="${GITHUB_REPO##*/}"
API="https://api.github.com"
UPLOADS="https://uploads.github.com"

auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "User-Agent: jenkins-ci")

echo "[gh] procurando release por tag: $TAG"
set +e
resp=$(curl -sS "${auth[@]}" "$API/repos/$OWNER/$REPO/releases/tags/$TAG")
set -e

if echo "$resp" | jq -e .id >/dev/null 2>&1; then
  RELEASE_ID=$(echo "$resp" | jq -r .id)
  echo "[gh] release existente id=$RELEASE_ID"
else
  echo "[gh] criando release nova"
  payload=$(jq -n --arg tag "$TAG" --arg name "$TAG" \
    '{ tag_name: $tag, name: $name, draft: false, prerelease: false }')
  resp=$(curl -sS "${auth[@]}" -X POST "$API/repos/$OWNER/$REPO/releases" -d "$payload")
  if ! echo "$resp" | jq -e .id >/dev/null 2>&1; then
    echo "ERRO ao criar release: $resp" >&2
    exit 3
  fi
  RELEASE_ID=$(echo "$resp" | jq -r .id)
  echo "[gh] release criada id=$RELEASE_ID"
fi

# Apaga asset com mesmo nome se já existir
asset_name="$(basename "$ASSET_PATH")"
assets=$(curl -sS "${auth[@]}" "$API/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets")
asset_id=$(echo "$assets" | jq -r --arg n "$asset_name" '.[] | select(.name==$n) | .id' | head -n1)
if [ -n "${asset_id:-}" ] && [ "$asset_id" != "null" ]; then
  echo "[gh] removendo asset existente id=$asset_id ($asset_name)"
  curl -sS "${auth[@]}" -X DELETE "$API/repos/$OWNER/$REPO/releases/assets/$asset_id" >/dev/null
fi

echo "[gh] enviando asset: $asset_name"
upload_url="$UPLOADS/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=$(printf '%s' "$asset_name" | jq -sRr @uri)"
curl -sS -X POST "${auth[@]}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @"$ASSET_PATH" \
  "$upload_url" >/dev/null

echo "[gh] ok: release=$TAG asset=$asset_name"
