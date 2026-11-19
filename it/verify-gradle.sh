#!/usr/bin/env bash
# Copyright 2026 the ltsboot contributors. SPDX-License-Identifier: Apache-2.0
#
# Docker-only verification of the Gradle platform example (T-4.3). Needs it/repo (created by it/verify-maven.sh).
# Resolves runtimeClasspath of examples/gradle-platform and asserts the ADR-004 default versions.
# Usage: it/verify-gradle.sh [jdk: 8|11|17 (default 17)]      Output: it/work/gradle-*.txt
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; JDK="${1:-17}"; OUT="$HERE/it/work"; mkdir -p "$OUT"
[[ -d $HERE/it/repo/io/github/ltsboot/lts-dependencies ]] || { echo "run it/verify-maven.sh first (creates it/repo)" >&2; exit 2; }
docker volume create lts-bom-gradle-cache >/dev/null
g() { docker run --rm -i -u root --memory=6g --cpus=4 -v "$HERE":/work -w /work/examples/gradle-platform \
  -v lts-bom-gradle-cache:/home/gradle/.gradle -e GRADLE_USER_HOME=/home/gradle/.gradle \
  "gradle:7.6.3-jdk$JDK" gradle --no-daemon --console=plain -PltsRepo=file:///work/it/repo "$@"; }
g build > "$OUT/gradle-build.txt" 2>&1 || { tail -40 "$OUT/gradle-build.txt"; exit 1; }
g lsRuntimeJars > "$OUT/gradle-jars.txt" 2>&1 || { tail -40 "$OUT/gradle-jars.txt"; exit 1; }
g dependencies --configuration runtimeClasspath > "$OUT/gradle-deps.txt" 2>&1 || { tail -40 "$OUT/gradle-deps.txt"; exit 1; }
fail=0
expect() { if grep -Eq "$1" "$OUT/gradle-deps.txt"; then echo "ok   $2"; else echo "FAIL $2"; fail=1; fi; }
absent() { if grep -Eq "$1" "$OUT/gradle-deps.txt"; then echo "FAIL $2"; fail=1; else echo "ok   $2"; fi; }
expect 'jackson-databind:[0-9.]* -> 2\.18\.12|jackson-databind:2\.18\.12' 'jackson-databind 2.18.12'
expect 'thymeleaf:[0-9.A-Z]* -> 3\.1\.7\.RELEASE|org.thymeleaf:thymeleaf:3\.1\.7\.RELEASE' 'thymeleaf 3.1.7.RELEASE'
expect 'activemq-client:[0-9.]* -> 5\.16\.8|activemq-client:5\.16\.8' 'activemq-client 5.16.8'
expect 'at\.yawk\.lz4:lz4-java' 'at.yawk.lz4:lz4-java present'
expect 'lz4-java:[0-9.]* -> 1\.11\.4|at\.yawk\.lz4:lz4-java:1\.11\.4' 'at.yawk.lz4:lz4-java 1.11.4'
absent 'FAILED' 'no unresolved dependency (capability conflict resolved)'
absent 'org\.lz4:lz4-java:[0-9.]+( \(\*\))?$' 'no org.lz4:lz4-java node stays (all replaced by at.yawk)'
expect 'nimbus-jose-jwt:[0-9.]* -> 9\.48|nimbus-jose-jwt:9\.48' 'nimbus-jose-jwt 9.48'
absent 'mchange' 'no com.mchange artifact (quartz)'
expect 'quartz:[0-9.]*' 'quartz present'
expect 'tomcat-embed-core:[0-9.]* -> 9\.0\.124|tomcat-embed-core:9\.0\.124' 'tomcat-embed-core 9.0.124'
expect 'spring-core:[0-9.]* -> 5\.3\.39|spring-core:5\.3\.39' 'spring-core 5.3.39'
if grep -Eq "^jar: lz4-java-1\.8" "$OUT/gradle-jars.txt" || grep -Eq "^jar: mchange" "$OUT/gradle-jars.txt"; then echo "FAIL runtime jars contain org.lz4 / mchange"; fail=1; else echo "ok   runtime jars: no lz4-java-1.8.x, no mchange"; fi
grep -E "^jar: (lz4|nimbus|jackson-databind|thymeleaf-3|activemq-client|quartz)" "$OUT/gradle-jars.txt" | sort
echo "--- selected lines"; grep -E 'jackson-databind|thymeleaf:|activemq-client|lz4|nimbus-jose-jwt|mchange|quartz:|spring-core' "$OUT/gradle-deps.txt" | sort -u | head -30
exit $fail
