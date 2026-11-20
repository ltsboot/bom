#!/usr/bin/env bash
# Copyright 2026 the ltsboot contributors. SPDX-License-Identifier: Apache-2.0
# T-4.5 (Docker only): resolves the Gradle consumer projects in the three ways a Boot 2.7 build applies a BOM and asserts the outcome.
# Needs it/repo (it/verify-maven.sh). Usage: it/gradle-consumers/verify.sh [jdk 8|11|17 (default 8)]   Output: it/work/gradle-consumers/
set -uo pipefail
HERE="$(cd "$(dirname "$0")/../.." && pwd)"; JDK="${1:-8}"; OUT="$HERE/it/work/gradle-consumers"; rm -rf "$OUT"; mkdir -p "$OUT"
for m in platform enforced depmgmt boot; do "$HERE/it/gradle-consumers/probe.sh" "$JDK" $m "$OUT" > /dev/null 2>&1; done
fail=0
ok() { echo "ok   $1"; }; ko() { echo "FAIL $1"; fail=1; }
has() { grep -Eq "$2" "$OUT/$1" && return 0 || return 1; }   # has <file> <regex>
chk() { local desc=$1 file=$2 re=$3 want=$4   # want = yes|no
  if has "$file" "$re"; then [[ $want == yes ]] && ok "$desc" || ko "$desc"; else [[ $want == no ]] && ok "$desc" || ko "$desc"; fi; }
for m in platform enforced depmgmt; do
  has $m-logging.test.txt 'logging test rc=0' && ok "[$m] logging: slf4j + log4j-api calls reach logback" || ko "[$m] logging test"
  chk "[$m] logging: no slf4j-api 2.x" $m-logging.deps.txt 'slf4j-api:[0-9.]* -> 2\.|slf4j-api:2\.' no
  chk "[$m] logging: log4j-api 2.25.5" $m-logging.deps.txt 'log4j-api:[0-9.]* -> 2\.25\.5' yes
  chk "[$m] quartz starter without consumer rule: no mchange (BOM exclusion honoured)" $m-quartz-default.deps.txt 'mchange' no
  chk "[$m] quartz + c3p0: mchange-commons-java stays (c3p0 needs it)" $m-quartz-c3p0.deps.txt 'mchange-commons-java:0\.2\.19' yes
  chk "[$m] mockk 1.12.4: kotlin-stdlib 1.6.21" $m-kotlin-mockk-1124.deps.txt 'kotlin-stdlib:1\.6\.0 -> 1\.6\.21' yes
  chk "[$m] layout-dialect 3.4.0 selected" $m-layout-dialect.deps.txt 'thymeleaf-layout-dialect -> 3\.4\.0' yes
done
for m in enforced depmgmt; do
  chk "[$m] mockk 1.13.5: kotlin-stdlib/-reflect forced to the managed 1.6.21" $m-kotlin-mockk.deps.txt 'kotlin-reflect:1\.8\.20 -> 1\.6\.21' yes
  chk "[$m] mockk 1.13.5: no Kotlin 1.8 stdlib left" $m-kotlin-mockk.deps.txt 'kotlin-stdlib:[0-9.]*( -> )?1\.8' no
  chk "[$m] jakarta.json-api stays at the managed javax.json 1.1.6" $m-elasticsearch-java.deps.txt 'jakarta.json-api:2\.0\.[0-9]* -> 1\.1\.6' yes
done
# documented (inherited from Boot 2.7.18's own BOM): a plain platform() lets a transitive request win over a managed version
chk "[platform] mockk 1.13.5 drags kotlin-reflect 1.8.20 (documented; same as Boot's BOM, see [boot])" platform-kotlin-mockk.deps.txt 'kotlin-reflect:1\.8\.20 \(\*\)' yes
chk "[boot control] same kotlin 1.8.20 with Boot's own BOM as plain platform" boot-kotlin-mockk.deps.txt 'kotlin-reflect:1\.8\.20 \(\*\)' yes
chk "[platform] jakarta.json-api 2.0.x wins (documented; same as Boot's BOM)" platform-elasticsearch-java.deps.txt 'jakarta.json-api:1\.1\.6 -> 2\.0' yes
chk "[boot control] same jakarta.json-api 2.0.x with Boot's own BOM" boot-elasticsearch-java.deps.txt 'jakarta.json-api:1\.1\.6 -> 2\.0' yes
chk "[boot control] Quartz keeps mchange without the lts-bom exclusion (sanity)" boot-quartz-default.deps.txt 'mchange-commons-java' yes
chk "[platform] layout-dialect + Groovy 3: capability conflict is reported (documented)" platform-layout-dialect.deps.txt 'groovy:[0-9.]* FAILED' yes
exit $fail
