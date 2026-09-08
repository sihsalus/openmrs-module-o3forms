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
publication is intentionally unconfigured in this branch, including removal of
the upstream deployment destinations. Publishing requires a separate decision
on the registry, the approved commit and the release process. After publication
and validation, infrastructure may consume the immutable module version through
its normal dependency configuration, without embedding Java source or patches.

## REST APIS

### O3 Form Schema

This feature allows the frontend to request an O3 form and receive a form object that has:

* All referenced forms loaded into the appropriate parts of the main form
* All translations provided in a translation file for the appropriate locale
* Metadata about concepts used in the forms

The goal of this feature is to reduce the overall traffic between a browser and the OpenMRS server involved in loading a form.

#### Retrieve a complete form

```http request
GET /ws/rest/v1/o3/forms/<NAME_OR_UUID>
```

| URL Parameter  | Type     | Description                                         |
|:---------------|:---------|:----------------------------------------------------|
| `NAME_OR_UUID` | `string` | Either the name or UUID of the form to be displayed |

| Query Parameter            | Type      | Description                                                                              |
|:---------------------------|:----------|:-----------------------------------------------------------------------------------------|
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
