"""Path utilities for centralized directory management."""

from pathlib import Path


def get_repo_root() -> Path:
    """Get the repository root directory.

    Returns:
        Path to python-projects repository root
    """
    # From src/utils/paths.py, go up to mongo_backup_tools, then up to python-projects
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # src/utils/ -> src/ -> mongo_backup_tools/
    repo_root = project_root.parent  # mongo_backup_tools/ -> python-projects/
    return repo_root


def get_logs_dir() -> Path:
    """Get centralized logs directory for this project.

    Returns:
        Path to logs/mongo_backup_tools/
    """
    logs_dir = get_repo_root() / "logs" / "mongo_backup_tools"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_output_dir() -> Path:
    """Get centralized output directory for this project.

    Returns:
        Path to data/output/mongo_backup_tools/
    """
    output_dir = get_repo_root() / "data" / "output" / "mongo_backup_tools"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_input_dir() -> Path:
    """Get centralized input directory for this project.

    Returns:
        Path to data/input/mongo_backup_tools/
    """
    input_dir = get_repo_root() / "data" / "input" / "mongo_backup_tools"
    input_dir.mkdir(parents=True, exist_ok=True)
    return input_dir
