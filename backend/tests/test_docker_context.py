from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _dockerignore_rules(relative_path: str) -> set[str]:
    lines = (REPOSITORY_ROOT / relative_path).read_text(encoding='utf-8').splitlines()
    return {line.strip() for line in lines if line.strip() and not line.lstrip().startswith('#')}


@pytest.mark.parametrize(
    ('relative_path', 'required_rules'),
    (
        (
            'backend/.dockerignore',
            {
                '.env*',
                '**/.env*',
                '.venv/',
                '**/.venv/',
                '**/__pycache__/',
                '.pytest_cache/',
                '.ruff_cache/',
                'build/',
                'dist/',
                'staticfiles/',
                'media/',
                'db.sqlite3*',
                '*.pem',
                '*.key',
            },
        ),
        (
            'frontend/.dockerignore',
            {
                '.env*',
                '**/.env*',
                '.venv/',
                '**/.venv/',
                '**/__pycache__/',
                'node_modules/',
                '.next/',
                'out/',
                'build/',
                'dist/',
                'coverage/',
                '*.pem',
                '*.key',
            },
        ),
    ),
)
def test_docker_context_excludes_secrets_caches_and_local_output(relative_path, required_rules):
    rules = _dockerignore_rules(relative_path)
    assert required_rules <= rules
    assert not any(rule.startswith(('!.env', '!**/.env')) for rule in rules)
