from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


class HelmValidationError(Exception):
    """Raised when Helm validation fails."""


def fail(message: str) -> None:
    raise HelmValidationError(message)


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
        fail(
            f"{path}.{key} must be a non-empty string."
        )

    return value.strip()


def require_string_list(
    mapping: dict[str, Any],
    key: str,
    path: str,
) -> list[str]:
    value = mapping.get(key)

    if not isinstance(value, list) or not value:
        fail(
            f"{path}.{key} must be a non-empty list."
        )

    if not all(
        isinstance(item, str) and item.strip()
        for item in value
    ):
        fail(
            f"{path}.{key} must contain only "
            "non-empty strings."
        )

    return [item.strip() for item in value]


def load_contract(
    contract_file: Path,
) -> dict[str, Any]:
    if not contract_file.is_file():
        fail(
            f"GitOps contract does not exist: "
            f"{contract_file}"
        )

    try:
        with contract_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            document = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        fail(
            f"Invalid YAML in {contract_file}: {exc}"
        )

    return require_mapping(
        document,
        "GitOps contract",
    )


def get_deployment_configuration(
    contract: dict[str, Any],
) -> tuple[str, list[str]]:
    spec = require_mapping(
        contract.get("spec"),
        "spec",
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

    return chart_path, environments


def validate_chart_structure(
    chart_path: Path,
) -> None:
    if not chart_path.is_dir():
        fail(
            f"Helm chart directory does not exist: "
            f"{chart_path}"
        )

    chart_yaml = chart_path / "Chart.yaml"

    if not chart_yaml.is_file():
        fail(
            f"Helm chart is missing Chart.yaml: "
            f"{chart_yaml}"
        )

    templates = chart_path / "templates"

    if not templates.is_dir():
        fail(
            f"Helm chart is missing templates directory: "
            f"{templates}"
        )


def validate_values_file(
    service_name: str,
    environment: str,
) -> Path:
    values_file = Path(
        "environments"
    ) / environment / service_name / "values.yaml"

    if not values_file.is_file():
        fail(
            f"Required values file does not exist: "
            f"{values_file}"
        )

    return values_file


def run_helm(
    args: list[str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["helm", *args],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        command = "helm " + " ".join(args)

        fail(
            f"Helm command failed:\n"
            f"Command: {command}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return result


def lint_chart(
    chart_path: Path,
) -> None:
    print(
        f"Running Helm lint against {chart_path}"
    )

    run_helm(
        [
            "lint",
            str(chart_path),
        ]
    )


def render_environment(
    service_name: str,
    environment: str,
    chart_path: Path,
    values_file: Path,
    output_directory: Path,
) -> None:
    output_file = (
        output_directory
        / f"{environment}.yaml"
    )

    release_name = (
        f"{service_name}-{environment}"
    )

    print(
        f"Rendering {service_name} for "
        f"environment '{environment}'"
    )

    result = run_helm(
        [
            "template",
            release_name,
            str(chart_path),
            "--namespace",
            service_name,
            "--values",
            str(values_file),
        ]
    )

    output_file.write_text(
        result.stdout,
        encoding="utf-8",
    )

    print(
        f"Rendered manifests written to "
        f"{output_file}"
    )


def validate_rendered_output(
    output_directory: Path,
    environment: str,
) -> None:
    output_file = (
        output_directory
        / f"{environment}.yaml"
    )

    if not output_file.is_file():
        fail(
            f"Helm did not produce the expected "
            f"rendered manifest: {output_file}"
        )

    if not output_file.read_text(
        encoding="utf-8"
    ).strip():
        fail(
            f"Rendered manifest is empty: "
            f"{output_file}"
        )


def write_outputs(
    output_directory: Path,
    environments: list[str],
) -> None:
    output_file = os.environ.get(
        "GITHUB_OUTPUT"
    )

    if not output_file:
        return

    with open(
        output_file,
        "a",
        encoding="utf-8",
    ) as output:
        output.write(
            "output-directory="
            f"{output_directory}\n"
        )

        output.write(
            "environments="
            f"{','.join(environments)}\n"
        )


def main() -> int:
    service_name = os.environ.get(
        "SERVICE_NAME",
        "",
    ).strip()

    contract_file = Path(
        os.environ.get(
            "CONTRACT_FILE",
            ".github/gitops.yaml",
        )
    )

    output_directory = Path(
        os.environ.get(
            "OUTPUT_DIRECTORY",
            ".gitops-rendered",
        )
    )

    try:
        if not service_name:
            fail(
                "SERVICE_NAME is required."
            )

        contract = load_contract(
            contract_file
        )

        chart_path_string, environments = (
            get_deployment_configuration(
                contract
            )
        )

        chart_path = Path(
            chart_path_string
        )

        validate_chart_structure(
            chart_path
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        lint_chart(chart_path)

        for environment in environments:
            values_file = validate_values_file(
                service_name,
                environment,
            )

            render_environment(
                service_name=service_name,
                environment=environment,
                chart_path=chart_path,
                values_file=values_file,
                output_directory=output_directory,
            )

            validate_rendered_output(
                output_directory,
                environment,
            )

        write_outputs(
            output_directory,
            environments,
        )

        print(
            "GitOps Helm validation passed."
        )

        return 0

    except HelmValidationError as exc:
        print(
            f"::error::{exc}",
            file=sys.stderr,
        )
        return 1

    except Exception as exc:
        print(
            "::error::Unexpected Helm validation "
            f"failure: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())