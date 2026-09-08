"""Synthetic release-guard tests: no network access, tags, pushes or publication."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from verify_release import REPOSITORY, maven_versions, verify_artifact, verify_identity

VERSION = "2.3.1-sihsalus.1"
SHA = "a" * 40


class ReleaseIdentityTest(unittest.TestCase):
    def verify(self, **overrides):
        arguments = dict(
            repository=REPOSITORY, tag=VERSION, head=SHA, tag_commit=SHA,
            maintenance_head=SHA, versions=[VERSION] * 4, dirty="",
        )
        arguments.update(overrides)
        verify_identity(**arguments)

    def test_accepts_exact_clean_maintenance_head(self):
        self.verify()

    def test_accepts_future_positive_patch_and_qualifier_numbers(self):
        for tag in ("2.3.1-sihsalus.2", "2.3.2-sihsalus.1", "2.3.10-sihsalus.12"):
            with self.subTest(tag=tag):
                self.verify(tag=tag, versions=[tag] * 4)

    def test_rejects_reusing_the_incompatible_minimum_version_series(self):
        for tag in ("2.3.0-sihsalus.1", "2.3.0-sihsalus.2"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "tag"):
                self.verify(tag=tag, versions=[tag] * 4)

    def test_rejects_upstream_repository(self):
        with self.assertRaisesRegex(ValueError, "repository"):
            self.verify(repository="openmrs/openmrs-module-o3forms")

    def test_rejects_unrelated_or_unsafe_tags(self):
        for tag in ("3.0.0", "2.3.0", "2.3.1", "2.3.1-SNAPSHOT", "2.3.1-sihsalus.0",
                    "2.3.01-sihsalus.1", "2.3.1-sihsalus.01", "2.4.1-sihsalus.1", "--help", VERSION + "\n"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "tag"):
                self.verify(tag=tag)

    def test_rejects_malformed_source_commit(self):
        with self.assertRaisesRegex(ValueError, "source commit"):
            self.verify(head="main")

    def test_rejects_tag_pointing_to_another_commit(self):
        with self.assertRaisesRegex(ValueError, "checked-out source"):
            self.verify(tag_commit="b" * 40)

    def test_rejects_stale_maintenance_head(self):
        with self.assertRaisesRegex(ValueError, "maintenance branch head"):
            self.verify(maintenance_head="b" * 40)

    def test_rejects_dirty_checkout(self):
        for dirty in (" M pom.xml", "?? unexpected-file"):
            with self.subTest(dirty=dirty), self.assertRaisesRegex(ValueError, "source changes"):
                self.verify(dirty=dirty)

    def test_rejects_any_mismatched_reactor_version(self):
        for index in range(4):
            versions = [VERSION] * 4
            versions[index] = "2.3.0"
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "Maven versions"):
                self.verify(versions=versions)

    def test_rejects_missing_reactor_version(self):
        with self.assertRaisesRegex(ValueError, "Maven versions"):
            self.verify(versions=[VERSION] * 3)

    def test_reads_the_real_reactor_versions(self):
        self.assertEqual(maven_versions(Path(__file__).resolve().parent.parent), [VERSION] * 4)


class ReleaseArtifactTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / f"o3forms-{VERSION}.omod"

    def artifact(self, version=VERSION, module_id="o3forms", descriptor=True):
        with zipfile.ZipFile(self.path, "w") as artifact:
            if descriptor:
                artifact.writestr("config.xml", f"<module><id>{module_id}</id><version>{version}</version></module>")

    def test_accepts_expected_descriptor(self):
        self.artifact()
        verify_artifact(self.path, VERSION)

    def test_rejects_wrong_packaged_version(self):
        self.artifact(version="2.3.0")
        with self.assertRaisesRegex(ValueError, "version"):
            verify_artifact(self.path, VERSION)

    def test_rejects_wrong_packaged_module(self):
        self.artifact(module_id="another-module")
        with self.assertRaisesRegex(ValueError, "identity"):
            verify_artifact(self.path, VERSION)

    def test_rejects_missing_descriptor(self):
        self.artifact(descriptor=False)
        with self.assertRaisesRegex(ValueError, "descriptor"):
            verify_artifact(self.path, VERSION)

    def test_rejects_wrong_filename(self):
        with self.assertRaisesRegex(ValueError, "filename"):
            verify_artifact(self.path.with_name("another.omod"), VERSION)


if __name__ == "__main__":
    unittest.main()
