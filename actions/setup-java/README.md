# Setup Java

## Purpose

Configures the Java build environment for all Microbank reusable workflows.

## Responsibilities

- Install Java.
- Configure Maven dependency cache.
- Verify Java installation.
- Verify Maven Wrapper.

## Inputs

| Name | Default |
|------|----------|
| java-version | 21 |
| distribution | temurin |
| cache | maven |

## Outputs

None.

## Example

```yaml
- name: Setup Java
  uses: microbank-github-workflows/actions/setup-java@v1
  with:
    java-version: "21"