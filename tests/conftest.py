from pathlib import Path

import pytest

from unreadable_language_pack.converters import MandarinConverter
from unreadable_language_pack.repository import LanguageDataRepository, ProjectLayout


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repository(project_root: Path) -> LanguageDataRepository:
    return LanguageDataRepository(ProjectLayout.from_root(project_root))


@pytest.fixture(scope="session")
def mandarin_converter(repository: LanguageDataRepository) -> MandarinConverter:
    return MandarinConverter(repository)
