#!/usr/bin/env bash
# Build Bitcoin Core (see doc/build-unix.md for details).
set -euo pipefail

cd "$(dirname "$0")"

BUILD_DIR=build
JOBS="$(nproc)"

cmake -B "$BUILD_DIR"
cmake --build "$BUILD_DIR" -j "$JOBS"

echo
echo "Build complete. Binaries are in $BUILD_DIR/bin/"
