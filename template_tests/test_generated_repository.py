from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PATHS = {
    path
    for path in """
.copier-answers.yml
.dockerignore
.gitignore
.pre-commit-config.yaml
Dockerfile
LICENSE
Makefile
README.md
alembic
alembic.ini
alembic/env.py
alembic/script.py.mako
alembic/versions
alembic/versions/.gitkeep
docker-compose.yml
docs
docs/assets
docs/assets/bootstrap-base-glow-hq.gif
iac
iac/.gitkeep
poetry.lock
pyproject.toml
ruff.toml
src
src/__init__.py
src/api
src/api/__init__.py
src/api/dependencies.py
src/api/middleware
src/api/middleware/__init__.py
src/api/routes
src/api/routes/__init__.py
src/api/routes/health.py
src/api/schemas
src/api/schemas/__init__.py
src/api/schemas/error.py
src/api/schemas/health.py
src/config.py
src/domain
src/domain/__init__.py
src/domain/entities
src/domain/entities/__init__.py
src/domain/exceptions
src/domain/exceptions/__init__.py
src/domain/types
src/domain/types/__init__.py
src/main.py
src/persistence
src/persistence/__init__.py
src/persistence/database.py
src/persistence/models
src/persistence/models/__init__.py
src/persistence/repositories
src/persistence/repositories/__init__.py
src/services
src/services/__init__.py
src/services/exceptions
src/services/exceptions/__init__.py
tests
tests/__init__.py
tests/acceptance
tests/acceptance/__init__.py
tests/acceptance/run.py
tests/conftest.py
tests/factories
tests/factories/__init__.py
tests/integration
tests/integration/__init__.py
tests/integration/api
tests/integration/api/__init__.py
tests/integration/api/test_health.py
tests/unit
tests/unit/__init__.py
tests/unit/api
tests/unit/api/__init__.py
tests/unit/api/middleware
tests/unit/api/middleware/__init__.py
tests/unit/api/routes
tests/unit/api/routes/__init__.py
tests/unit/api/schemas
tests/unit/api/schemas/__init__.py
tests/unit/domain
tests/unit/domain/__init__.py
tests/unit/domain/entities
tests/unit/domain/entities/__init__.py
tests/unit/domain/exceptions
tests/unit/domain/exceptions/__init__.py
tests/unit/domain/types
tests/unit/domain/types/__init__.py
tests/unit/persistence
tests/unit/persistence/__init__.py
tests/unit/persistence/models
tests/unit/persistence/models/__init__.py
tests/unit/persistence/repositories
tests/unit/persistence/repositories/__init__.py
tests/unit/services
tests/unit/services/__init__.py
tests/unit/services/exceptions
tests/unit/services/exceptions/__init__.py
""".splitlines()
    if path
}


class TestGeneratedRepository(unittest.TestCase):
    """Validate the repository an end user receives from Copier."""

    temporary_directory: tempfile.TemporaryDirectory[str]
    project_directory: Path
    project_report_path: Path
    generated_paths: set[str]
    setup_output: str
    placeholder_count: int = 0

    @classmethod
    def run_command(cls, command: list[str]) -> str:
        result = subprocess.run(
            command,
            cwd=cls.project_directory,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300,
        )
        if result.returncode:
            raise AssertionError(f"Command failed ({' '.join(command)}):\n{result.stdout}")
        return result.stdout

    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory(prefix="fastapi-template-acceptance-")
        cls.project_directory = Path(cls.temporary_directory.name) / "acceptance-app"

        result = subprocess.run(
            [
                "copier",
                "copy",
                "--trust",
                "--defaults",
                "--data",
                "project_name=Acceptance App",
                str(TEMPLATE_ROOT),
                str(cls.project_directory),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
        )
        if result.returncode:
            raise RuntimeError(f"Copier generation failed:\n{result.stdout}")

        cls.generated_paths = {
            path.relative_to(cls.project_directory).as_posix()
            for path in cls.project_directory.rglob("*")
        }

        environment = os.environ.copy()
        environment["CI"] = "1"
        environment["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"
        cls.project_report_path = (
            Path(cls.temporary_directory.name) / "generated-project-report.html"
        )
        environment["PROJECT_REPORT_PATH"] = str(cls.project_report_path)
        result = subprocess.run(
            ["make", "setup"],
            cwd=cls.project_directory,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
        )
        if result.returncode:
            raise RuntimeError(f"Generated-project setup failed:\n{result.stdout}")
        cls.setup_output = result.stdout

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def test_generated_tree_matches_contract(self) -> None:
        """Generated tree matches the complete contract."""
        self.assertEqual(self.generated_paths, EXPECTED_PATHS)

    def test_project_identity_is_rendered(self) -> None:
        """Project name, slug, and Compose name are rendered."""
        self.assertIn(
            'name = "acceptance-app"',
            (self.project_directory / "pyproject.toml").read_text(),
        )
        self.assertIn(
            'name: "acceptance-app"',
            (self.project_directory / "docker-compose.yml").read_text(),
        )
        self.assertIn(
            'app = FastAPI(title="Acceptance App", lifespan=lifespan)',
            (self.project_directory / "src/main.py").read_text(),
        )

    def test_all_template_placeholders_are_rendered(self) -> None:
        """Every source placeholder is rendered in the generated repository."""
        placeholder_files: dict[Path, int] = {}
        for path in TEMPLATE_ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative_path = path.relative_to(TEMPLATE_ROOT)
            excluded_parts = {
                ".git",
                ".github",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                ".venv",
                "template_tests",
            }
            if relative_path == Path("copier.yml") or excluded_parts.intersection(
                relative_path.parts
            ):
                continue
            try:
                content = path.read_text()
            except UnicodeDecodeError:
                continue
            count = content.count("{{")
            if count:
                placeholder_files[relative_path] = count

        type(self).placeholder_count = sum(placeholder_files.values())
        self.assertGreater(type(self).placeholder_count, 0)

        unresolved_files = []
        for path in self.project_directory.rglob("*"):
            if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
                continue
            try:
                content = path.read_text()
            except UnicodeDecodeError:
                continue
            if "{{" in content or "{%" in content:
                unresolved_files.append(path.relative_to(self.project_directory).as_posix())

        self.assertEqual(unresolved_files, [])
        for relative_path in placeholder_files:
            self.assertTrue((self.project_directory / relative_path).is_file())

    def test_setup_installs_and_runs_git_hooks(self) -> None:
        """Installed hooks pass clean code and block an invalid local push."""
        self.assertIn("Running GEN-01", self.setup_output)
        self.assertIn("All set — acceptance-app is ready.", self.setup_output)
        self.assertIn("6/6 checks passed", self.setup_output)
        report = self.project_report_path.read_text()
        self.assertIn(
            "<title>FastAPI Starter Check: acceptance-app</title>",
            report,
        )
        self.assertIn("<h1>FastAPI Starter Check: acceptance-app</h1>", report)
        self.assertTrue((self.project_directory / ".git/hooks/pre-commit").stat().st_mode & 0o111)
        self.assertTrue((self.project_directory / ".git/hooks/pre-push").stat().st_mode & 0o111)
        self.run_command(["git", "config", "user.name", "Template Acceptance"])
        self.run_command(["git", "config", "user.email", "acceptance@example.invalid"])
        self.run_command(["git", "add", "."])
        self.run_command(["git", "commit", "-m", "test: verify clean generated project"])

        probe_path = self.project_directory / "src/hook_probe.py"
        remote_path = Path(self.temporary_directory.name) / "audit.git"
        try:
            probe_path.write_text('value: int = "invalid"\n')
            self.run_command(["git", "add", "src/hook_probe.py"])
            self.run_command(["git", "commit", "--no-verify", "-m", "test: probe pre-push hook"])
            self.run_command(["git", "init", "--bare", str(remote_path)])
            self.run_command(["git", "remote", "add", "audit", str(remote_path)])
            push_result = subprocess.run(
                ["git", "push", "audit", "main"],
                cwd=self.project_directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=300,
            )
            self.assertNotEqual(push_result.returncode, 0)
            self.assertIn("src/hook_probe.py", push_result.stdout)
        finally:
            probe_path.unlink(missing_ok=True)

    def test_poetry_lock_is_consistent(self) -> None:
        """Poetry metadata and lock file are consistent."""
        self.run_command(["poetry", "check", "--lock"])

    def test_static_checks_pass(self) -> None:
        """Ruff and strict MyPy checks pass."""
        self.run_command(["make", "check"])

    def test_application_tests_pass(self) -> None:
        """The generated FastAPI integration test passes."""
        self.run_command(["make", "test"])

    def test_docker_compose_configuration_resolves(self) -> None:
        """Docker Compose configuration resolves."""
        self.run_command(["docker", "compose", "config", "--quiet"])
