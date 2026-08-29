from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class KubernetesValidationError(Exception):
    """Raised when Kubernetes manifest validation fails."""


def fail(message: str) -> None:
    raise KubernetesValidationError(message)


def get_rendered_files(
    rendered_directory: Path,
) -> list[Path]:
    if not rendered_directory.is_dir():
        fail(
            "Rendered manifest directory does not exist: "
            f"{rendered_directory}"
        )

    files = sorted(
        path
        for path in rendered_directory.glob("*.yaml")
        if path.is_file()
    )

    if not files:
        fail(
            "No rendered Kubernetes manifests were found in "
            f"{rendered_directory}"
        )

    return files


def validate_kubernetes_version(
    version: str,
) -> None:
    parts = version.split(".")

    if len(parts) != 2:
        fail(
            "Kubernetes version must use MAJOR.MINOR format, "
            f"for example '1.33'. Got '{version}'."
        )

    if not all(part.isdigit() for part in parts):
        fail(
            "Kubernetes version must contain numeric "
            f"MAJOR.MINOR components. Got '{version}'."
        )


def count_documents(
    files: list[Path],
) -> int:
    """
    Count YAML documents separated by '---'.

    This is intentionally lightweight. Kubeconform remains
    authoritative for actual Kubernetes validation.
    """

    count = 0

    for file in files:
        content = file.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            continue

        documents = [
            document
            for document in content.split("\n---")
            if document.strip()
        ]

        count += len(documents)

    return count


def run_kubeconform(
    rendered_directory: Path,
    kubernetes_version: str,
) -> None:
    command = [
        "kubeconform",
        "-strict",
        "-summary",
        "-output",
        "text",
        "-kubernetes-version",
        kubernetes_version,
        str(rendered_directory),
    ]

    print(
        "Running kubeconform:"
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
            "Kubernetes manifest validation failed."
        )


def write_outputs(
    manifest_count: int,
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
            f"manifest-count={manifest_count}\n"
        )


def main() -> int:
    rendered_directory = Path(
        os.environ.get(
            "RENDERED_DIRECTORY",
            ".gitops-rendered",
        )
    )

    kubernetes_version = os.environ.get(
        "KUBERNETES_VERSION",
        "",
    ).strip()

    try:
        if not kubernetes_version:
            fail(
                "KUBERNETES_VERSION is required."
            )

        validate_kubernetes_version(
            kubernetes_version
        )

        files = get_rendered_files(
            rendered_directory
        )

        manifest_count = count_documents(
            files
        )

        if manifest_count == 0:
            fail(
                "Rendered manifests contain no YAML "
                "documents."
            )

        print(
            f"Found {len(files)} rendered manifest file(s)."
        )

        print(
            f"Found {manifest_count} manifest document(s)."
        )

        print(
            "Kubernetes schema version: "
            f"{kubernetes_version}"
        )

        run_kubeconform(
            rendered_directory,
            kubernetes_version,
        )

        write_outputs(
            manifest_count
        )

        print(
            "GitOps Kubernetes validation passed."
        )

        return 0

    except KubernetesValidationError as exc:
        print(
            f"::error::{exc}",
            file=sys.stderr,
        )
        return 1

    except Exception as exc:
        print(
            "::error::Unexpected Kubernetes "
            f"validation failure: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())