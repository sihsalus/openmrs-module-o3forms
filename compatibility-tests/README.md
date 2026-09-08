# Packaged module compatibility tests

This standalone Maven project checks the built OMOD with the **actual OpenMRS
Core 2.8.8 `ModuleUtil.compareVersion`** implementation used during dependent
module startup. It does not copy or reimplement the comparator.

From the repository root, with JDK 21:

```sh
mvn --batch-mode --no-transfer-progress -Dformatter.skip=true -Dimpsort.skip=true clean verify
mvn --batch-mode --no-transfer-progress -f compatibility-tests/pom.xml clean verify
```

The second command requires the first command's packaged OMOD. Tests read the
root reactor version and the corresponding archive's `config.xml`, fail if the
archive is absent or mismatched, and check the Patient Documents minimum `2.3.0`.
Negative controls retain the rejected `2.3.0-sihsalus.1` case and show that the
replacement qualifier does not satisfy a future minimum of final `2.3.1`.

The pinned OpenMRS API, Commons Lang and SLF4J dependencies match Core 2.8.8;
they and JUnit are **test-only**. This project is not a runtime reactor module,
is not included in the OMOD and must not be published. It has no application
sources and does not start OpenMRS, connect to a database or access patients.
XML parsing never fetches the module descriptor's external DTD.

Both the PR build and the tag-only release build run these tests before
retaining or attesting the OMOD. Passing this check establishes the version
ordering contract, not actual dependent-module startup or clinical acceptance.
Those still require coordinated DEV/QLTY validation with synthetic fixtures and
verified cleanup after an explicitly authorized release and image deployment.
