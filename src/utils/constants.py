from pathlib import Path
import os

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Core Directories
CORE_DIR = PROJECT_ROOT / "core"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"
TMP_DIR = PROJECT_ROOT / "tmp"

# Config Files
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Data Files
DB_FILE = DATA_DIR / "evolution.db"
MONITOR_STATUS_FILE = DATA_DIR / "monitor_status.json"
OPTIMIZATION_HISTORY_FILE = DATA_DIR / "optimization_history.json"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Backup/Archive
LEGACY_ARCHIVE_DIR = DATA_DIR / "legacy_archive"
DEPLOYMENT_BACKUPS_DIR = LEGACY_ARCHIVE_DIR / "deployment_backups"
ARCHIVE_DIR = LEGACY_ARCHIVE_DIR / "archive"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
