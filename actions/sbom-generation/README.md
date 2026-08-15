# SBOM Generation

Generates a Software Bill of Materials (SBOM) for a locally built
container image using Trivy.

The action produces a machine-readable inventory of the software
components contained within the image.

## Purpose

The SBOM Generation action establishes the software-inventory boundary
for the container artifact.

The intended flow is:

    Docker Build
        ↓
    Container Verification
        ↓
    Container Scan
        ↓
    SBOM Generation
        ↓
    Security Gate
        ↓
    Docker Publish

The SBOM is generated from the exact local container image that has
already been verified and scanned.

## Responsibilities

This action is responsible for:

- Validating that Docker is available.
- Validating that the target image exists locally.
- Preparing the SBOM output directory.
- Setting up the approved Trivy version.
- Generating a CycloneDX JSON SBOM.
- Optionally generating an SPDX JSON SBOM.
- Verifying that generated SBOM files exist.
- Verifying that generated SBOM files are non-empty.
- Exposing generated SBOM locations.

## Non-Responsibilities

This action does not:

- Build the container image.
- Build the Java application.
- Verify the JAR.
- Perform vulnerability gating.
- Push the image to ECR.
- Publish the JAR to JFrog.
- Sign the image.
- Create an SBOM attestation.
- Promote the image.
- Deploy the application.

These responsibilities belong to other actions or workflow stages.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `image` | Yes | — | Local container image reference. |
| `report-directory` | No | `.github/reports` | Directory where SBOM files are generated. |
| `generate-cyclonedx` | No | `true` | Whether to generate a CycloneDX JSON SBOM. |
| `generate-spdx` | No | `false` | Whether to generate an SPDX JSON SBOM. |
| `trivy-version` | No | `0.72.0` | Approved Trivy CLI version. |

## Outputs

| Output | Description |
|---|---|
| `cyclonedx-file` | Absolute path to the generated CycloneDX SBOM. |
| `spdx-file` | Absolute path to the generated SPDX JSON SBOM. |

## SBOM Formats

### CycloneDX

CycloneDX JSON is the default SBOM format.

The generated file is:

    container-sbom.cdx.json

CycloneDX is suitable for software-component inventory, dependency
analysis, and supply-chain tooling.

### SPDX

SPDX JSON generation is optional.

The generated file is:

    container-sbom.spdx.json

SPDX can be enabled when a downstream enterprise platform or compliance
process specifically requires it.

## Default Policy

The action generates:

    CycloneDX JSON

and does not generate SPDX unless explicitly requested.

This avoids producing multiple equivalent reports when only one format
is required by downstream tooling.

## Usage

```yaml
- name: Generate Container SBOM
  id: sbom
  uses: ./.github/actions/sbom-generation
  with:
    image: ${{ steps.docker-build.outputs.image }}