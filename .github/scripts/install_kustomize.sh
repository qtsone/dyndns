#!/usr/bin/env bash

set -e

# Navigate to a temporary directory
cd "$(mktemp -d)"

# Set kustomize details
usage="Usage: $0 <kustomize-version>"
KUSTOMIZE_VERSION=${1?$usage}
KUSTOMIZE_TARBALL="https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz"
KUSTOMIZE_CHECKSUM="https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/${KUSTOMIZE_VERSION}/checksums.txt"
FILE_NAME=$(basename "${KUSTOMIZE_TARBALL}")

# Download kustomize tarball, and checksum
curl -L --silent --fail "${KUSTOMIZE_TARBALL}" -o "${FILE_NAME}"
curl -L --silent --fail "${KUSTOMIZE_CHECKSUM}" | grep "${FILE_NAME}" > "${FILE_NAME}.sha"

# Verify checksum
sha256sum -c "${FILE_NAME}.sha"

# Extract kustomize binary from the tarball
tar -xzvf "${FILE_NAME}"

# Move to .local/bin
mkdir -p "$HOME/.local/bin"
mv kustomize "$HOME/.local/bin/kustomize"

# Add to PATH
echo "$HOME/.local/bin" >> "$GITHUB_PATH"
