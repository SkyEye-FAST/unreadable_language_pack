from pathlib import Path
from zipfile import ZipFile

from unreadable_language_pack.build import PackBuilder
from unreadable_language_pack.repository import ProjectLayout


def test_archive_is_reproducible_and_excludes_split_file(tmp_path: Path) -> None:
    (tmp_path / "output").mkdir()
    (tmp_path / "pack.mcmeta").write_text("{}", encoding="utf-8")
    (tmp_path / "pack.png").write_bytes(b"png")
    (tmp_path / "output" / "zh_py.json").write_text("{}", encoding="utf-8")
    (tmp_path / "output" / "en_i7h.json").write_text("{}", encoding="utf-8")
    (tmp_path / "output" / "zh_split.json").write_text("{}", encoding="utf-8")
    builder = PackBuilder(ProjectLayout.from_root(tmp_path))

    builder.create_archive(["zh_py", "zh_split", "en_i7h"])
    first = builder.layout.archive.read_bytes()
    builder.create_archive(["zh_py", "zh_split", "en_i7h"])

    assert builder.layout.archive.read_bytes() == first
    with ZipFile(builder.layout.archive) as archive:
        assert archive.namelist() == [
            "pack.mcmeta",
            "pack.png",
            "assets/minecraft/lang/en_i7h.json",
            "assets/minecraft/lang/zh_py.json",
        ]
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
