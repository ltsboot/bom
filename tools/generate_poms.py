#!/usr/bin/env python3
# Copyright 2026 the ltsboot contributors.
# SPDX-License-Identifier: Apache-2.0
"""Generates lts-dependencies/pom.xml and lts-starter-parent/pom.xml from ONE table (VERSIONS below).

Source of the values: docs/decisions/ADR-003 (Spring portfolio) and ADR-004 (third-party libraries) of the ltsboot
workspace. The dependencyManagement entries that Boot 2.7.18 drives through a property are COPIED from the real
spring-boot-dependencies-2.7.18.pom (type, classifier, scope, exclusions), only the version property is ours.

Usage: generate_poms.py <spring-boot-dependencies-2.7.18.pom> <repo-dir>
"""
import sys
import xml.etree.ElementTree as ET

NS = "http://maven.apache.org/POM/4.0.0"
Q = "{%s}" % NS
VERSION = "2.7.18.1"
BOOT = "2.7.18"

# property (same name Boot uses) -> (version, comment)
OVERRIDES = [
    ("spring-framework.version", "5.3.39", "ADR-003: last OSS 5.3 (fork line: 5.3.39.1, see README 'Fork versions')"),
    ("spring-security.version", "5.7.14", "ADR-003: last OSS 5.7 on Central (fork line: 5.7.14.1)"),
    ("reactor-bom.version", "2020.0.47", "ADR-003: pairs with Framework 5.3.39"),
    ("spring-ldap.version", "2.4.4", "ADR-003"),
    ("tomcat.version", "9.0.124", "ADR-004"),
    ("netty.version", "4.1.141.Final", "ADR-004: pairs with Reactor Netty 1.0.48"),
    ("undertow.version", "2.2.41.Final", "ADR-004"),
    ("jetty.version", "9.4.58.v20250814", "ADR-004: last 9.4 on Central; two critical CVEs have no fix (doc-mitigation)"),
    ("jackson-bom.version", "2.18.12", "ADR-004 (human-approved). Opt-in fallback: 2.15.4 (fixes far fewer CVEs)"),
    ("activemq.version", "5.16.8", "ADR-004: last Java 8 release. Opt-in: 5.19.12 (needs Java 11)"),
    ("rabbit-amqp-client.version", "5.38.0", "ADR-004"),
    ("elasticsearch.version", "7.17.29", "ADR-004"),
    ("thymeleaf.version", "3.1.7.RELEASE", "ADR-004 (human-approved): removes #request/#response/#session/#servletContext"),
    ("thymeleaf-extras-springsecurity.version", "3.1.7.RELEASE", "ADR-004: must move with Thymeleaf"),
    ("thymeleaf-layout-dialect.version", "3.4.0", "ADR-004: must move with Thymeleaf"),
    ("snakeyaml.version", "1.33", "ADR-004 (CVE-2022-1471 needs 2.0: not fixed here)"),
    ("log4j2.version", "2.25.5", "ADR-004"),
    ("logback.version", "1.2.13", "ADR-004"),
    ("graphql-java.version", "19.11", "ADR-004"),
    ("freemarker.version", "2.3.35", "ADR-004"),
    ("assertj.version", "3.27.7", "ADR-004 (test scope)"),
    ("jakarta-mail.version", "1.6.8", "ADR-004"),
    ("sun-mail.version", "1.6.8",
     "T-4.6: CVE-2025-7962 (SMTP CR/LF injection) is fixed in the implementation com.sun.mail:jakarta.mail, which Boot versions "
     "with sun-mail.version (spring-boot-starter-mail depends on it; only the API was bumped before)"),
]
# properties Boot 2.7.18 does not have (transitive-only artifacts, ADR-004 section 6)
NEW_PROPS = [
    ("nimbus-jose-jwt.version", "9.48", "ADR-004 s6: transitive of spring-security-oauth2-jose"),
    ("parsson.version", "1.0.5", "ADR-004 s6: transitive of elasticsearch-java"),
    ("commons-beanutils.version", "1.11.0", "ADR-004 s6: transitive"),
    ("lz4-java.version", "1.11.4", "ADR-004 s6: at.yawk.lz4:lz4-java replaces org.lz4:lz4-java 1.8.0 (groupId change)"),
    ("lz4-java-relocation.version", "1.8.1",
     "ADR-004 s6: org.lz4:lz4-java 1.8.1 is a Sonatype relocation POM to at.yawk.lz4:lz4-java; managing it makes Maven follow "
     "the relocation for kafka-clients etc. (instead of excluding lz4, which would leave Kafka without lz4)"),
    ("xnio.version", "3.8.14.Final",
     "ADR-004 s6: transitive of Undertow. T-4.5.15: pinned to 3.8.14 (CVE-2023-5685 fixed in 3.8.14). xnio 3.8.15+ (incl. 3.8.16 "
     "declared by Undertow 2.2.41) hangs forever in NioTcpServer.close/WorkerThread.cancelKey when Undertow stops after a failed "
     "secondary-connector bind, so an app whose port is in use hangs at startup instead of failing (3.8.7/3.8.8/3.8.14 pass, "
     "3.8.15/3.8.16/3.8.17 hang). No advisory open against 3.8.14 (OSV 2026-11-21)"),
    ("log4j-to-slf4j.version", "2.21.1",
     "T-4.5.7: log4j-to-slf4j 2.22+ DECLARES slf4j-api 2.0.x (it still runs on 1.7 at runtime, support range [1.7,3), but a Gradle consumer "
     "resolves the declared 2.0.x, which Boot 2.7's logback 1.2 cannot bind: logging silently dead). 2.21.1 is the last release that "
     "declares slf4j-api 1.7.36. Only the bridge is pinned: log4j-api/-core/-jul/-slf4j-impl stay on log4j2.version "
     "(the CVEs are in log4j-api/-core, not in the bridge)"),
]
NEW_PROPS.append(("jackson-module-kotlin.version", "2.17.3",
     "T-4.5.10: jackson-module-kotlin 2.18.x ships Kotlin 1.8.0 metadata, which the Kotlin 1.6.21 compiler of Boot 2.7 cannot read (every "
     "Kotlin 1.6 module that has it on the compile classpath fails). 2.17.3 ships 1.7.1 metadata (readable by 1.6.x) and runs on "
     "jackson-databind/-core 2.18.12 (verified with the webflux-kotlin-coroutines compat app). No CVE is open against this module"))
NEW_DEPS = [  # (groupId, artifactId, version property, exclusions)
    ("com.nimbusds", "nimbus-jose-jwt", "nimbus-jose-jwt.version", []),
    ("org.eclipse.parsson", "parsson", "parsson.version", []),
    ("commons-beanutils", "commons-beanutils", "commons-beanutils.version", []),
    ("at.yawk.lz4", "lz4-java", "lz4-java.version", []),
    ("org.lz4", "lz4-java", "lz4-java-relocation.version", []),
    ("org.apache.logging.log4j", "log4j-to-slf4j", "log4j-to-slf4j.version", []),
    ("com.fasterxml.jackson.module", "jackson-module-kotlin", "jackson-module-kotlin.version", []),
    ("org.jboss.xnio", "xnio-api", "xnio.version", []),
    ("org.jboss.xnio", "xnio-nio", "xnio.version", []),
]
# Boot entries that need an ADDED exclusion (they are re-declared with the extra exclusions)
EXTRA_EXCLUSIONS = {
    ("org.quartz-scheduler", "quartz"): [("com.mchange", "mchange-commons-java")],
}
LICENSE = """<!--
  Copyright 2026 the ltsboot contributors.
  SPDX-License-Identifier: Apache-2.0

  GENERATED by tools/generate_poms.py - edit the table in that script, not this file.
  ltsboot is an independent project, not affiliated with, endorsed by or sponsored by Broadcom Inc. or VMware.
-->
"""


def load_boot(path):
    root = ET.parse(path).getroot()
    entries = []
    for d in root.find(Q + "dependencyManagement").find(Q + "dependencies"):
        g = lambda n: (d.findtext(Q + n) or "").strip()
        ex = [(e.findtext(Q + "groupId"), e.findtext(Q + "artifactId"))
              for e in d.iterfind(Q + "exclusions/" + Q + "exclusion")]
        entries.append(dict(g=g("groupId"), a=g("artifactId"), v=g("version"), t=g("type"), c=g("classifier"),
                            s=g("scope"), ex=ex))
    return entries


def dep_xml(e, version, indent="      "):
    o = [f"{indent}<dependency>", f"{indent}  <groupId>{e['g']}</groupId>", f"{indent}  <artifactId>{e['a']}</artifactId>",
         f"{indent}  <version>{version}</version>"]
    if e.get("t"):
        o.append(f"{indent}  <type>{e['t']}</type>")
    if e.get("c"):
        o.append(f"{indent}  <classifier>{e['c']}</classifier>")
    if e.get("s"):
        o.append(f"{indent}  <scope>{e['s']}</scope>")
    if e["ex"]:
        o.append(f"{indent}  <exclusions>")
        for g, a in e["ex"]:
            o += [f"{indent}    <exclusion>", f"{indent}      <groupId>{g}</groupId>",
                  f"{indent}      <artifactId>{a}</artifactId>", f"{indent}    </exclusion>"]
        o.append(f"{indent}  </exclusions>")
    o.append(f"{indent}</dependency>")
    return "\n".join(o)


def props_xml(rows, indent="    "):
    return "\n".join(f"{indent}<!-- {c} -->\n{indent}<{p}>{v}</{p}>" for p, v, c in rows)


def main(boot_pom, out):
    boot = load_boot(boot_pom)
    names = {p for p, _, _ in OVERRIDES}
    managed = [e for e in boot if e["v"].startswith("${") and e["v"][2:-1] in names]
    # Entries copied from Boot: version replaced by the same property (defined in OUR pom with OUR value).
    by_prop = {}
    for e in managed:
        by_prop.setdefault(e["v"][2:-1], []).append(e)
    missing = names - set(by_prop)
    # these only drive entries through other properties or nothing in dependencyManagement; reported, not fatal
    for p in sorted(missing):
        print(f"note: no dependencyManagement entry uses ${{{p}}} in Boot {BOOT}", file=sys.stderr)
    dm = []
    for p, _, _ in OVERRIDES:
        for e in by_prop.get(p, []):
            e = dict(e)
            e["ex"] = e["ex"] + EXTRA_EXCLUSIONS.get((e["g"], e["a"]), [])
            dm.append((p, e))
    # Boot entries that are NOT property-driven by one of our properties but need an added exclusion
    covered = {(e["g"], e["a"], e["c"]) for _, e in dm}
    for e in boot:
        key = (e["g"], e["a"])
        if key in EXTRA_EXCLUSIONS and (e["g"], e["a"], e["c"]) not in covered:
            e = dict(e)
            e["ex"] = e["ex"] + EXTRA_EXCLUSIONS[key]
            dm.append((e["v"], e))
    # sanity: every extra exclusion was applied
    for key in EXTRA_EXCLUSIONS:
        assert any((e["g"], e["a"]) == key for _, e in dm), key
    new_entries = [dict(g=g, a=a, v="${%s}" % p, t="", c="", s="", ex=ex) for g, a, p, ex in NEW_DEPS]

    all_props = OVERRIDES + NEW_PROPS
    # Boot properties that the re-declared (exclusion) entries reference; the BOM must define them (a BOM cannot see Boot's
    # properties). The parent inherits them from Boot, so users can still override them there.
    boot_props = {c.tag.replace(Q, ""): (c.text or "").strip() for c in ET.parse(boot_pom).getroot().find(Q + "properties")}
    used = {e["v"][2:-1] for _, e in dm if e["v"].startswith("${")} - {p for p, _, _ in all_props}
    bom_props = all_props + [(n, boot_props[n], f"same value as Boot {BOOT} (needed because a BOM cannot read Boot's properties)")
                             for n in sorted(used)]
    boot_import = dict(g="org.springframework.boot", a="spring-boot-dependencies", v=BOOT, t="pom", c="", s="import", ex=[])

    # ---------------- lts-dependencies: importable BOM ----------------
    # Order matters for Maven imports: our direct entries win over everything; Boot's BOM is imported LAST.
    imports = [e for _, e in dm if e["s"] == "import"]
    direct = [e for _, e in dm if e["s"] != "import"] + new_entries
    body = [LICENSE.strip(), '<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">',
            "  <modelVersion>4.0.0</modelVersion>", "",
            "  <groupId>io.github.ltsboot</groupId>", "  <artifactId>lts-dependencies</artifactId>",
            f"  <version>{VERSION}</version>", "  <packaging>pom</packaging>", "",
            "  <name>ltsboot lts-dependencies</name>",
            f"  <description>Importable BOM: Spring Boot {BOOT} dependency management with the patched third-party versions of "
            "the ltsboot project (not affiliated with Broadcom/VMware).</description>",
            "  <url>https://github.com/ltsboot/bom</url>",
            "  <licenses><license><name>Apache License, Version 2.0</name>"
            "<url>https://www.apache.org/licenses/LICENSE-2.0</url></license></licenses>",
            "  <developers><developer><id>ltsboot</id><name>The ltsboot contributors</name>"
            "<url>https://github.com/ltsboot</url></developer></developers>",
            "  <scm><connection>scm:git:https://github.com/ltsboot/bom.git</connection>"
            "<developerConnection>scm:git:git@github.com:ltsboot/bom.git</developerConnection>"
            "<url>https://github.com/ltsboot/bom</url></scm>", "",
            "  <properties>", props_xml(bom_props), "  </properties>", "",
            "  <dependencyManagement>", "    <dependencies>",
            "      <!-- Direct entries override every imported BOM. Imports below come BEFORE Boot's BOM, so they win too. -->"]
    for e in direct:
        body.append(dep_xml(e, e["v"]))
    body.append("      <!-- Imported BOMs with our versions (first import wins) -->")
    for e in imports:
        body.append(dep_xml(e, e["v"]))
    body.append(f"      <!-- Boot's own BOM LAST: everything not overridden above stays exactly as Boot {BOOT} manages it -->")
    body.append(dep_xml(boot_import, BOOT))
    body += ["    </dependencies>", "  </dependencyManagement>", "</project>", ""]
    with open(f"{out}/lts-dependencies/pom.xml", "w") as f:
        f.write("\n".join(body))

    # ---------------- lts-starter-parent ----------------
    # Boot reads these properties inside its own BOM (spring-boot-dependencies), so a property override is all that is needed
    # for the entries Boot already manages. Only NEW entries and exclusions are re-declared here.
    parent_dm = [e for e in new_entries]
    for _, e in dm:
        if (e["g"], e["a"]) in EXTRA_EXCLUSIONS:
            parent_dm.append(e)
    p = [LICENSE.strip(), '<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
         '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">',
         "  <modelVersion>4.0.0</modelVersion>", "",
         "  <parent>", "    <groupId>org.springframework.boot</groupId>", "    <artifactId>spring-boot-starter-parent</artifactId>",
         f"    <version>{BOOT}</version>", "    <relativePath/>", "  </parent>", "",
         "  <groupId>io.github.ltsboot</groupId>", "  <artifactId>lts-starter-parent</artifactId>",
         f"  <version>{VERSION}</version>", "  <packaging>pom</packaging>", "",
         "  <name>ltsboot lts-starter-parent</name>",
         f"  <description>Maven parent with spring-boot-starter-parent {BOOT} semantics (plugin management, Java 8, UTF-8, "
         "resource filtering) plus the patched third-party versions of the ltsboot project (not affiliated with Broadcom/VMware).</description>",
         "  <url>https://github.com/ltsboot/bom</url>",
         "  <licenses><license><name>Apache License, Version 2.0</name>"
         "<url>https://www.apache.org/licenses/LICENSE-2.0</url></license></licenses>",
         "  <developers><developer><id>ltsboot</id><name>The ltsboot contributors</name>"
            "<url>https://github.com/ltsboot</url></developer></developers>",
            "  <scm><connection>scm:git:https://github.com/ltsboot/bom.git</connection>"
            "<developerConnection>scm:git:git@github.com:ltsboot/bom.git</developerConnection>"
            "<url>https://github.com/ltsboot/bom</url></scm>", "",
         "  <properties>", props_xml(all_props), "  </properties>", "",
         "  <dependencyManagement>", "    <dependencies>"]
    for e in parent_dm:
        p.append(dep_xml(e, e["v"]))
    p += ["    </dependencies>", "  </dependencyManagement>", "</project>", ""]
    with open(f"{out}/lts-starter-parent/pom.xml", "w") as f:
        f.write("\n".join(p))
    print(f"lts-dependencies: {len(direct)} direct + {len(imports)} imports + Boot BOM; "
          f"lts-starter-parent: {len(all_props)} properties + {len(parent_dm)} entries")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
