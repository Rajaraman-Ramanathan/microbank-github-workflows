# JAR Verification

Validates a Java JAR artifact before it is consumed by downstream CI/CD
stages such as artifact publication or Docker image construction.

The action verifies the JAR structure, optionally validates the expected
Spring Boot executable JAR layout, calculates a SHA-256 checksum, and can
optionally compare the calculated checksum against an expected value.

## Purpose

The JAR verification action establishes a validation boundary between the
Maven build artifact and downstream consumers.

The intended artifact flow is:

Maven Build
    ↓
JAR Verification
    ↓
Upload Build Artifact
    ↓
Download Build Artifact
    ↓
JAR Verification
    ↓
Docker Build / Artifact Publication

The action can therefore be used both:

1. Immediately after Maven creates the JAR.
2. After the JAR is downloaded by a downstream workflow job.

## Responsibilities

This action is responsible for:

- Verifying that the JAR exists.
- Verifying that the JAR is not empty.
- Verifying that Java and the JAR tooling are available.
- Verifying that the JAR is a readable archive.
- Verifying that `META-INF/MANIFEST.MF` exists and is not empty.
- Optionally verifying the expected Spring Boot executable JAR structure.
- Calculating a SHA-256 checksum.
- Generating a checksum file.
- Optionally comparing the calculated checksum with an expected SHA-256 value.
- Exposing the verified JAR and checksum information as action outputs.

## Non-Responsibilities

This action does not:

- Build the application.
- Run Maven.
- Install Java.
- Upload workflow artifacts.
- Download workflow artifacts.
- Publish artifacts to JFrog or another artifact repository.
- Build Docker images.
- Push Docker images.

The calling workflow is responsible for orchestration and artifact
movement between CI/CD stages.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `jar-path` | Yes | — | Path to the JAR artifact to verify. |
| `checksum-path` | No | `<jar-path>.sha256` | Path where the SHA-256 checksum file will be generated. |
| `expected-sha256` | No | `""` | Expected SHA-256 checksum. When provided, the calculated checksum must match it. |
| `verify-spring-boot` | No | `"true"` | Whether to verify the expected Spring Boot executable JAR structure. |

## Outputs

| Output | Description |
|---|---|
| `jar-file` | Absolute path to the verified JAR. |
| `sha256` | SHA-256 checksum of the verified JAR. |
| `checksum-file` | Absolute path to the generated SHA-256 checksum file. |

## Validation

### 1. JAR existence

The action verifies that the configured path points to a regular file.

```bash
[[ -f "$JAR_PATH" ]]