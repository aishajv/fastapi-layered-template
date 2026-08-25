from __future__ import annotations

import html
import os
import tempfile
import time
import traceback
import unittest
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from template_tests.test_generated_repository import TestGeneratedRepository

TEST_ORDER = [
    "test_generated_tree_matches_contract",
    "test_all_template_placeholders_are_rendered",
    "test_project_identity_is_rendered",
    "test_setup_installs_and_runs_git_hooks",
    "test_poetry_lock_is_consistent",
    "test_static_checks_pass",
    "test_application_tests_pass",
    "test_docker_compose_configuration_resolves",
]

CHECK_DETAILS = {
    "prepare": (
        "The template checkout, Copier 9+, Poetry 2.4, Git, and Make are available.",
        'copier copy --trust --defaults --data "project_name=Acceptance App" TEMPLATE OUTPUT\n'
        "make setup",
        "A standalone project is generated, Git initializes, dependencies install, "
        "and hooks install.",
    ),
    "test_generated_tree_matches_contract": (
        "A fresh project exists before generated files are modified.",
        "Compare every generated file and directory with the explicit path contract.",
        "There are no missing or additional paths.",
    ),
    "test_all_template_placeholders_are_rendered": (
        "All template files, including hidden Copier answer metadata, are scanned.",
        "Count every source {{ ... }} expression and scan every generated text file.",
        "Every discovered expression renders and no Jinja marker remains.",
    ),
    "test_project_identity_is_rendered": (
        "The project name is Acceptance App.",
        "Inspect pyproject.toml, docker-compose.yml, and src/main.py.",
        "The name, acceptance-app slug, and acceptance_app database name are correct.",
    ),
    "test_setup_installs_and_runs_git_hooks": (
        "The generated repository has completed make setup.",
        "Create a clean commit, commit invalid typing with --no-verify, and push to a "
        "local bare remote.",
        "The clean commit succeeds and the installed pre-push hook blocks the invalid file.",
    ),
    "test_poetry_lock_is_consistent": (
        "The generated Poetry project and lockfile exist.",
        "poetry check --lock",
        "Poetry metadata and the lockfile agree.",
    ),
    "test_static_checks_pass": (
        "Generated-project dependencies are installed.",
        "make check",
        "Ruff formatting, Ruff linting, and strict MyPy pass.",
    ),
    "test_application_tests_pass": (
        "The generated FastAPI project and test environment are ready.",
        "make test",
        "The shipped health integration test passes.",
    ),
    "test_docker_compose_configuration_resolves": (
        "Docker Compose is available.",
        "docker compose config --quiet",
        "The generated Compose configuration resolves without errors.",
    ),
}

CHECK_GROUPS = {
    "Generation": [
        "prepare",
        "test_generated_tree_matches_contract",
        "test_all_template_placeholders_are_rendered",
        "test_project_identity_is_rendered",
    ],
    "Developer tooling": [
        "test_setup_installs_and_runs_git_hooks",
        "test_poetry_lock_is_consistent",
        "test_static_checks_pass",
    ],
    "Application": ["test_application_tests_pass"],
    "Containers": ["test_docker_compose_configuration_resolves"],
}

CHECK_IDS = {
    "prepare": "SETUP-01",
    "test_generated_tree_matches_contract": "GEN-04",
    "test_all_template_placeholders_are_rendered": "GEN-03",
    "test_project_identity_is_rendered": "GEN-01",
    "test_setup_installs_and_runs_git_hooks": "HOOK-02/05",
    "test_poetry_lock_is_consistent": "QUAL-03",
    "test_static_checks_pass": "QUAL-01",
    "test_application_tests_pass": "QUAL-02",
    "test_docker_compose_configuration_resolves": "CTR-01",
}


@dataclass(frozen=True)
class CheckResult:
    key: str
    label: str
    status: str
    observed: str
    detail: str = ""


def print_progress(completed: int, total: int, result: CheckResult, elapsed: float) -> None:
    filled = round(12 * completed / total)
    bar = "█" * filled + "░" * (12 - filled)
    print(
        f"[{completed}/{total}] {bar} {result.status:<6} "
        f"{CHECK_IDS[result.key]} {result.label} ({elapsed:.1f}s)"
    )


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []
    discovered_tests = unittest.defaultTestLoader.getTestCaseNames(TestGeneratedRepository)
    if set(TEST_ORDER) != set(discovered_tests):
        missing_tests = sorted(set(discovered_tests) - set(TEST_ORDER))
        unknown_tests = sorted(set(TEST_ORDER) - set(discovered_tests))
        raise RuntimeError(f"TEST_ORDER mismatch; missing={missing_tests}, unknown={unknown_tests}")

    grouped_key_list = [key for keys in CHECK_GROUPS.values() for key in keys]
    grouped_keys = set(grouped_key_list)
    expected_grouped_keys = {"prepare", *TEST_ORDER}
    if grouped_keys != expected_grouped_keys or len(grouped_key_list) != len(grouped_keys):
        raise RuntimeError("CHECK_GROUPS must include every reported check exactly once")
    if set(CHECK_IDS) != expected_grouped_keys:
        raise RuntimeError("CHECK_IDS must include every reported check")

    total = len(TEST_ORDER) + 1

    print("\nPreparing a fresh generated repository…")
    started_at = time.monotonic()
    try:
        TestGeneratedRepository.setUpClass()
        preparation = CheckResult(
            key="prepare",
            label="Fresh repository generated and setup completed.",
            status="passed",
            observed="Project generation and setup completed successfully.",
        )
    except Exception:
        preparation = CheckResult(
            key="prepare",
            label="Fresh repository generated and setup completed.",
            status="failed",
            observed="Project generation or setup failed.",
            detail=traceback.format_exc(),
        )
        print_progress(1, total, preparation, time.monotonic() - started_at)
        print(preparation.detail)
        return [preparation]

    print_progress(1, total, preparation, time.monotonic() - started_at)
    results.append(preparation)
    try:
        for completed, test_name in enumerate(TEST_ORDER, start=2):
            test_case = TestGeneratedRepository(methodName=test_name)
            label = test_case.shortDescription() or test_name
            started_at = time.monotonic()
            try:
                test_case.setUp()
                getattr(test_case, test_name)()
                test_case.tearDown()
                if test_name == "test_all_template_placeholders_are_rendered":
                    label = (
                        f"{TestGeneratedRepository.placeholder_count} placeholders found; "
                        f"{TestGeneratedRepository.placeholder_count} rendered."
                    )
                result = CheckResult(
                    key=test_name,
                    label=label,
                    status="passed",
                    observed=(
                        label
                        if test_name == "test_all_template_placeholders_are_rendered"
                        else "Passed."
                    ),
                )
            except Exception:
                result = CheckResult(
                    key=test_name,
                    label=label,
                    status="failed",
                    observed="Failed. See diagnostics below.",
                    detail=traceback.format_exc(),
                )
                print(result.detail)
            print_progress(
                completed,
                total,
                result,
                time.monotonic() - started_at,
            )
            results.append(result)
    finally:
        TestGeneratedRepository.tearDownClass()

    return results


def render_case(result: CheckResult) -> str:
    diagnostics = (
        f"<section><h3>Diagnostics</h3><pre>{html.escape(result.detail)}</pre></section>"
        if result.detail
        else ""
    )
    return f"""
        <details class="case {result.status}">
          <summary>
            <span class="case-id">{CHECK_IDS[result.key]}</span>
            <span>{html.escape(result.label)}</span>
            <strong>{result.status}</strong>
            <span class="chevron" aria-hidden="true">›</span>
          </summary>
          <div class="detail">
            <section><h3>Setup</h3><p>{html.escape(CHECK_DETAILS[result.key][0])}</p></section>
            <section><h3>Command</h3><pre>{html.escape(CHECK_DETAILS[result.key][1])}</pre></section>
            <section><h3>Expected</h3><p>{html.escape(CHECK_DETAILS[result.key][2])}</p></section>
            <section class="result"><h3>Result</h3><p>{html.escape(result.observed)}</p></section>
            {diagnostics}
          </div>
        </details>
    """


def write_report(results: list[CheckResult]) -> Path:
    default_path = Path(tempfile.gettempdir()) / "fastapi-generated-repository-validation.html"
    report_path = Path(os.environ.get("TEMPLATE_REPORT_PATH", default_path))
    results_by_key = {result.key: result for result in results}
    groups = "".join(
        f"""
        <section class="group">
          <div class="group-title">
            <h2>{html.escape(group)}</h2>
            <span>{len([key for key in keys if key in results_by_key])} checks</span>
          </div>
          {"".join(render_case(results_by_key[key]) for key in keys if key in results_by_key)}
        </section>
        """
        for group, keys in CHECK_GROUPS.items()
        if any(key in results_by_key for key in keys)
    )
    passed = sum(result.status == "passed" for result in results)
    blockers = len(results) - passed
    blocker_label = "blocker" if blockers == 1 else "blockers"
    report_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>FastAPI Starter Check</title>
  <style>
    :root {{
      color-scheme: dark;
      --ink: #edede7;
      --muted: #92928d;
      --line: #30302d;
      --accent: #d8ff36;
      --panel: #131312;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #080808;
      color: var(--ink);
      font: 400 14px/1.6 ui-monospace, 'SFMono-Regular', Consolas, monospace;
    }}
    main {{ width: min(820px, calc(100% - 32px)); margin: 0 auto; padding: 56px 0; }}
    h1 {{
      margin: 0 0 6px;
      font-size: clamp(1.7rem, 5vw, 2.7rem);
      font-weight: 300;
      letter-spacing: -.04em;
    }}
    p {{ margin: 0; color: var(--muted); }}
    .summary {{ margin: 30px 0 18px; padding: 12px 0; border-block: 1px solid var(--line); }}
    .summary strong {{ color: var(--accent); font-weight: 400; }}
    .case {{
      margin: 7px 0;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--panel);
    }}
    summary {{
      display: grid;
      grid-template-columns: 88px minmax(0, 1fr) auto 18px;
      align-items: center;
      gap: 20px;
      padding: 13px 15px;
      cursor: pointer;
    }}
    summary strong {{ color: #8bd17c; font-size: .72rem; font-weight: 400; }}
    .case-id {{ color: var(--accent); font-size: .7rem; }}
    .failed summary strong {{ color: #ff806d; }}
    .chevron {{
      color: var(--muted);
      font-size: 1.35rem;
      line-height: 1;
      transition: transform .15s ease;
    }}
    details[open] .chevron {{ transform: rotate(90deg); color: var(--accent); }}
    .group {{ margin-top: 24px; }}
    .group-title {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      margin-bottom: 8px;
    }}
    .group-title h2 {{
      margin: 0;
      font-size: .82rem;
      font-weight: 400;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .group-title span {{ color: var(--muted); font-size: .68rem; }}
    .detail {{ border-top: 1px solid var(--line); }}
    .detail section {{
      display: grid;
      grid-template-columns: 110px minmax(0, 1fr);
      gap: 16px;
      padding: 12px 15px;
      border-bottom: 1px solid #242421;
    }}
    .detail section:last-child {{ border-bottom: 0; }}
    .detail .result {{ box-shadow: inset 2px 0 0 var(--accent); }}
    h3 {{
      margin: 2px 0 0;
      color: var(--muted);
      font-size: .68rem;
      font-weight: 400;
      text-transform: uppercase;
    }}
    .detail p {{ color: var(--ink); }}
    pre {{
      margin: 0;
      padding: 9px 11px;
      border: 1px solid var(--line);
      border-radius: 3px;
      background: #181817;
      white-space: pre-wrap;
      color: var(--ink);
      overflow: auto;
    }}
    @media (max-width: 620px) {{
      .detail section {{ grid-template-columns: 1fr; gap: 5px; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>FastAPI Starter Check</h1>
    <p>A fresh FastAPI repository that installs, tests, and runs.</p>
    <div class="summary">
      <strong>{passed}/{len(results)} passed</strong> · {blockers} {blocker_label}
    </div>
    {groups}
  </main>
</body>
</html>
"""
    )
    return report_path


def main() -> int:
    results = run_checks()
    report_path = write_report(results)
    passed = sum(result.status == "passed" for result in results)

    print(f"\n{passed}/{len(results)} checks passed")
    print(f"Visual report: {report_path.as_uri()}")
    if not os.environ.get("CI"):
        try:
            if not webbrowser.open(report_path.as_uri()):
                print("The browser did not open; use the report link above.")
        except webbrowser.Error:
            print("The browser did not open; use the report link above.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
