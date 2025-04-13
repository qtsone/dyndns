#!/usr/bin/env bash

set -e

# Navigate to a temporary directory
cd "$(mktemp -d)"

# Set yq details
usage="Usage: $0 <yq-version>"
YQ_VERSION=${1?$usage}
YQ_BINARY="yq_linux_amd64"
YQ_TARBALL="https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/${YQ_BINARY}.tar.gz"
YQ_CHECKSUM="https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/checksums"
YQ_CHECKSUM_EXTRACT="https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/extract-checksum.sh"
YQ_CHECKSUM_HASHES="https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/checksums_hashes_order"
FILE_NAME=$(basename "${YQ_TARBALL}")

# Download yq tarball, checksum, extract script, hashes order
curl -L --silent --fail "${YQ_TARBALL}" -o "${FILE_NAME}"
curl -L --silent --fail "${YQ_CHECKSUM}" -o checksums
curl -L --silent --fail "${YQ_CHECKSUM_EXTRACT}" -o extract-checksum.sh
curl -L --silent --fail "${YQ_CHECKSUM_HASHES}" -o checksums_hashes_order

# Verify checksum and extract
sh ./extract-checksum.sh SHA-256 "${FILE_NAME}" | awk '{ print $2 " " $1}' > "${FILE_NAME}.sha"
sha256sum -c "${FILE_NAME}.sha"

# Extract yq binary from the tarball
tar -xzvf "${FILE_NAME}"

# Move to .local/bin
mkdir -p "$HOME/.local/bin"
mv ${YQ_BINARY} "$HOME/.local/bin/yq"

# Add to PATH
echo "$HOME/.local/bin" >> "$GITHUB_PATH"