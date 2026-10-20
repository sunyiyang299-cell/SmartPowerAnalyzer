"""Project-owned runtime resources; never use the process working directory."""
from pathlib import Path


def resource_path(name):
    base = Path(__file__).resolve().parent / 'assets'
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError('资源路径必须位于应用资源目录。')
    return path
