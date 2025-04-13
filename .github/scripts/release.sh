#!/usr/bin/env bash

set -e

: "${SERVER_URL:?SERVER_URL must be set}"
: "${REPOSITORY:?REPOSITORY must be set}"
: "${ACTOR:?ACTOR must be set}"
: "${OWNER:?OWNER must be set}"
: "${GH_TOKEN:?GH_TOKEN must be set}"
: "${CHART_PATH:?CHART_PATH must be set}"
: "${VERSION:?VERSION must be set}"

colorize() {
  export BLACK="\033[30m"
  export RED="\033[31m"
  export GREEN="\033[92m"
  export YELLOW="\033[33m"
  export BLUE="\033[34m"
  export MAGENTA="\033[35m"
  export CYAN="\033[36m"
  export WHITE="\033[37m"
  export VIVID="\033[95m"
  export RST="\033[0m"
}

log_info() {
  echo -e "${GREEN}[INFO]: $1${RST}"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]: $1${RST}" 1>&2
}

log_error() {
  echo -e "${RED}[ERROR]: $1${RST}" 1>&2
}

log_fatal() {
  echo -e "${RED}[FATAL]: $1${RST}" >&2
  exit 1
}

package_and_upload() {
  local _path="$1"
  local _name="$2"
  local _version="$3"

  pkg_path="/tmp/.cr-release-packages"
  mkdir -p "$pkg_path"

  log_info "Logging in to 'ghcr.io' ..."
  echo "$GH_TOKEN" | docker login ghcr.io --username="${ACTOR}" --password-stdin

  git fetch --all
  log_info "[$_path] [$_version] Updating Chart.yaml version..."
  yq -i ".version = \"$_version\"" "$_path/Chart.yaml"
  
  log_info "[$_path] [$_version] Packaging..."
  helm package --dependency-update --destination "$pkg_path" "$_path"

  log_info "[$_path] [$_version] Publishing..."
  helm push "${pkg_path}/${_name}-${_version}.tgz" "oci://ghcr.io/${OWNER}/${REPOSITORY}"

  # Cleanup
  rm -rf "$pkg_path"

  sleep 3
}

colorize
log_info "Processing chart..."
log_info "Chart: $REPOSITORY"
log_info "Version: $VERSION"
package_and_upload "$CHART_PATH" "$REPOSITORY" "$VERSION"
