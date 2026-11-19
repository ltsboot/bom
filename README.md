<!--
  Copyright 2026 the ltsboot contributors.
  SPDX-License-Identifier: Apache-2.0
-->
# lts-bom

Two Maven artifacts (groupId `io.github.ltsboot`, version `2.7.18.1`) that keep a **Spring Boot 2.7.18** application on
patched versions of Spring and of its third-party dependencies, without forking Boot itself:

| Artifact | What it is | Use it when |
|---|---|---|
| `lts-dependencies` | Importable BOM. Imports the patched BOMs/entries first and **Boot 2.7.18's own BOM last**, so one import replaces `spring-boot-dependencies`. | Maven without the Boot parent, or Gradle (`platform(...)`). |
| `lts-starter-parent` | Maven parent: `spring-boot-starter-parent:2.7.18` (plugin management, Java 8, UTF-8, resource filtering) plus the same overrides. | Maven applications that use `spring-boot-starter-parent` today: change only the `<parent>`. |

ltsboot is an independent project. It is **not affiliated with, endorsed by or sponsored by Broadcom Inc. or VMware**; "Spring"
is a trademark of its owner and is used here only to describe compatibility. License: Apache-2.0 (`LICENSE`).

The versions come from `ADR-003` (Spring portfolio) and `ADR-004` (third-party libraries) of the ltsboot workspace; both were
accepted by the maintainer on 2026-11-19. `tools/generate_poms.py` holds the one table both POMs are generated from.

## Maven: parent

```xml
<parent>
  <groupId>io.github.ltsboot</groupId>
  <artifactId>lts-starter-parent</artifactId>
  <version>2.7.18.1</version>
  <relativePath/>
</parent>
```
(replaces `org.springframework.boot:spring-boot-starter-parent:2.7.18`; keep `spring-boot-maven-plugin` as before.)

## Maven: BOM

```xml
<dependencyManagement><dependencies>
  <dependency>
    <groupId>io.github.ltsboot</groupId><artifactId>lts-dependencies</artifactId>
    <version>2.7.18.1</version><type>pom</type><scope>import</scope>
  </dependency>
</dependencies></dependencyManagement>
```
Import it **before** any other BOM that manages the same libraries (Maven: the first import wins).

## Gradle: platform

`examples/gradle-platform/` (verified on Gradle 7.6.3): `implementation platform('io.github.ltsboot:lts-dependencies:2.7.18.1')`
and Boot starters without versions. Two Gradle-only additions are in that example: Gradle ignores Maven `<exclusions>` in a BOM,
so the `mchange-commons-java` exclusion is declared in the build, and the `lz4-java` capability conflict (see below) needs a
`capabilitiesResolution` rule. With the Boot Gradle plugin / `io.spring.dependency-management`, override the properties
below in `gradle.properties` instead (`ext['jackson-bom.version'] = '2.15.4'`).

## What changes (defaults)

| Library | Boot 2.7.18 | lts-bom | Property |
|---|---|---|---|
| Spring Framework | 5.3.31 | 5.3.39 | `spring-framework.version` |
| Spring Security | 5.7.11 | 5.7.14 | `spring-security.version` |
| Reactor BOM | 2020.0.38 | 2020.0.47 | `reactor-bom.version` |
| Spring LDAP | 2.4.1 | 2.4.4 | `spring-ldap.version` |
| Tomcat | 9.0.83 | 9.0.124 | `tomcat.version` |
| Netty | 4.1.101.Final | 4.1.141.Final | `netty.version` |
| Undertow / XNIO | 2.2.28.Final / 3.8.7 | 2.2.41.Final / 3.8.16.Final | `undertow.version`, `xnio.version` (new) |
| Jetty | 9.4.53 | 9.4.58.v20250814 | `jetty.version` |
| Jackson | 2.13.5 | 2.18.12 | `jackson-bom.version` |
| ActiveMQ | 5.16.7 | 5.16.8 (Java 8) | `activemq.version` |
| RabbitMQ amqp-client | 5.14.3 | 5.38.0 | `rabbit-amqp-client.version` |
| Elasticsearch | 7.17.15 | 7.17.29 | `elasticsearch.version` |
| Thymeleaf (+ springsecurity5, layout dialect) | 3.0.15 (3.0.5, 3.0.0) | 3.1.7 (3.1.7, 3.4.0) | `thymeleaf.version`, `thymeleaf-extras-springsecurity.version`, `thymeleaf-layout-dialect.version` |
| SnakeYAML | 1.30 | 1.33 | `snakeyaml.version` |
| Log4j2 / Logback | 2.17.2 / 1.2.12 | 2.25.5 / 1.2.13 | `log4j2.version`, `logback.version` |
| graphql-java | 18.5 | 19.11 | `graphql-java.version` |
| FreeMarker, AssertJ, jakarta.mail | 2.3.32, 3.22.0, 1.6.7 | 2.3.35, 3.27.7, 1.6.8 | `freemarker.version`, `assertj.version`, `jakarta-mail.version` |
| nimbus-jose-jwt (transitive) | 9.22 | 9.48 | `nimbus-jose-jwt.version` (new managed entry) |
| parsson, commons-beanutils (transitive) | 1.0.0, 1.9.4 | 1.0.5, 1.11.0 | `parsson.version`, `commons-beanutils.version` (new) |
| lz4-java (Kafka, Elasticsearch) | `org.lz4:lz4-java` 1.8.0 | `at.yawk.lz4:lz4-java` 1.11.4 | `lz4-java.version` (new; groupId change) |
| mchange-commons-java (via Quartz) | 0.2.15 | excluded from `quartz` | - |

Everything else stays exactly as Boot 2.7.18 manages it. Behaviour notes for the risky bumps (Jackson 2.18, Thymeleaf 3.1 removing
`#request/#response/#session/#servletContext`, Netty/Reactor pairing, Kotlin metadata 1.8) are in ADR-004 sections 2, 4 and 5.

### Opt-in properties (documented alternatives, not defaults)

Set them in the application POM (parent users) or in `gradle.properties` (`ext[...]`); BOM-only Maven users declare their own
`dependencyManagement` entry **before** the import.

| Property | Opt-in value | Effect / cost |
|---|---|---|
| `activemq.version` | `5.19.12` | Fixes 11 more high CVEs (incl. KEV CVE-2026-34197). **Needs Java 11.** |
| `jackson-bom.version` | `2.15.4` | Smaller jump, but leaves 6 high + 6 medium CVEs open (ADR-004). |
| `spring-security.version` | `5.8.16` | Not covered by the fork's backports, no extra CVE fix, 3 binary breaks (ADR-003 section 3). |
| `spring-framework.version`, `spring-security.version` | `5.3.39.1`, `5.7.14.1` | The ltsboot fork line, once published (needs the fork repository and the relocator / ltsboot Gradle plugin, ADR-002/007/008). |

### Fork versions

The defaults use the plain OSS Spring releases (`5.3.39`, `5.7.14`), which exist on Maven Central. The ltsboot forks carry the extra
CVE backports under `5.3.39.1` / `5.7.14.1` (ADR-002); they are not published yet, so they are an opt-in until then.

### lz4-java (deviation from the literal ADR-004 wording)

ADR-004 asks for `at.yawk.lz4:lz4-java` plus a Maven exclusion of `org.lz4:lz4-java` on `kafka-clients`. An exclusion alone would
leave Kafka without lz4. Instead the BOM manages `org.lz4:lz4-java:1.8.1`, which is a Sonatype **relocation POM** to
`at.yawk.lz4:lz4-java`; Maven follows it and applies the managed `at.yawk.lz4:lz4-java:1.11.4`: no `org.lz4` jar, no duplicate
`net.jpountz` package, and every consumer (Kafka, Elasticsearch) still gets lz4. Verified by `it/verify-maven.sh`.

## Verification (Docker only)

```
it/verify-maven.sh 8     # mvn verify + deploy to it/repo, control / parent / BOM apps, 33 assertions on dependency:tree
it/verify-gradle.sh 17   # Gradle 7.6.3 platform example against it/repo
```
Each prints the selected `dependency:tree` / `dependencies` lines. A control app on plain `spring-boot-starter-parent:2.7.18` is
resolved with the same dependencies to show the difference.

## Limitations

* Resolution is verified, not behaviour: the Boot 2.7.18 test suite against these versions is T-4.4 of the workspace plan.
* The BOM is not on any repository yet (publication is a human gate).
* Gradle does not apply Maven `<exclusions>` from a BOM (see the example).
