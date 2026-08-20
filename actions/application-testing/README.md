# Application Testing

Performs a lightweight HTTP health/smoke test against a deployed
application.

The action is intended for deployment validation after GitOps/ArgoCD has
reconciled a new application version.

## Purpose

The action verifies that the deployed application is reachable and returns
the expected HTTP status.

For the Microbank Spring Boot services, the default endpoint is:

```text
/actuator/health