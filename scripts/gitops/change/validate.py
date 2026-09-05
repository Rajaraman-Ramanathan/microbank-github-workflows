from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

import yaml


ENVIRONMENTS = {"dev", "stage", "prod"}

EXPECTED_APP_ACTOR_TYPE = "Bot"
EXPECTED_HUMAN_ACTOR_TYPE = "User"

EXPECTED_APP_PROVIDER = "github-app"

SERVICE_PATH_PATTERN = re.compile(
    r"^environments/(?P<environment>[^/]+)/(?P<service>[^/]+)/values\.yaml$"
)


class ChangeValidationError(Exception):
    """Raised when a GitOps PR violates the change contract."""


@dataclass(frozen=True, slots=True)
class ChangeContext:
    service_name: str
    contract_file: str
    actor_login: str
    actor_type: str
    base_sha: str
    head_sha: str
    head_repository: str


def fail(message: str) -> None:
    raise ChangeValidationError(message)


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

    if not all(
        isinstance(item, str) and item.strip()
        for item in value
    ):
        fail(
            f"{path}.{key} must contain only non-empty strings."
        )

    return [item.strip() for item in value]


def load_yaml_from_git(
    sha: str,
    path: str,
) -> Any:
    result = subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    try:
        return yaml.safe_load(result.stdout)
    except yaml.YAMLError as exc:
        fail(
            f"Invalid YAML in '{path}' at revision "
            f"'{sha}': {exc}"
        )


def get_changed_files(
    base_sha: str,
    head_sha: str,
) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "--find-renames",
            "--find-copies",
            base_sha,
            head_sha,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        fail(
            "Unable to determine pull request changes: "
            f"{result.stderr.strip()}"
        )

    files: list[str] = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        status = parts[0]

        if status.startswith(("R", "C")):
            if len(parts) < 3:
                fail(
                    f"Unexpected git diff output: {line}"
                )

            files.append(parts[1])
            files.append(parts[2])
            continue

        if len(parts) < 2:
            fail(
                f"Unexpected git diff output: {line}"
            )

        files.append(parts[1])

    return sorted(set(files))


def load_contract(
    contract_file: str,
    head_sha: str,
) -> dict[str, Any]:
    document = load_yaml_from_git(
        head_sha,
        contract_file,
    )

    if document is None:
        fail(
            f"GitOps contract '{contract_file}' does not "
            "exist in the pull request head revision."
        )

    return require_mapping(
        document,
        "GitOps contract",
    )


def get_application_automation_contract(
    document: dict[str, Any],
) -> tuple[str, str, list[str], list[str]]:
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

    automation = require_mapping(
        spec.get("applicationAutomation"),
        "spec.applicationAutomation",
    )

    provider = require_string(
        automation,
        "provider",
        "spec.applicationAutomation",
    )

    if provider != EXPECTED_APP_PROVIDER:
        fail(
            "Unsupported application automation provider: "
            f"'{provider}'."
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
            "spec.applicationAutomation.actor.type "
            "must be 'app'."
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

    allowed_fields = require_string_list(
        automation,
        "allowedFields",
        "spec.applicationAutomation",
    )

    return (
        application_repository,
        actor_slug,
        allowed_paths,
        allowed_fields,
    )


def normalize_app_login(login: str) -> str:
    """
    GitHub App PR actors commonly appear as:

        my-app[bot]

    The GitOps contract stores:

        my-app
    """
    return login.removesuffix("[bot]")


def is_expected_application_actor(
    actor_login: str,
    actor_type: str,
    expected_actor_slug: str,
) -> bool:
    if actor_type != EXPECTED_APP_ACTOR_TYPE:
        return False

    return (
        normalize_app_login(actor_login)
        == expected_actor_slug
    )


def classify_path(
    path: str,
    service_name: str,
) -> str | None:
    match = SERVICE_PATH_PATTERN.fullmatch(path)

    if not match:
        return None

    environment = match.group("environment")
    service = match.group("service")

    if environment not in ENVIRONMENTS:
        return None

    if service != service_name:
        return None

    return environment


def resolve_allowed_path(
    path_template: str,
    service_name: str,
) -> re.Pattern[str]:
    escaped = re.escape(
        path_template.replace(
            "{service}",
            service_name,
        )
    )

    escaped = escaped.replace(
        re.escape("{environment}"),
        r"(?P<environment>[^/]+)",
    )

    return re.compile(
        f"^{escaped}$"
    )


def path_is_allowed(
    path: str,
    allowed_paths: list[str],
    service_name: str,
) -> str | None:
    for template in allowed_paths:
        pattern = resolve_allowed_path(
            template,
            service_name,
        )

        match = pattern.fullmatch(path)

        if not match:
            continue

        environment = match.groupdict().get(
            "environment"
        )

        if environment and environment not in ENVIRONMENTS:
            fail(
                "Unsupported environment in changed path: "
                f"'{environment}'."
            )

        return environment

    return None


def json_pointer(
    path: tuple[str, ...],
) -> str:
    escaped = [
        component
        .replace("~", "~0")
        .replace("/", "~1")
        for component in path
    ]

    return "/" + "/".join(escaped)


def collect_changes(
    old: Any,
    new: Any,
    path: tuple[str, ...] = (),
) -> set[str]:
    """
    Return JSON Pointer paths whose values changed.

    Mapping changes are represented at the changed leaf.

    Lists are treated as a single value at their containing path.
    """

    if type(old) is not type(new):
        return {json_pointer(path)}

    if isinstance(old, dict):
        changes: set[str] = set()

        keys = set(old) | set(new)

        for key in keys:
            child_path = (*path, str(key))

            if key not in old or key not in new:
                changes.add(json_pointer(child_path))
                continue

            changes.update(
                collect_changes(
                    old[key],
                    new[key],
                    child_path,
                )
            )

        return changes

    if isinstance(old, list):
        if old != new:
            return {json_pointer(path)}

        return set()

    if old != new:
        return {json_pointer(path)}

    return set()


def validate_application_change(
    context: ChangeContext,
    contract: dict[str, Any],
) -> tuple[str, str]:
    (
        application_repository,
        expected_actor,
        allowed_paths,
        allowed_fields,
    ) = get_application_automation_contract(contract)

    if not is_expected_application_actor(
        context.actor_login,
        context.actor_type,
        expected_actor,
    ):
        fail(
            "Pull request was created by an unsupported "
            "automation identity. "
            f"Expected GitHub App '{expected_actor}', "
            f"got '{context.actor_login}' "
            f"of type '{context.actor_type}'."
        )

    if context.head_repository != application_repository:
        fail(
            "Application automation source repository mismatch. "
            f"Expected '{application_repository}', "
            f"got '{context.head_repository}'."
        )

    changed_files = get_changed_files(
        context.base_sha,
        context.head_sha,
    )

    if not changed_files:
        fail(
            "Pull request does not contain any changes."
        )

    protected_prefixes = (
        ".github/",
        "argocd/",
        "workloads/",
    )

    protected_files = [
        path
        for path in changed_files
        if path.startswith(protected_prefixes)
    ]

    if protected_files:
        fail(
            "Application automation cannot modify protected "
            f"GitOps paths: {protected_files}"
        )

    environments: set[str] = set()

    for path in changed_files:
        environment = path_is_allowed(
            path,
            allowed_paths,
            context.service_name,
        )

        if environment is None:
            fail(
                "Application automation is not allowed "
                f"to modify '{path}'."
            )

        environments.add(environment)

    if len(environments) != 1:
        fail(
            "Application automation PR must target exactly "
            "one environment. "
            f"Detected: {sorted(environments)}."
        )

    environment = next(iter(environments))

    expected_values_path = (
        f"environments/{environment}/"
        f"{context.service_name}/values.yaml"
    )

    if changed_files != [expected_values_path]:
        fail(
            "Application automation PR must modify exactly "
            f"'{expected_values_path}'. "
            f"Changed files: {changed_files}"
        )

    old_values = load_yaml_from_git(
        context.base_sha,
        expected_values_path,
    )

    new_values = load_yaml_from_git(
        context.head_sha,
        expected_values_path,
    )

    if old_values is None:
        fail(
            "Application automation cannot create a new "
            "environment values file: "
            f"'{expected_values_path}'."
        )

    if new_values is None:
        fail(
            "Application automation cannot delete the "
            "environment values file: "
            f"'{expected_values_path}'."
        )

    changed_fields = collect_changes(
        old_values,
        new_values,
    )

    unexpected_fields = (
        changed_fields - set(allowed_fields)
    )

    if unexpected_fields:
        fail(
            "Application automation may modify only the "
            f"following fields: {allowed_fields}. "
            f"Unexpected changes: "
            f"{sorted(unexpected_fields)}"
        )

    if not changed_fields:
        fail(
            "The values file was changed but no semantic "
            "YAML field change was detected."
        )

    if "/image/digest" not in changed_fields:
        fail(
            "Application release PR must modify "
            "'/image/digest'."
        )

    return (
        "application-image-update",
        environment,
    )


def validate_human_change(
    context: ChangeContext,
) -> tuple[str, str]:
    changed_files = get_changed_files(
        context.base_sha,
        context.head_sha,
    )

    if not changed_files:
        fail(
            "Pull request does not contain any changes."
        )

    environments = {
        environment
        for path in changed_files
        if (
            environment := classify_path(
                path,
                context.service_name,
            )
        )
    }

    if len(environments) == 1:
        environment = next(iter(environments))
    elif len(environments) == 0:
        environment = ""
    else:
        environment = "multiple"

    return (
        "human-change",
        environment,
    )


def write_outputs(
    actor_type: str,
    actor_login: str,
    change_type: str,
    environment: str,
) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")

    if not output_file:
        return

    with open(
        output_file,
        "a",
        encoding="utf-8",
    ) as output:
        output.write(
            f"actor-type={actor_type}\n"
        )
        output.write(
            f"actor-login={actor_login}\n"
        )
        output.write(
            f"change-type={change_type}\n"
        )
        output.write(
            f"environment={environment}\n"
        )


def main() -> int:
    service_name = os.environ.get(
        "SERVICE_NAME",
        "",
    ).strip()

    contract_file = os.environ.get(
        "CONTRACT_FILE",
        ".github/gitops.yaml",
    )

    actor_login = os.environ.get(
        "PR_ACTOR_LOGIN",
        "",
    ).strip()

    actor_type = os.environ.get(
        "PR_ACTOR_TYPE",
        "",
    ).strip()

    base_sha = os.environ.get(
        "PR_BASE_SHA",
        "",
    ).strip()

    head_sha = os.environ.get(
        "PR_HEAD_SHA",
        "",
    ).strip()

    head_repository = os.environ.get(
        "PR_HEAD_REPOSITORY",
        "",
    ).strip()

    context = ChangeContext(
        service_name=service_name,
        contract_file=contract_file,
        actor_login=actor_login,
        actor_type=actor_type,
        base_sha=base_sha,
        head_sha=head_sha,
        head_repository=head_repository,
    )

    try:
        if not context.service_name:
            fail("SERVICE_NAME is required.")

        if not context.actor_login:
            fail(
                "Pull request actor login is unavailable."
            )

        if not context.actor_type:
            fail(
                "Pull request actor type is unavailable."
            )

        if not context.base_sha:
            fail(
                "Pull request base SHA is unavailable."
            )

        if not context.head_sha:
            fail(
                "Pull request head SHA is unavailable."
            )

        contract = load_contract(
            context.contract_file,
            context.head_sha,
        )

        if context.actor_type == EXPECTED_HUMAN_ACTOR_TYPE:
            change_type, environment = (
                validate_human_change(context)
            )

        elif context.actor_type == EXPECTED_APP_ACTOR_TYPE:
            if not context.head_repository:
                fail(
                    "Application automation source repository "
                    "identity is unavailable."
                )

            change_type, environment = (
                validate_application_change(
                    context,
                    contract,
                )
            )

        else:
            fail(
                "Unsupported pull request actor type: "
                f"'{context.actor_type}'."
            )

        write_outputs(
            actor_type=(
                "user"
                if context.actor_type == EXPECTED_HUMAN_ACTOR_TYPE
                else "app"
            ),
            actor_login=context.actor_login,
            change_type=change_type,
            environment=environment,
        )

        print(
            "GitOps change validation passed."
        )
        print(
            f"Actor       : {context.actor_login}"
        )
        print(
            f"Actor type  : {context.actor_type}"
        )
        print(
            f"Change type : {change_type}"
        )
        print(
            "Environment : "
            f"{environment or 'not environment-specific'}"
        )

        return 0

    except ChangeValidationError as exc:
        print(
            f"::error::{exc}",
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