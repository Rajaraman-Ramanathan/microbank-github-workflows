# ECR Image Promotion

Promotes an approved and signed container image from a DEV Amazon ECR
repository to a STAGE Amazon ECR repository in a different AWS account.

The action is designed for enterprise release pipelines where:

- DEV and STAGE use separate AWS accounts.
- Both environments use the same AWS region.
- The image is built only once.
- The image is identified by an immutable SHA-256 digest.
- The image is signed before promotion.
- The exact signed artifact is promoted to STAGE.
- The destination image digest must match the source digest.
- The Cosign signature must remain verifiable after promotion.

## Promotion model

```text
DEV AWS Account
──────────────────────────────

ECR
└── microbank/account-service
    ├── image
    │   └── sha256:ABC...
    │
    └── Cosign signature
              │
              │
              │ cross-account promotion
              ▼
STAGE AWS Account
──────────────────────────────

ECR
└── microbank/account-service
    ├── image
    │   └── sha256:ABC...
    │
    └── Cosign signature