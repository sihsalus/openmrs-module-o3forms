#!/usr/bin/env python3
"""Read-only, fail-closed checks for an explicitly authorized maintenance tag."""

import argparse
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

REPOSITORY = "sihsalus/openmrs-module-o3forms"
MAINTENANCE_REF = "refs/remotes/origin/sihsalus/2.3.x"
NAMESPACE = {"m": "http://maven.apache.org/POM/4.0.0"}
# Qualifying the minimum 2.3.0 sorts BELOW that minimum in OpenMRS Core.
# Require a positive patch increment; retain tag/head/artifact checks below.
RELEASE_TAG_PATTERN = r"2\.3\.[1-9][0-9]*-sihsalus\.[1-9][0-9]*"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_identity(repository, tag, head, tag_commit, maintenance_head, versions, dirty):
    require(repository == REPOSITORY, "Release repository is not the SIH Salus fork")
    require(re.fullmatch(RELEASE_TAG_PATTERN, tag), "Unexpected release tag")
    require(re.fullmatch(r"[0-9a-f]{40}", head), "Invalid source commit")
    require(head == tag_commit, "Tag does not identify the checked-out source")
    require(head == maintenance_head, "Tag is not the current maintenance branch head")
    require(not dirty, "Tracked or untracked source changes are present")
    require(len(versions) == 4 and all(v == tag for v in versions), "Maven versions do not match the tag")


def maven_versions(root):
    parent = ET.parse(root / "pom.xml").getroot()
    api = ET.parse(root / "api/pom.xml").getroot()
    omod = ET.parse(root / "omod/pom.xml").getroot()
    require(parent.findtext("m:groupId", namespaces=NAMESPACE) == "org.openmrs.module", "Unexpected Maven group")
    require(parent.findtext("m:artifactId", namespaces=NAMESPACE) == "o3forms", "Unexpected Maven artifact")
    dependencies = omod.findall("m:dependencies/m:dependency", NAMESPACE)
    api_dependencies = [
        dependency for dependency in dependencies
        if dependency.findtext("m:groupId", namespaces=NAMESPACE) == "org.openmrs.module"
        and dependency.findtext("m:artifactId", namespaces=NAMESPACE) == "o3forms-api"
    ]
    require(len(api_dependencies) == 1, "Expected exactly one O3 Forms API dependency")
    return [
        parent.findtext("m:version", namespaces=NAMESPACE),
        api.findtext("m:parent/m:version", namespaces=NAMESPACE),
        omod.findtext("m:parent/m:version", namespaces=NAMESPACE),
        api_dependencies[0].findtext("m:version", namespaces=NAMESPACE),
    ]


def verify_artifact(path, tag):
    require(path.name == f"o3forms-{tag}.omod", "Unexpected OMOD filename")
    with zipfile.ZipFile(path) as artifact:
        require(artifact.testzip() is None, "Corrupt OMOD archive")
        require(artifact.namelist().count("config.xml") == 1, "Expected one module descriptor")
        descriptor = ET.fromstring(artifact.read("config.xml"))
        require(descriptor.findtext("id") == "o3forms", "Unexpected module identity")
        require(descriptor.findtext("version") == tag, "Packaged module version does not match the tag")


def git(*arguments):
    return subprocess.check_output(["git", *arguments], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    # Validate the tag before it can become part of a Git revision expression.
    require(re.fullmatch(RELEASE_TAG_PATTERN, args.tag), "Unexpected release tag")
    verify_identity(
        args.repository, args.tag, git("rev-parse", "HEAD"),
        git("rev-parse", f"refs/tags/{args.tag}^{{commit}}"),
        git("rev-parse", MAINTENANCE_REF), maven_versions(Path.cwd()),
        git("status", "--porcelain", "--untracked-files=all"),
    )
    if args.artifact:
        verify_artifact(args.artifact, args.tag)
    print(f"PASSED: {args.tag} matches the clean maintenance head and Maven versions")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ET.ParseError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Release validation failed: {error}") from error
