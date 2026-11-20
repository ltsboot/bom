/*
 * Copyright 2026 the ltsboot contributors.
 * SPDX-License-Identifier: Apache-2.0
 */
package example;

import nz.net.ultraq.thymeleaf.layoutdialect.LayoutDialect;
import org.junit.jupiter.api.Test;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.context.Context;
import org.thymeleaf.templateresolver.ClassLoaderTemplateResolver;

import static org.assertj.core.api.Assertions.assertThat;

class LayoutDialectTests {

	@Test
	void decoratesPageWithLayout() {
		ClassLoaderTemplateResolver resolver = new ClassLoaderTemplateResolver();
		resolver.setPrefix("templates/");
		resolver.setSuffix(".html");
		TemplateEngine engine = new TemplateEngine();
		engine.setTemplateResolver(resolver);
		engine.addDialect(new LayoutDialect());
		String html = engine.process("page", new Context());
		assertThat(html).contains("<h1>Layout</h1>").contains("page content").doesNotContain("default");
	}

}
