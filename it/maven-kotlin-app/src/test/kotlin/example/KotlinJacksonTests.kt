/*
 * Copyright 2026 the ltsboot contributors.
 * SPDX-License-Identifier: Apache-2.0
 */
package example

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

data class Person(val name: String, val age: Int, val nick: String? = null)

class KotlinJacksonTests {

    @Test
    fun kotlinDataClassRoundTrip() {
        val mapper: ObjectMapper = jacksonObjectMapper()
        val json = mapper.writeValueAsString(Person("ada", 36))
        assertThat(json).contains("\"name\":\"ada\"")
        // constructor parameter names, nullability and the default value come from the Kotlin module
        val back: Person = mapper.readValue("""{"name":"bob","age":41}""")
        assertThat(back).isEqualTo(Person("bob", 41, null))
        assertThat(com.fasterxml.jackson.databind.cfg.PackageVersion.VERSION.toString()).isEqualTo("2.18.12")
    }
}
