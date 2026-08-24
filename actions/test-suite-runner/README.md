# Test Suite Runner

Runs an application-specific automated test suite from a dedicated test
repository against a deployed application environment.

This action is designed for use by the reusable release workflow and keeps
test implementation separate from the centralized GitHub Actions workflow
repository.

The action does not implement integration or system testing itself. Instead,
it checks out the application's dedicated test repository at the requested
Git reference and invokes the standardized test repository contract.

---

## Purpose

The Microbank platform uses a dedicated automated testing repository for each
application.

A test repository may contain multiple test suites, for example:

- integration
- system
- regression
- smoke
- other application-specific automated tests

The reusable workflow decides **which suite to execute** while the test
repository owns the actual test implementation.

For example:

```text
microbank-account-service-tests
│
├── scripts/
│   └── run-tests.sh
│
├── integration/
├── system/
├── regression/
├── smoke/
└── test-results/