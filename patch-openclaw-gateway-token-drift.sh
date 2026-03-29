#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: patch-openclaw-gateway-token-drift.sh [--check]

Patches the installed OpenClaw CLI bundle so gateway token drift checks can
resolve env-backed SecretRefs without emitting a false warning.

Options:
  --check   Verify whether the patch is already present without modifying files
  -h        Show this help
EOF
}

MODE="apply"
if [[ "${1:-}" == "--check" ]]; then
  MODE="check"
elif [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
elif [[ $# -gt 0 ]]; then
  echo "Unknown argument: $1" >&2
  usage >&2
  exit 2
fi

OPENCLAW_BIN="${OPENCLAW_BIN:-$(command -v openclaw || true)}"
if [[ -z "$OPENCLAW_BIN" ]]; then
  echo "openclaw binary not found in PATH. Set OPENCLAW_BIN and retry." >&2
  exit 1
fi

resolve_path() {
  perl -MCwd=abs_path -e 'my $p = shift; my $r = abs_path($p); die "resolve failed\n" unless defined $r; print $r;' "$1"
}

OPENCLAW_REAL="$(resolve_path "$OPENCLAW_BIN")"
MODULE_DIR="$(cd "$(dirname "$OPENCLAW_REAL")" && pwd)"
DIST_DIR="$MODULE_DIR/dist"

LIFECYCLE_FILES=()
while IFS= read -r file; do
  LIFECYCLE_FILES+=("$file")
done < <(find "$DIST_DIR" -maxdepth 1 -type f -name 'lifecycle-core-*.js' | sort)

AUTH_PROFILE_FILES=()
while IFS= read -r file; do
  AUTH_PROFILE_FILES+=("$file")
done < <(find "$DIST_DIR" -maxdepth 1 -type f -name 'auth-profiles-*.js' | sort)

FILES=("$DIST_DIR/daemon-cli.js")
FILES+=("${LIFECYCLE_FILES[@]}")
FILES+=("${AUTH_PROFILE_FILES[@]}")

if [[ ${#LIFECYCLE_FILES[@]} -eq 0 && ${#AUTH_PROFILE_FILES[@]} -eq 0 ]]; then
  echo "No supported OpenClaw bundle files found under: $DIST_DIR" >&2
  exit 1
fi

for file in "${FILES[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Expected bundle file not found: $file" >&2
    exit 1
  fi
done

PATCHED_COUNT=0
NEEDS_PATCH_COUNT=0

is_patched_file() {
  local file="$1"
  if grep -Fq $'function resolveGatewayTokenForDriftCheck(params) {\n\treturn resolveGatewayCredentialsFromConfig({\n\t\tcfg: params.cfg,\n\t\tenv: process.env,\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "env-first"\n\t}).token;\n}' "$file"; then
    return 0
  fi
  if grep -Fq $'function resolveGatewayDriftCheckCredentialsFromConfig(params) {\n\treturn resolveGatewayCredentialsFromConfig({\n\t\tcfg: params.cfg,\n\t\tenv: process.env,\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "env-first"\n\t});\n}' "$file"; then
    return 0
  fi
  return 1
}

needs_patch_file() {
  local file="$1"
  if grep -Fq $'function resolveGatewayTokenForDriftCheck(params) {\n\treturn resolveGatewayCredentialsFromConfig({\n\t\tcfg: params.cfg,\n\t\tenv: {},\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "config-first"\n\t}).token;\n}' "$file"; then
    return 0
  fi
  if grep -Fq $'function resolveGatewayDriftCheckCredentialsFromConfig(params) {\n\treturn resolveGatewayCredentialsFromConfig({\n\t\tcfg: params.cfg,\n\t\tenv: {},\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "config-first"\n\t});\n}' "$file"; then
    return 0
  fi
  return 1
}

for file in "${FILES[@]}"; do
  if is_patched_file "$file"; then
    PATCHED_COUNT=$((PATCHED_COUNT + 1))
  elif needs_patch_file "$file"; then
    NEEDS_PATCH_COUNT=$((NEEDS_PATCH_COUNT + 1))
  fi
done

if [[ "$MODE" == "check" ]]; then
  if [[ $NEEDS_PATCH_COUNT -eq 0 ]]; then
    echo "already patched"
    exit 0
  fi
  echo "patch missing in $NEEDS_PATCH_COUNT file(s)"
  exit 1
fi

if [[ $NEEDS_PATCH_COUNT -eq 0 ]]; then
  if [[ $PATCHED_COUNT -gt 0 ]]; then
    echo "already patched"
    exit 0
  fi
  echo "no supported patch target found"
  exit 0
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
PATCH_PATTERN_WRAPPER='s/function resolveGatewayTokenForDriftCheck\(params\) \{\n\treturn resolveGatewayCredentialsFromConfig\(\{\n\t\tcfg: params\.cfg,\n\t\tenv: \{\},\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "config-first"\n\t\}\)\.token;\n\}/function resolveGatewayTokenForDriftCheck(params) {\n\treturn resolveGatewayCredentialsFromConfig({\n\t\tcfg: params.cfg,\n\t\tenv: process.env,\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "env-first"\n\t}).token;\n}/g'
PATCH_PATTERN_DRIFT='s/function resolveGatewayDriftCheckCredentialsFromConfig\(params\) \{\n\treturn resolveGatewayCredentialsFromConfig\(\{\n\t\tcfg: params\.cfg,\n\t\tenv: \{\},\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "config-first"\n\t\}\);\n\}/function resolveGatewayDriftCheckCredentialsFromConfig(params) {\n\treturn resolveGatewayCredentialsFromConfig({\n\t\tcfg: params.cfg,\n\t\tenv: process.env,\n\t\tmodeOverride: "local",\n\t\tlocalTokenPrecedence: "env-first"\n\t});\n}/g'

for file in "${FILES[@]}"; do
  if ! needs_patch_file "$file"; then
    continue
  fi
  cp "$file" "$file.bak.$STAMP"
  perl -0pi -e "$PATCH_PATTERN_WRAPPER" -e "$PATCH_PATTERN_DRIFT" "$file"
done

for file in "${FILES[@]}"; do
  if needs_patch_file "$file"; then
    echo "Patch verification failed: $file" >&2
    exit 1
  fi
done

echo "patched openclaw gateway token drift check"
printf 'Backups created with suffix: .bak.%s\n' "$STAMP"
