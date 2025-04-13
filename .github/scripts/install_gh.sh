#!/usr/bin/env bash

set -e

# Navigate to a temporary directory
cd "$(mktemp -d)"

# Set gh details
usage="Usage: $0 <gh-version>"
GH_VERSION=${1?$usage}
GH_TARBALL="https://github.com/cli/cli/releases/download/${GH_VERSION}/gh_${GH_VERSION#v}_linux_amd64.tar.gz"
GH_CHECKSUM="https://github.com/cli/cli/releases/download/${GH_VERSION}/gh_${GH_VERSION#v}_checksums.txt"
FILE_NAME=$(basename "${GH_TARBALL}")

# Download gh tarball, and checksum
curl -L --silent --fail "${GH_TARBALL}" -o "${FILE_NAME}"
curl -L --silent --fail "${GH_CHECKSUM}" | grep "${FILE_NAME}" > "${FILE_NAME}.sha"

# Verify checksum
sha256sum -c "${FILE_NAME}.sha"

# Extract gh binary from the tarball
tar -xzvf "${FILE_NAME}"

# Move to .local/bin
mkdir -p "$HOME/.local/bin"
mv "${FILE_NAME%.tar.gz}/bin/gh" "$HOME/.local/bin/gh"

# Add to PATH
echo "$HOME/.local/bin" >> "$GITHUB_PATH"
