from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class PolicyValidationError(Exception):
    """Raised when policy validation fails."""


def fail(message: str) -> None:
    raise PolicyValidationError(message)


def validate_directory(
    directory: Path,
    description: str,
) -> None:
    if not directory.is_dir():
        fail(
            f"{description} does not exist: {directory}"
        )


def get_manifest_files(
    rendered_directory: Path,
) -> list[Path]:
    files = sorted(
        path
        for path in rendered_directory.glob("*.yaml")
        if path.is_file()
    )

    if not files:
        fail(
            "No rendered Kubernetes manifests found in "
            f"{rendered_directory}"
        )

    return files


def get_policy_files(
    policy_directory: Path,
) -> list[Path]:
    files = sorted(
        path
        for path in policy_directory.rglob("*.yaml")
        if path.is_file()
    )

    if not files:
        fail(
            "No Kyverno policy files found in "
            f"{policy_directory}"
        )

    return files


def run_kyverno(
    rendered_directory: Path,
    policy_directory: Path,
) -> None:
    command = [
        "kyverno",
        "apply",
        str(policy_directory),
        "--resource",
        str(rendered_directory),
    ]

    print(
        "Running Kyverno policy validation:"
    )

    print(
        " ".join(command)
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        if result.stderr:
            print(
                result.stderr,
                file=sys.stderr,
            )

        fail(
            "Kyverno policy validation failed."
        )


def write_outputs(
    status: str,
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
            f"policy-status={status}\n"
        )


def main() -> int:
    rendered_directory = Path(
        os.environ.get(
            "RENDERED_DIRECTORY",
            ".gitops-rendered",
        )
    )

    policy_directory = Path(
        os.environ.get(
            "POLICY_DIRECTORY",
            "",
        )
    )

    try:
        if not str(policy_directory):
            fail(
                "POLICY_DIRECTORY is required."
            )

        validate_directory(
            rendered_directory,
            "Rendered manifest directory",
        )

        validate_directory(
            policy_directory,
            "Kyverno policy directory",
        )

        manifest_files = get_manifest_files(
            rendered_directory
        )

        policy_files = get_policy_files(
            policy_directory
        )

        print(
            f"Found {len(manifest_files)} rendered "
            "manifest file(s)."
        )

        print(
            f"Found {len(policy_files)} policy file(s)."
        )

        run_kyverno(
            rendered_directory,
            policy_directory,
        )

        write_outputs("passed")

        print(
            "GitOps policy validation passed."
        )

        return 0

    except PolicyValidationError as exc:
        print(
            f"::error::{exc}",
            file=sys.stderr,
        )

        write_outputs("failed")

        return 1

    except Exception as exc:
        print(
            "::error::Unexpected policy validation "
            f"failure: {exc}",
            file=sys.stderr,
        )

        write_outputs("failed")

        return 1


if __name__ == "__main__":
    raise SystemExit(main())