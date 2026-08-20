# GitOps Image Update

Updates the immutable container image digest for a microservice in the
Microbank GitOps repository, commits the change, and pushes it to the
specified environment branch.

## Purpose

This action is used by release workflows to promote a previously verified
container image through GitOps.

The action updates only:

```text
environments/<environment>/<service-directory>/values.yaml