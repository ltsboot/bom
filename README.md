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

## Gradle

Three ways to apply the BOM; all three were verified (`it/gradle-consumers/verify.sh`, Gradle 7.6.3, JDK 8) and run against the six
compat apps (`state/compat/T-4.5-ltsbom.md` of the ltsboot workspace):

| How | Versions in conflict with a transitive request | Use it when |
|---|---|---|
| `io.spring.dependency-management` + `mavenBom('io.github.ltsboot:lts-dependencies:2.7.18.1')` | **The managed version wins** (same as Maven and as Boot's own plugin behaviour). Override with `ext['jackson-bom.version'] = ...` / `gradle.properties`. | Boot Gradle plugin users (recommended; the compat apps use it). |
| `implementation enforcedPlatform('io.github.ltsboot:lts-dependencies:2.7.18.1')` | The managed version wins. | No dependency-management plugin, but the Boot-style "managed wins" semantics. |
| `implementation platform('io.github.ltsboot:lts-dependencies:2.7.18.1')` | **The highest version wins**, so a library that requests a newer version than the BOM manages evicts the managed one (see "Behaviour changes", Gradle). | Libraries and Java apps; `examples/gradle-platform/` (verified on 7.6.3). **Not for Kotlin 1.6 modules**: `jackson-databind` 2.18's Gradle metadata re-imports `jackson-bom` 2.18.12 (evicting the `jackson-module-kotlin` 2.17.3 pin) and `jackson-module-kotlin` pulls Kotlin 1.8 stdlib: the `webflux-kotlin-coroutines` app fails to compile in this mode (and passes in the other two). |

Gradle applies the Maven `<exclusions>` the BOM declares on an entry (the `mchange-commons-java` exclusion on Quartz works with a plain
`platform(...)`).

**One Gradle-only rule is required in every mode** for Kafka (`kafka-clients`) and Elasticsearch users: `lz4-java` moved to the groupId `at.yawk.lz4`
(ADR-004) and the new artifact declares the old capability `org.lz4:lz4-java`, so without a selection Gradle fails with "Cannot select module with
conflict on capability 'org.lz4:lz4-java'". A BOM cannot carry this rule; put it in the build (the compat apps' Gradle builds carry it):

```kotlin
configurations.configureEach {
    resolutionStrategy.capabilitiesResolution.withCapability("org.lz4:lz4-java") {
        val maintained = candidates.firstOrNull { (it.id as? org.gradle.api.artifacts.component.ModuleComponentIdentifier)?.group == "at.yawk.lz4" }
        if (maintained != null) select(maintained)
    }
}
```
(Groovy: `examples/gradle-platform/build.gradle`.) Maven needs nothing: the managed `org.lz4:lz4-java:1.8.1` is a relocation POM.

## What changes (defaults)

| Library | Boot 2.7.18 | lts-bom | Property |
|---|---|---|---|
| Spring Framework | 5.3.31 | 5.3.39 | `spring-framework.version` |
| Spring Security | 5.7.11 | 5.7.14 | `spring-security.version` |
| Reactor BOM | 2020.0.38 | 2020.0.47 | `reactor-bom.version` |
| Spring LDAP | 2.4.1 | 2.4.4 | `spring-ldap.version` |
| Tomcat | 9.0.83 | 9.0.124 | `tomcat.version` |
| Netty | 4.1.101.Final | 4.1.141.Final | `netty.version` |
| Undertow / XNIO | 2.2.28.Final / 3.8.7 | 2.2.41.Final / 3.8.14.Final (T-4.5.15: 3.8.15+ hangs on a failed bind) | `undertow.version`, `xnio.version` (new) |
| Jetty | 9.4.53 | 9.4.58.v20250814 | `jetty.version` |
| Jackson | 2.13.5 | 2.18.12 | `jackson-bom.version` |
| jackson-module-kotlin | 2.13.5 | **2.17.3** (not 2.18.12) | `jackson-module-kotlin.version` (new) |
| ActiveMQ | 5.16.7 | 5.16.8 (Java 8) | `activemq.version` |
| RabbitMQ amqp-client | 5.14.3 | 5.38.0 | `rabbit-amqp-client.version` |
| Elasticsearch | 7.17.15 | 7.17.29 | `elasticsearch.version` |
| Thymeleaf (+ springsecurity5, layout dialect) | 3.0.15 (3.0.5, 3.0.0) | 3.1.7 (3.1.7, 3.4.0) | `thymeleaf.version`, `thymeleaf-extras-springsecurity.version`, `thymeleaf-layout-dialect.version` |
| SnakeYAML | 1.30 | 1.33 | `snakeyaml.version` |
| Log4j2 / Logback | 2.17.2 / 1.2.12 | 2.25.5 / 1.2.13 | `log4j2.version`, `logback.version` |
| log4j-to-slf4j (the bridge in `spring-boot-starter-logging`) | 2.17.2 | **2.21.1** (not 2.25.5) | `log4j-to-slf4j.version` (new) |
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
| `activemq.version` | `5.19.12` | Fixes 11 more high CVEs (incl. KEV CVE-2026-34197). **Needs Java 11.** On Java 8, apply the controls in `docs/mitigations/activemq-5.16.md` (workspace) |
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

## Behaviour changes for consumers

Everything here follows from a deliberate version bump (ADR-004) or from how Maven/Gradle resolve versions. "Verified" means a test in
`it/` or in the compat apps ran against these POMs; nothing here needs a version-forcing script.

**Fixed in the BOM (no action needed)**

* **Logging (slf4j 1.7 + logback 1.2 stay the Boot 2.7 line).** `log4j-api`/`-core` are bumped to 2.25.5 (the CVEs are there), but
  `log4j-to-slf4j` 2.22+ *declares* `slf4j-api` 2.0.x. Maven keeps the managed 1.7.36 and still works; Gradle resolves the declared 2.0.x
  (highest wins), logback 1.2 then finds no SLF4J provider and logging **silently stops**. The BOM therefore pins the bridge to 2.21.1, the last
  release that declares `slf4j-api` 1.7.36 (`log4j-to-slf4j.version`). Verified in Maven and in all three Gradle modes: an slf4j call and a
  `log4j-api` call both reach a logback appender (`it/maven-logging-app`, `it/gradle-consumers`). `spring-boot-starter-log4j2` is unaffected
  (`log4j-slf4j-impl` 2.25.5 declares slf4j 1.7). **Logback 1.3/1.5 is evaluated, not offered:** they need slf4j 2.x and fix the Logback CVEs that the 1.2 line
  cannot get; **stock Boot 2.7.18 cannot use them**: with `logback.version` 1.3.16 + `slf4j.version` 2.0.17 + `log4j-to-slf4j.version` 2.25.5 every Spring context of the
  `web-mvc-actuator` app fails with `ClassNotFoundException: org.slf4j.impl.StaticLoggerBinder` (`state/build-logs/T-4.5-logback13-optin.log`). It would need a Boot fork change
  so the BOM does not offer it; the 6 Logback CVEs fixed only on 1.3/1.5 stay open on the 1.2 line.
* **Kotlin and Jackson.** `jackson-module-kotlin` is pinned to 2.17.3 while Jackson core/databind stay at 2.18.12: 2.18.x ships Kotlin 1.8.0 metadata, and a
  Kotlin 1.6.21 module (the Boot 2.7 line) that merely has it on the classpath fails with "binary version of its metadata is 1.8.0, expected 1.6.0".
  2.17.3 ships 1.7.1 metadata (readable by 1.6.x). Verified: the `webflux-kotlin-coroutines` compat app compiles and passes on Kotlin 1.6.21 in
  Maven and Gradle, and `it/maven-kotlin-app` round-trips a Kotlin data class on databind 2.18.12. If you compile with Kotlin 1.8+, set
  `jackson-module-kotlin.version` to 2.18.12.
* **mchange-commons-java (T-4.5.8).** The exclusion is declared on the `quartz` entry only. c3p0 users keep `mchange-commons-java` (Maven and Gradle verified).
  A blanket `exclude group: 'com.mchange'` breaks c3p0 with `IllegalAccessError`; do not add one. The c3p0/mchange CVEs themselves stay mitigation-only.
* **parsson / jakarta.json (T-4.5.6).** `parsson` 1.0.5 is only a managed version (CVE-2023-7272 fix); the BOM does not add it to any classpath. Boot 2.7
  manages `jakarta.json-api` at 1.1.6 (the `javax.json` namespace) and `spring-boot-starter-data-elasticsearch` brings `elasticsearch-java`, which wants the
  `jakarta.json` 2.x API. Whether the 1.1.6 or the 2.x API wins is decided by the build tool, not by the BOM, and it is identical with Boot 2.7.18's
  own BOM: Maven, `enforcedPlatform` and the dependency-management plugin keep 1.1.6; a plain Gradle `platform()` lets 2.0.x win. Pinning 1.1.6 in the BOM
  would change nothing for plain platforms (verified with a Boot-BOM control build) and removing parsson would reopen the CVE, so neither is done. Rule:
  `javax.json` users must use the dependency-management plugin or `enforcedPlatform`; users of the `elasticsearch-java` client (`jakarta.json`) set
  `jakarta-json.version` to 2.0.2.
* **thymeleaf-layout-dialect 3.4.0 / Groovy 4 (T-4.5.5).** It stays managed (ADR-004: it must move with Thymeleaf 3.1) and brings its own Groovy 4
  (`org.apache.groovy:groovy`); the BOM does not exclude it (the dialect is written in Groovy and breaks without it). Verified: a layout is rendered with
  Thymeleaf 3.1.7 + layout-dialect 3.4.0 + Groovy 4 (`it/maven-layout-app`). The only conflict is an application that also has Groovy 3 (Spock,
  `starter-groovy-templates`): Gradle reports a capability conflict between `org.apache.groovy:groovy` and `org.codehaus.groovy:groovy`, Maven puts both on the
  classpath. Resolve it consciously (select one in `capabilitiesResolution`, or keep `thymeleaf-layout-dialect.version` at Boot's 3.0.0, which uses Groovy 3 and
  rendered the same layout with Thymeleaf 3.1.7 in our test). Thymeleaf itself is out of scope (ADR-008 s.3).

**Gradle: plain `platform()` and managed versions (T-4.5.3).** With a plain `platform()` a library that requests a *higher* version than the BOM manages
wins (Gradle's rule). Example: `io.mockk:mockk:1.13.5` requests `kotlin-stdlib`/`kotlin-reflect` 1.8.20, so a Kotlin 1.6 build stops compiling. That is the same with
Boot 2.7.18's own BOM (verified with a control build); the BOM cannot enforce downgrades. Use the dependency-management plugin or `enforcedPlatform` (managed
1.6.21 wins, verified), or a mockk release declaring Kotlin <= 1.6.21 (1.12.4 resolves to 1.6.21, verified).

**Version bumps that change behaviour (documented, not blocked)**

* **AssertJ 3.27.7 (T-4.5.4, test scope).** `fail(null)` is now ambiguous (new generic `fail(Throwable)`/`fail(String)` overloads); call `fail((String) null)`.
* **jackson-core 2.18.x `StreamReadConstraints` (T-4.5.9).** Maximum nesting depth 1000 (and limits on number/string length): deeply nested JSON that parsed
  on 2.13 is rejected with a different message. Deliberate upstream hardening. Raise it with `JsonFactory.builder().streamReadConstraints(StreamReadConstraints.builder()
  .maxNestingDepth(...).build())` only if you must accept such input.
* **jackson-core 2.18.x is a multi-release jar (T-4.5.2)** with class files up to major 65. Application jars are unaffected, but Gradle TestKit classpath
  instrumentation (all versions up to 8.0.2 tested) fails on it (`Unsupported class file major version`) and can hang the test JVM: only plugin authors running TestKit
  with lts-bom on the TestKit classpath are affected (keep the multi-release jackson-core off the instrumented classpath, or test plugins on a Gradle without that instrumentation).
* **Tomcat 9.0.124 (T-4.5.11).** `RemoteIpValve`'s built-in default for `internalProxies` changed. Spring Boot always applies its own default
  (`server.tomcat.remoteip.internal-proxies`), so Boot applications are unchanged; embedded-Tomcat users without Boot must set it explicitly.
* **Undertow 2.2.41 (T-4.5.12): action may be needed.** `UndertowOptions.DEFAULT_MAX_ENTITY_SIZE` changed from -1 (unlimited) to **2 MB** (2097152). Boot 2.7
  documents `server.undertow.max-http-post-size` = -1 as "unlimited" but only applies **positive** values, so on Undertow 2.2.41 an application that does not
  set it now rejects request entities above 2 MB. Set `server.undertow.max-http-post-size` to the size you need (a positive value: -1 cannot restore
  "unlimited" through the property).
* **amqp-client 5.38.0 (T-4.5.13).** The insecure `TrustEverythingTrustManager` default is gone (CVE-2026-63336), so the "SECURITY ALERT" warning no longer exists and
  `spring.rabbitmq.ssl.validate-server-certificate=false` no longer silently trusts any certificate. Configure a trust store (`spring.rabbitmq.ssl.trust-store`).
* **Log4j2 2.25.x on JDK 8 with `-Werror` (T-4.4).** A log4j annotation carries an `ElementType.MODULE` target; JDK 8 `javac` reports a mandatory
  "unknown enum constant" warning that fails `-Werror` builds. Drop `-Werror` for JDK 8 compiles, or compile with JDK 11+ (`--release 8`). When
  `log4j-core` is on the annotation-processor path, pass `-Alog4j.graalvm.groupId=... -Alog4j.graalvm.artifactId=...` to silence the GraalVM processor.
* **Boot fork only.** Boot's own `SpringBootPropertySource` test trips on the new default method `PropertySource.getPropertyNames()` of log4j2 2.25.x (T-4.5.14);
  no runtime effect for applications.

## Verification (Docker only)

```
it/verify-maven.sh 8     # mvn verify + deploy to it/repo, control / parent / BOM apps, 33 assertions on dependency:tree
it/verify-gradle.sh 17   # Gradle 7.6.3 platform example against it/repo
it/gradle-consumers/verify.sh 8   # Gradle consumers in 3 modes (platform / enforcedPlatform / dependency-management) + a Boot-BOM control
```
`verify-maven.sh` also runs the behaviour ITs (logging bridge reaches logback, Kotlin 1.6.21 + jackson-module-kotlin, layout dialect, c3p0).
Each prints the selected `dependency:tree` / `dependencies` lines. A control app on plain `spring-boot-starter-parent:2.7.18` is
resolved with the same dependencies to show the difference.

## Limitations

* Beyond resolution, behaviour is verified by the ITs above and by the six compat apps (Maven import, Maven parent, Gradle in three modes, JDK 8 and 17); the full
  Boot 2.7.18 suite against these versions is T-4.4 of the workspace plan.
* The BOM is not on any repository yet (publication is a human gate).
* Plain Gradle `platform()` cannot enforce a managed version against a transitive request for a higher one (see "Behaviour changes").
