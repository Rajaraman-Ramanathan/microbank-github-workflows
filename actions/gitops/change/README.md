# GitOps Change Validation

Validates the identity and change scope of pull requests
submitted to a service-specific GitOps repository.

## Purpose

The action distinguishes between:

- Human-generated pull requests
- Application automation pull requests created through the
  approved GitHub App

Application automation is restricted to updating the service's
environment values file and the approved image digest field.

Human pull requests continue through normal repository governance
such as CODEOWNERS and branch protection.

## Inputs

### `service-name`

Required.

The microservice represented by the GitOps repository.

Example:

```yaml
with:
  service-name: account