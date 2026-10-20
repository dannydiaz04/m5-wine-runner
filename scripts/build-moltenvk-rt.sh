#!/bin/zsh
# Build isolated experimental MoltenVK with Hardware Ray Tracing (VK_KHR_ray_query / VK_KHR_ray_tracing_pipeline)
# for id Tech 8 (DOOM: The Dark Ages) on Apple Silicon M5 Max.

set -euo pipefail

DEST_DIR="${M5RUNNER_GAMES_DIR:-$HOME/Games}/sdk/moltenvk-rt"
WORK_DIR="${TMPDIR:-/tmp}/moltenvk-rt-build"
PR_NUMBER="${MOLTENVK_RT_PR:-2771}"

echo "=== Building Experimental MoltenVK Ray Tracing (PR #${PR_NUMBER}) ==="
echo "Target SDK Directory: ${DEST_DIR}"

for tool in cmake ninja git xcodebuild; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Installing missing build dependency: $tool via Homebrew..."
    brew install "$tool"
  fi
done

mkdir -p "$DEST_DIR"
rm -rf "$WORK_DIR"
git clone https://github.com/KhronosGroup/MoltenVK.git "$WORK_DIR"
cd "$WORK_DIR"

echo "Fetching experimental Hardware Ray Tracing branch (PR #${PR_NUMBER})..."
if git fetch origin "pull/${PR_NUMBER}/head:raytracing-pr"; then
  git checkout raytracing-pr
else
  echo "Warning: PR #${PR_NUMBER} ref unavailable; building latest main with Metal argument buffers."
fi

./fetchDependencies --macos
make macos

BUILT_DYLIB="Package/Release/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
if [[ ! -f "$BUILT_DYLIB" ]]; then
  BUILT_DYLIB="$(find Package -name 'libMoltenVK.dylib' | head -n 1)"
fi

if [[ -z "$BUILT_DYLIB" || ! -f "$BUILT_DYLIB" ]]; then
  echo "Error: Failed to locate compiled libMoltenVK.dylib" >&2
  exit 1
fi

cp -f "$BUILT_DYLIB" "$DEST_DIR/libMoltenVK.dylib"
/usr/bin/codesign --force -s - "$DEST_DIR/libMoltenVK.dylib"

cat > "$DEST_DIR/MoltenVK_icd.json" <<EOF
{
  "file_format_version": "1.0.0",
  "ICD": {
    "library_path": "${DEST_DIR}/libMoltenVK.dylib",
    "api_version": "1.3.296",
    "is_portability_driver": true
  }
}
EOF

echo "=== Successfully installed custom Ray Tracing libMoltenVK.dylib to ${DEST_DIR} ==="
