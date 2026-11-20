/*
 * Copyright 2026 the ltsboot contributors.
 * SPDX-License-Identifier: Apache-2.0
 */
package example;

import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;
import org.junit.jupiter.api.Test;
import org.slf4j.LoggerFactory;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Regression test (T-4.5.7): with slf4j 1.7 + logback 1.2 (Boot 2.7 starter-logging) both an slf4j call and a
 * log4j-api call (routed by log4j-to-slf4j) must reach a logback appender. With slf4j-api 2.x on the classpath
 * logback 1.2 finds no provider and logging goes to a NOP logger: the list stays empty.
 */
class LoggingBridgeTests {

	@Test
	void slf4jAndLog4jApiCallsReachLogback() {
		assertThat(LoggerFactory.getILoggerFactory().getClass().getName()).isEqualTo("ch.qos.logback.classic.LoggerContext");
		Logger root = (Logger) LoggerFactory.getLogger(org.slf4j.Logger.ROOT_LOGGER_NAME);
		ListAppender<ILoggingEvent> appender = new ListAppender<>();
		appender.start();
		root.addAppender(appender);
		try {
			LoggerFactory.getLogger("via.slf4j").info("hello {}", "slf4j");
			org.apache.logging.log4j.LogManager.getLogger("via.log4j").info("hello {}", "log4j");
			assertThat(appender.list).extracting(ILoggingEvent::getFormattedMessage)
					.containsExactly("hello slf4j", "hello log4j");
			assertThat(appender.list).extracting(ILoggingEvent::getLoggerName).containsExactly("via.slf4j", "via.log4j");
		}
		finally {
			root.detachAppender(appender);
		}
	}

}
