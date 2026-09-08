# O3 Forms

## Description

This module provides REST APIs to provide backend services for O3-style forms

## Requirements

This module requires OpenMRS 2.6.0 or higher and the webservices.rest module 2.40.0 or higher.

## SIH Salus maintenance branch

`sihsalus/2.3.x` starts at upstream tag `2.3.0`
(`34733b3b909e8e35456c9afa7d643cc22c52bb91`). It deliberately does not include
the dependency upgrades in upstream's newer branches.

The candidate version is `2.3.0-sihsalus.1`. Translation selection skips null
entries in the preferred locale set without modifying that set or its order.
When no configured locale has a matching translation, no translation entries are
added (the API returns an empty translations map). The patch does not invent a
language fallback or repair OpenMRS's locale caches.

Build and run the full test suite with Maven and JDK 21:

```sh
mvn --batch-mode --no-transfer-progress -Dformatter.skip=true -Dimpsort.skip=true clean verify
```

The `java21-tests` profile automatically opens the JDK packages required by the
legacy test dependencies, only in the forked test JVM. Java 8 bytecode targets
and runtime dependencies are unchanged. The profile preserves the JaCoCo agent
and also supports `-Djacoco.skip=true`. Tests use synthetic fixtures in a local
in-memory database; do not test this candidate against real patients or production.

The build command skips the inherited automatic formatters to avoid rewriting
unrelated legacy sources. It does not skip any tests, compilation or packaging.

Java source, regression tests and OMOD compilation belong in this module
repository. CI only builds/tests and retains short-lived review artifacts;
it does not publish a release, deploy a module or restart a server. Maven
publication remains unconfigured, including removal of upstream deployment
destinations. The SIH Salus distribution consumes a published OMOD from a public
immutable GitHub Release, pinned by exact version and SHA256. No module source,
patch or OMOD compilation belongs in the infrastructure repository.

### Authorized release process

Publishing requires explicit maintainer authorization for the exact approved
commit. DEV/QLTY acceptance and deployment are separate gates; a passing module
build is not clinical validation and does not authorize production use.

1. Review and merge the focused PR into `sihsalus/2.3.x`, then wait for its
   exact merge-head CI to pass. Do not change the upstream-derived `main` branch
   or use its inherited release workflow.
2. An administrator must enable and verify release immutability for this fork
   before publication (`GET /repos/sihsalus/openmrs-module-o3forms/immutable-releases`
   must return `enabled: true`). If necessary, enabling it uses `PUT` on that
   same endpoint with repository Administration write permission. Do not change
   organization-wide settings or introduce an administrator token in CI.
3. Create and push the exact version tag (for example `2.3.0-sihsalus.1`) at the
   approved maintenance head. Never move or replace a release tag. The tag-only
   `release-sihsalus.yml` workflow rejects wrong repositories, stale heads, dirty
   sources, version mismatches and unexpected packaged module identities. It
   rebuilds and tests with JDK 21, then produces an OMOD, SHA256, provenance JSON
   and a signed GitHub artifact-attestation bundle. It cannot publish releases:
   its only write permissions are for OIDC and attestations.
4. Wait for that exact tag run to succeed and download its `o3forms-release-...`
   artifact to a fresh temporary directory with `gh run download`. Verify the
   checksum with `sha256sum --check o3forms-<version>.omod.sha256` (or
   `shasum -a 256 --check` on macOS). Verify provenance with
   `gh attestation verify`, restricting the repository, signer workflow, source
   ref and source digest to the approved values:

   ```sh
   gh attestation verify o3forms-<version>.omod \
     --repo sihsalus/openmrs-module-o3forms \
     --signer-workflow sihsalus/openmrs-module-o3forms/.github/workflows/release-sihsalus.yml \
     --source-ref refs/tags/<version> --source-digest <approved-commit>
   ```

   Check the manifest and source SHA against the approved run; do not substitute
   a local build, PR artifact, older run, or an artifact from another repository.

5. Recheck release immutability. Using a maintainer credential with Contents
   write permission, create a **draft** release with `gh release create`, the
   exact version and all four exact asset paths, and the flags `--verify-tag`,
   `--draft`, `--prerelease`, `--latest=false` and
   `--repo sihsalus/openmrs-module-o3forms`. Supply reviewed notes describing the
   patch, upstream base, exact source and build run, and pending DEV/QLTY validation.
   Verify all assets before publishing with `gh release edit <version> --draft=false --latest=false --repo sihsalus/openmrs-module-o3forms`.
   Check that the release API returns `immutable: true`, and download and verify
   the published OMOD again. Never overwrite assets or reuse this version for a fix.
   Keep `prerelease: true` and `latest: false` until DEV and QLTY acceptance passes
   and a maintainer explicitly approves stable promotion.
6. Infrastructure may consume the exact public release URL and SHA256 through
   its normal image build. Rollback selects the previously verified backend image;
   it does not copy an OMOD into a running server. Coordinate DEV first, and QLTY
   only after DEV acceptance passes, with synthetic data and recoverable cleanup.

Release-guard unit tests are read-only except for disposable synthetic ZIP
fixtures and do not call GitHub, create tags or publish anything:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

## REST APIS

### O3 Form Schema

This feature allows the frontend to request an O3 form and receive a form object that has:

- All referenced forms loaded into the appropriate parts of the main form
- All translations provided in a translation file for the appropriate locale
- Metadata about concepts used in the forms

The goal of this feature is to reduce the overall traffic between a browser and the OpenMRS server involved in loading a form.

#### Retrieve a complete form

```http request
GET /ws/rest/v1/o3/forms/<NAME_OR_UUID>
```

| URL Parameter  | Type     | Description                                         |
| :------------- | :------- | :-------------------------------------------------- |
| `NAME_OR_UUID` | `string` | Either the name or UUID of the form to be displayed |

| Query Parameter            | Type      | Description                                                                              |
| :------------------------- | :-------- | :--------------------------------------------------------------------------------------- |
| `includeConceptReferences` | `boolean` | Whether or not to include the conceptReferences object. Defaults to true.                |
| `v`                        | `string`  | REST API-style formatting for the conceptReferences. Defaults to `custom:(uuid,display)` |

If the form exists and everything process correctly, you should get a response like:

```http response
HTTP/1.1 200 OK
Cache-Control: no-cache; private
Content-Type: application/json;charset=UTF-8
Etag: "<some value>"

<JSON Content>
```

Other responses will be returned as appropriate. The API will return a 404 with an explanation if the form cannot be found
or the referenced form does not have the appropriate form resources associated with it.

If an error occurs either generating the translations section or the concept references (if requested), those elements will
simply not be present and appropriate messages will log to the backend. This is to ensure that we don't have form failures
just due to issues with translations or concepts. It is assumed that the consuming application will take appropriate action
if these elements do not exist.
