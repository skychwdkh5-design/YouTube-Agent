#!/usr/bin/env bash
# Fetch the public-domain Natural Earth vector files OrbitalAtlas geo scenes use (sparse, shallow, ~50 MB). Not committed.
# Source: https://github.com/nvkelso/natural-earth-vector (public domain: see its LICENSE.md). Pinned commit below; sha256 are checked.
set -euo pipefail
DEST="${1:-data/natural_earth}"; PIN=ca96624a56bd078437bca8184e78163e5039ad19
TMP="$(mktemp -d)"; export GIT_LFS_SKIP_SMUDGE=1
git clone --depth 1 --filter=blob:none --sparse https://github.com/nvkelso/natural-earth-vector "$TMP/ne"
cd "$TMP/ne"; [ "$(git rev-parse HEAD)" = "$PIN" ] || echo "WARNING: upstream HEAD differs from pinned $PIN; checksums below may fail" >&2
git sparse-checkout set --no-cone /LICENSE.md $(for f in ne_110m_land ne_50m_land ne_10m_land ne_110m_admin_0_countries ne_50m_admin_0_countries ne_10m_admin_0_countries ne_10m_populated_places ne_10m_geography_marine_polys ne_10m_geography_regions_polys; do echo /geojson/$f.geojson; done)
cd - >/dev/null; mkdir -p "$DEST"; cp "$TMP"/ne/geojson/*.geojson "$TMP/ne/LICENSE.md" "$DEST"/
( cd "$DEST" && sha256sum -c "$OLDPWD/data/natural_earth.sha256" ) || echo "checksum mismatch or manifest missing (see data/natural_earth.sha256)" >&2
rm -rf "$TMP"; echo "Natural Earth data in $DEST"
