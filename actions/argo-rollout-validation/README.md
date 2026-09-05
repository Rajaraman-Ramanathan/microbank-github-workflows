# Argo Rollout Validation

Reusable composite GitHub Action for validating an Argo Rollout before a
release workflow permits the production rollout to continue.

The action is intentionally **validation-only**.

It does not:

- deploy an application;
- modify a Rollout;
- promote a Rollout;
- change canary weights;
- manipulate Istio traffic;
- execute `kubectl argo rollouts promote`.

Those responsibilities remain with Argo CD, Argo Rollouts, and Istio.

---

## Purpose

The release workflow uses this action after the production GitOps deployment
has been reconciled and the Argo Rollout has started the configured canary.

The action verifies:

1. Kubernetes connectivity.
2. The expected Argo Rollout exists.
3. The Rollout is not degraded.
4. The configured container image matches the expected repository.
5. The configured container image uses the expected immutable SHA-256 digest.
6. The optional expected Rollout phase is satisfied.

The action does not decide the canary percentage or rollout strategy.

Those are defined by the Argo Rollout resource in the GitOps repository.

---

## Inputs

### `namespace`

Required.

Kubernetes namespace containing the Argo Rollout.

Example:

```text
prod