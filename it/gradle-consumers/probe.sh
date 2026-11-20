#!/usr/bin/env bash
# Copyright 2026 the ltsboot contributors. SPDX-License-Identifier: Apache-2.0
# Usage: it/gradle-consumers/probe.sh <jdk 8|11|17> <platform|enforced|depmgmt|boot> <outdir>   (Docker only)
set -uo pipefail
HERE="$(cd "$(dirname "$0")/../.." && pwd)"; JDK=$1; MODE=$2; OUT=$3; mkdir -p "$OUT"
docker volume create lts-bom-gradle-cache >/dev/null
g() { docker run --rm -i -u root --memory=6g --cpus=4 -v "$HERE":/work -w /work/it/gradle-consumers \
  -v lts-bom-gradle-cache:/home/gradle/.gradle -e GRADLE_USER_HOME=/home/gradle/.gradle \
  "gradle:7.6.3-jdk$JDK" gradle --no-daemon --console=plain -PltsRepo=file:///work/it/repo -PbomMode="$MODE" "$@"; }
for p in logging kotlin-mockk kotlin-mockk-1124 quartz-default quartz-c3p0 elasticsearch-java layout-dialect; do
  cfg=runtimeClasspath; [[ $p == kotlin-mockk* || $p == layout-dialect ]] && cfg=testRuntimeClasspath
  g ":$p:dependencies" --configuration $cfg > "$OUT/$MODE-$p.deps.txt" 2>&1
done
g :logging:test > "$OUT/$MODE-logging.test.txt" 2>&1; echo "logging test rc=$?" >> "$OUT/$MODE-logging.test.txt"
