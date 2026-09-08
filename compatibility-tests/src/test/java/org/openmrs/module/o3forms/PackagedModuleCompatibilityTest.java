/*
 * This Source Code Form is subject to the terms of the Mozilla Public License,
 * v. 2.0. If a copy of the MPL was not distributed with this file, You can
 * obtain one at http://mozilla.org/MPL/2.0/. OpenMRS is also distributed under
 * the terms of the Healthcare Disclaimer located at http://openmrs.org/license.
 *
 * Copyright (C) OpenMRS Inc. OpenMRS is a registered trademark and the OpenMRS
 * graphic logo is a trademark of OpenMRS Inc.
 */
package org.openmrs.module.o3forms;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;

import org.junit.BeforeClass;
import org.junit.Test;
import org.openmrs.module.ModuleUtil;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class PackagedModuleCompatibilityTest {

	private static final String PATIENT_DOCUMENTS_MINIMUM = "2.3.0";

	private static String reactorVersion;

	private static String packagedVersion;

	@BeforeClass
	public static void readActualPackagedModule() throws Exception {
		Path root = Paths.get(System.getProperty("o3forms.root"));
		try (InputStream input = Files.newInputStream(root.resolve("pom.xml"))) {
			reactorVersion = childText(parse(input).getDocumentElement(), "version");
		}
		assertNotNull("Root reactor version must be explicit", reactorVersion);
		Path artifact = root.resolve("omod/target/o3forms-" + reactorVersion + ".omod");
		assertTrue("Run the complete reactor package before the compatibility tests", Files.isRegularFile(artifact));
		try (ZipFile archive = new ZipFile(artifact.toFile())) {
			ZipEntry descriptor = archive.getEntry("config.xml");
			assertNotNull("Packaged OMOD must contain config.xml", descriptor);
			try (InputStream input = archive.getInputStream(descriptor)) {
				Element module = parse(input).getDocumentElement();
				assertEquals("o3forms", childText(module, "id"));
				packagedVersion = childText(module, "version");
			}
		}
		assertNotNull("Packaged descriptor must declare a version", packagedVersion);
	}

	private static Document parse(InputStream input) throws Exception {
		DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
		// OpenMRS descriptors contain a DOCTYPE; never resolve its remote DTD.
		factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
		factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
		factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
		factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
		factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
		factory.setXIncludeAware(false);
		factory.setExpandEntityReferences(false);
		return factory.newDocumentBuilder().parse(input);
	}

	private static String childText(Element parent, String name) {
		for (Node child = parent.getFirstChild(); child != null; child = child.getNextSibling()) {
			if (child instanceof Element && name.equals(child.getNodeName())) {
				return child.getTextContent().trim();
			}
		}
		return null;
	}

	@Test
	public void usesTheActualDeployedCoreComparator() throws Exception {
		Properties properties = new Properties();
		try (InputStream input = ModuleUtil.class.getResourceAsStream(
		    "/META-INF/maven/org.openmrs.api/openmrs-api/pom.properties")) {
			assertNotNull("The comparator must come from the real OpenMRS API artifact", input);
			properties.load(input);
		}
		assertEquals("2.8.8", properties.getProperty("version"));
		assertEquals("openmrs-api", properties.getProperty("artifactId"));
	}

	@Test
	public void packagedVersionMatchesReactorVersion() {
		assertEquals(reactorVersion, packagedVersion);
	}

	@Test
	public void packagedVersionSatisfiesPatientDocumentsMinimum() {
		// Core's module startup uses compareVersion, not the qualifier-ignoring helpers.
		assertTrue("The packaged O3 Forms must satisfy Patient Documents' actual minimum",
		    ModuleUtil.compareVersion(packagedVersion, PATIENT_DOCUMENTS_MINIMUM) >= 0);
	}

	@Test
	public void reproducesRejectedPublishedVersion() {
		assertTrue(ModuleUtil.compareVersion("2.3.0-sihsalus.1", PATIENT_DOCUMENTS_MINIMUM) < 0);
	}

	@Test
	public void correctedQualifierDoesNotClaimFinalReleaseCompatibility() {
		assertTrue(ModuleUtil.compareVersion("2.3.1-sihsalus.1", "2.3.1") < 0);
	}

	@Test
	public void upstreamVersionSatisfiesItsOwnMinimum() {
		assertEquals(0, ModuleUtil.compareVersion("2.3.0", PATIENT_DOCUMENTS_MINIMUM));
	}

	@Test
	public void lowerVersionCannotSatisfyMinimum() {
		assertTrue(ModuleUtil.compareVersion("2.2.9", PATIENT_DOCUMENTS_MINIMUM) < 0);
	}
}
