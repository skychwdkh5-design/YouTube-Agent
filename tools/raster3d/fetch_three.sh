#!/usr/bin/env bash
# three.js r160 (MIT) for tools/raster3d (not committed: fetched from jsdelivr and checked by SHA-256).
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p vendor
curl -s -o vendor/three.module.js https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js
curl -s -o vendor/LICENSE.three https://cdn.jsdelivr.net/npm/three@0.160.0/LICENSE
echo "76dea8151bc9352aef3528b4262e249b2604f62543828328db978d060d61a495  vendor/three.module.js" | sha256sum -c -
