# GitOps Helm Validation

Validates and renders the Helm chart used by a service-specific
GitOps repository.

## Purpose

The action:

1. Reads the GitOps repository contract.
2. Locates the configured Helm chart.
3. Runs `helm lint`.
4. Locates the values file for every declared environment.
5. Renders the chart for every environment.
6. Writes the rendered manifests to the configured output directory.

The action does not perform Kubernetes schema or policy validation.

## Inputs

### `service-name`

Required.

The microservice represented by the GitOps repository.

Example:

```yaml
with:
  service-name: account