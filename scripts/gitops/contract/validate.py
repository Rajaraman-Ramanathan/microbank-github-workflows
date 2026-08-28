from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml


EXPECTED_API_VERSION = "gitops.microbank.io/v1alpha1"
EXPECTED_KIND = "GitOpsRepository"

REQUIRED_ENVIRONMENTS = ("dev", "stage", "prod")

REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)

APP_PATH_TEMPLATE = (
    "environments/{environment}/{service}/values.yaml"
)


class ContractValidationError(Exception):
    """Raised when the GitOps repository contract is invalid."""


def fail(message: str) -> None:
    raise ContractValidationError(message)


def require_mapping(
    value: Any,
    path: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{path} must be a mapping.")

    return value


def require_string(
    mapping: dict[str, Any],
    key: str,
    path: str,
) -> str:
    value = mapping.get(key)

    if not isinstance(value, str) or not value.strip():
        fail(f"{path}.{key} must be a non-empty string.")

    return value.strip()


def require_string_list(
    mapping: dict[str, Any],
    key: str,
    path: str,
) -> list[str]:
    value = mapping.get(key)

    if not isinstance(value, list) or not value:
        fail(f"{path}.{key} must be a non-empty list.")

    if not all(isinstance(item, str) and item.strip() for item in value):
        fail(
            f"{path}.{key} must contain only non-empty strings."
        )

    return [item.strip() for item in value]


def validate_contract(
    document: dict[str, Any],
    service_name: str,
) -> dict[str, str]:
    api_version = document.get("apiVersion")

    if api_version != EXPECTED_API_VERSION:
        fail(
            "Invalid apiVersion: "
            f"expected '{EXPECTED_API_VERSION}', "
            f"got '{api_version}'."
        )

    kind = document.get("kind")

    if kind != EXPECTED_KIND:
        fail(
            f"Invalid kind: expected '{EXPECTED_KIND}', "
            f"got '{kind}'."
        )

    metadata = require_mapping(
        document.get("metadata"),
        "metadata",
    )

    metadata_name = require_string(
        metadata,
        "name",
        "metadata",
    )

    if metadata_name != service_name:
        fail(
            "Service identity mismatch: "
            f"workflow input is '{service_name}', "
            f"but metadata.name is '{metadata_name}'."
        )

    spec = require_mapping(
        document.get("spec"),
        "spec",
    )

    source = require_mapping(
        spec.get("source"),
        "spec.source",
    )

    application_repository = require_string(
        source,
        "applicationRepository",
        "spec.source",
    )

    if not REPOSITORY_PATTERN.fullmatch(application_repository):
        fail(
            "spec.source.applicationRepository must use "
            "'owner/repository' format."
        )

    deployment = require_mapping(
        spec.get("deployment"),
        "spec.deployment",
    )

    chart_path = require_string(
        deployment,
        "chartPath",
        "spec.deployment",
    )

    environments = require_string_list(
        deployment,
        "environments",
        "spec.deployment",
    )

    if len(environments) != len(set(environments)):
        fail(
            "spec.deployment.environments must not contain duplicates."
        )

    missing_environments = [
        environment
        for environment in REQUIRED_ENVIRONMENTS
        if environment not in environments
    ]

    if missing_environments:
        fail(
            "spec.deployment.environments is missing required "
            f"environment(s): {', '.join(missing_environments)}."
        )

    automation = require_mapping(
        spec.get("applicationAutomation"),
        "spec.applicationAutomation",
    )

    provider = require_string(
        automation,
        "provider",
        "spec.applicationAutomation",
    )

    if provider != "github-app":
        fail(
            "spec.applicationAutomation.provider must be "
            "'github-app'."
        )

    actor = require_mapping(
        automation.get("actor"),
        "spec.applicationAutomation.actor",
    )

    actor_type = require_string(
        actor,
        "type",
        "spec.applicationAutomation.actor",
    )

    if actor_type != "app":
        fail(
            "spec.applicationAutomation.actor.type must be 'app'."
        )

    actor_slug = require_string(
        actor,
        "slug",
        "spec.applicationAutomation.actor",
    )

    allowed_paths = require_string_list(
        automation,
        "allowedPaths",
        "spec.applicationAutomation",
    )

    expected_path = APP_PATH_TEMPLATE.format(
        environment="{environment}",
        service=service_name,
    )

    if expected_path not in allowed_paths:
        fail(
            "Application automation must allow exactly the "
            "standard service values path: "
            f"'{expected_path}'."
        )

    allowed_fields = require_string_list(
        automation,
        "allowedFields",
        "spec.applicationAutomation",
    )

    if "/image/digest" not in allowed_fields:
        fail(
            "Application automation must allow "
            "'/image/digest'."
        )

    return {
        "application_repository": application_repository,
        "chart_path": chart_path,
        "actor_slug": actor_slug,
    }


def validate_repository_structure(
    service_name: str,
    chart_path: str,
    environments: list[str],
) -> None:
    contract_file = Path(
        os.environ.get(
            "CONTRACT_FILE",
            ".github/gitops.yaml",
        )
    )

    if not contract_file.is_file():
        fail(
            f"Required contract file does not exist: "
            f"{contract_file}"
        )

    chart = Path(chart_path)

    if not chart.is_dir():
        fail(
            f"Helm chart directory does not exist: {chart}"
        )

    required_chart_files = (
        chart / "Chart.yaml",
        chart / "templates",
    )

    for path in required_chart_files:
        if not path.exists():
            fail(
                f"Required Helm chart path does not exist: {path}"
            )

    for environment in environments:
        values_file = Path(
            f"environments/{environment}/"
            f"{service_name}/values.yaml"
        )

        if not values_file.is_file():
            fail(
                "Required environment values file does not "
                f"exist: {values_file}"
            )


def set_github_outputs(
    application_repository: str,
) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")

    if not output_file:
        return

    with open(output_file, "a", encoding="utf-8") as output:
        output.write(
            f"service-name={os.environ['SERVICE_NAME']}\n"
        )
        output.write(
            "application-repository="
            f"{application_repository}\n"
        )


def main() -> int:
    service_name = os.environ.get("SERVICE_NAME", "").strip()

    if not service_name:
        print(
            "::error::SERVICE_NAME is required.",
            file=sys.stderr,
        )
        return 1

    contract_file = Path(
        os.environ.get(
            "CONTRACT_FILE",
            ".github/gitops.yaml",
        )
    )

    try:
        if not contract_file.is_file():
            fail(
                f"GitOps contract file does not exist: "
                f"{contract_file}"
            )

        with contract_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            document = yaml.safe_load(file)

        if not isinstance(document, dict):
            fail("GitOps contract must contain a YAML mapping.")

        result = validate_contract(
            document,
            service_name,
        )

        spec = require_mapping(
            document["spec"],
            "spec",
        )

        deployment = require_mapping(
            spec["deployment"],
            "spec.deployment",
        )

        environments = require_string_list(
            deployment,
            "environments",
            "spec.deployment",
        )

        validate_repository_structure(
            service_name=service_name,
            chart_path=result["chart_path"],
            environments=environments,
        )

        set_github_outputs(
            result["application_repository"],
        )

        print("GitOps contract validation passed.")
        print(f"Service: {service_name}")
        print(
            "Application repository: "
            f"{result['application_repository']}"
        )
        print(
            "Application automation actor: "
            f"{result['actor_slug']}"
        )
        print(
            "Supported environments: "
            f"{', '.join(environments)}"
        )
        print(
            "Helm chart: "
            f"{result['chart_path']}"
        )

        return 0

    except ContractValidationError as exc:
        print(
            f"::error::{exc}",
            file=sys.stderr,
        )
        return 1

    except yaml.YAMLError as exc:
        print(
            f"::error::Invalid YAML in {contract_file}: {exc}",
            file=sys.stderr,
        )
        return 1

    except Exception as exc:
        print(
            f"::error::Unexpected validation failure: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())