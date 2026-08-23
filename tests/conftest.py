from pathlib import Path

import pytest

from unreadable_language_pack.converters import ChineseConverter
from unreadable_language_pack.repository import DataRepository, ProjectLayout


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repository(project_root: Path) -> DataRepository:
    return DataRepository(ProjectLayout.from_root(project_root))


@pytest.fixture(scope="session")
def chinese_converter(repository: DataRepository) -> ChineseConverter:
    return ChineseConverter(repository)
