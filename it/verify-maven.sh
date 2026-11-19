#!/usr/bin/env bash
# Copyright 2026 the ltsboot contributors. SPDX-License-Identifier: Apache-2.0
#
# Docker-only verification of the Maven side of lts-bom (T-4.3).
#   1. `mvn -q verify` of the BOM project, then deploys the two POMs to a throw-away file repository (it/repo)
#   2. control app (spring-boot-starter-parent 2.7.18), parent app (lts-starter-parent) and BOM app (import lts-dependencies):
#      `dependency:tree` + `package` (compiles a tiny class)
#   3. asserts the ADR-004 default versions and the absence of org.lz4 / mchange
# Usage: it/verify-maven.sh [jdk: 8|11|17 (default 8)]     Logs: it/work/maven-<app>.tree.txt
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; JDK="${1:-8}"; OUT="$HERE/it/work"
mkdir -p "$OUT"; rm -rf "$HERE/it/repo"; mkdir -p "$HERE/it/repo"
docker volume create lts-m2-cache >/dev/null
mvn_run() { # <workdir inside /work> <mvn args...>
  local wd=$1; shift
  docker run --rm -i --memory=6g --cpus=4 -v "$HERE":/work -w "/work/$wd" -v lts-m2-cache:/root/.m2 \
    "maven:3.9-eclipse-temurin-$JDK" mvn -B -ntp -s /work/it/settings.xml "$@"
}
mvn_run . -q verify
mvn_run . -q deploy -DaltDeploymentRepository=lts-it::default::file:///work/it/repo
for app in control parent bom; do
  mvn_run it/maven-$app-app package -DskipTests > "$OUT/maven-$app.package.log" 2>&1 || { tail -40 "$OUT/maven-$app.package.log"; exit 1; }
  mvn_run it/maven-$app-app dependency:tree -DoutputFile=/work/it/work/maven-$app.tree.txt > "$OUT/maven-$app.tree.log" 2>&1 || { tail -40 "$OUT/maven-$app.tree.log"; exit 1; }
done
fail=0
expect() { # <app> <regex> <description>
  if grep -Eq "$2" "$OUT/maven-$1.tree.txt"; then echo "ok   [$1] $3"; else echo "FAIL [$1] $3"; fail=1; fi; }
absent() {
  if grep -Eq "$2" "$OUT/maven-$1.tree.txt"; then echo "FAIL [$1] $3"; fail=1; else echo "ok   [$1] $3"; fi; }
for app in parent bom; do
  expect $app 'jackson-databind:jar:2\.18\.12' 'jackson-databind 2.18.12'
  expect $app 'thymeleaf:jar:3\.1\.7\.RELEASE' 'thymeleaf 3.1.7.RELEASE'
  expect $app 'thymeleaf-spring5:jar:3\.1\.7\.RELEASE' 'thymeleaf-spring5 3.1.7.RELEASE'
  expect $app 'activemq-client:jar:5\.16\.8' 'activemq-client 5.16.8'
  expect $app 'at\.yawk\.lz4:lz4-java:jar:1\.11\.4' 'at.yawk.lz4:lz4-java 1.11.4'
  absent $app 'org\.lz4:' 'no org.lz4 artifact'
  expect $app 'nimbus-jose-jwt:jar:9\.48' 'nimbus-jose-jwt 9.48'
  absent $app 'mchange' 'no com.mchange artifact (quartz)'
  expect $app 'quartz:jar:2\.3\.2' 'quartz still present'
  expect $app 'tomcat-embed-core:jar:9\.0\.124' 'tomcat-embed-core 9.0.124'
  expect $app 'netty-codec-http:jar:4\.1\.141\.Final' 'netty-codec-http 4.1.141.Final'
  expect $app 'spring-core:jar:5\.3\.39' 'spring-core 5.3.39'
  expect $app 'spring-security-core:jar:5\.7\.14' 'spring-security-core 5.7.14'
  expect $app 'reactor-core:jar:3\.4\.41' 'reactor-core 3.4.41 (Reactor 2020.0.47)'
  expect $app 'snakeyaml:jar:1\.33' 'snakeyaml 1.33'
done
expect control 'org\.lz4:lz4-java:jar:1\.8\.0' 'control still has org.lz4:lz4-java 1.8.0 (sanity)'
expect control 'mchange-commons-java' 'control still has mchange-commons-java (sanity)'
expect control 'jackson-databind:jar:2\.13\.5' 'control still has jackson 2.13.5 (sanity)'
echo "--- selected lines (parent app)"; grep -E 'jackson-databind|thymeleaf:|activemq-client|lz4|nimbus-jose-jwt|mchange|quartz|tomcat-embed-core' "$OUT/maven-parent.tree.txt" || true
exit $fail
