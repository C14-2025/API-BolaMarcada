#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?Defina GITHUB_TOKEN}"
: "${GITHUB_REPO:?Ex: C14-2025/API-BolaMarcada}"
: "${TAG:?Ex: ci-<commit>}"
: "${ASSET_PATH:?Caminho do arquivo .tar}"

API="https://api.github.com"

# Verifica se já existe release para a TAG
set +e
release_resp=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" \
  "${API}/repos/${GITHUB_REPO}/releases/tags/${TAG}")
exists_code=$?
set -e

if echo "$release_resp" | jq -e '.id' >/dev/null 2>&1; then
  release_id=$(echo "$release_resp" | jq -r '.id')
else
  # Cria release (prerelease)
  release_id=$(curl -sS -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
    -d "{\"tag_name\":\"${TAG}\",\"name\":\"${TAG}\",\"draft\":false,\"prerelease\":true}" \
    "${API}/repos/${GITHUB_REPO}/releases" | jq -r '.id')
fi

upload_url=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" \
  "${API}/repos/${GITHUB_REPO}/releases/${release_id}" | jq -r '.upload_url' | sed 's/{?name,label}//')

fname=$(basename "${ASSET_PATH}")

# Remove asset existente com mesmo nome (idempotência)
assets=$(curl -sS -H "Authorization: token ${GITHUB_TOKEN}" \
  "${API}/repos/${GITHUB_REPO}/releases/${release_id}/assets")
asset_id=$(echo "$assets" | jq -r ".[] | select(.name==\"${fname}\") | .id")
if [ -n "${asset_id:-}" ] && [ "$asset_id" != "null" ]; then
  curl -sS -X DELETE -H "Authorization: token ${GITHUB_TOKEN}" \
    "${API}/repos/${GITHUB_REPO}/releases/assets/${asset_id}" >/dev/null
fi

# Upload
curl -sS -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @"${ASSET_PATH}" \
  "${upload_url}?name=${fname}" >/dev/null

echo "Asset enviado: ${fname} para release ${TAG}"
