"""The published JSON Schemas must accept what list-deps really prints."""
import json
from pathlib import Path

from click.testing import CliRunner

from depscan.cli import cli

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"

FIXTURES = {
    "Cargo.lock": '[[package]]\nname = "serde"\nversion = "1.0.0"\n',
    "go.mod": "module example.com/app\n\ngo 1.22\n\nrequire github.com/pkg/errors v0.9.1\n",
    "package-lock.json": json.dumps({"lockfileVersion": 3, "packages": {"node_modules/lodash": {"version": "4.17.21"}}}),
    "requirements.txt": "requests==2.31.0\n",
    "Gemfile.lock": "GEM\n  remote: https://rubygems.org/\n  specs:\n    rack (3.0.8)\n",
}


def test_list_deps_ecosystems_are_in_the_schema_enum(tmp_path):
    for name, content in FIXTURES.items():
        (tmp_path / name).write_text(content)
    result = CliRunner().invoke(cli, ["list-deps", "--json-output", str(tmp_path)])
    assert result.exit_code == 0, result.output
    printed = {dep["ecosystem"] for dep in json.loads(result.output)}
    schema = json.loads((SCHEMAS / "depscan-list-deps.json").read_text())
    allowed = set(schema["items"]["properties"]["ecosystem"]["enum"])
    assert printed == {"cargo", "go", "npm", "pypi", "rubygems"}
    assert printed <= allowed


def test_list_deps_schema_documents_the_cargo_workspace_marker(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[dependencies]\nserde = { workspace = true }\n")
    result = CliRunner().invoke(cli, ["list-deps", "--json-output", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert [dep["version"] for dep in json.loads(result.output)] == ["workspace"]
    schema = json.loads((SCHEMAS / "depscan-list-deps.json").read_text())
    assert '"workspace"' in schema["items"]["properties"]["version"]["description"]
