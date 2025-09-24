from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from pydolce.core.parser import CodeSegment, CodeSegmentReport, DocStatus
from pydolce.core.rules.rulesets import RuleSet, hash_ruleset

logger = logging.getLogger(__name__)


PROJECT_ROOT_INDICATORS = [
    "pyproject.toml",
    "setup.cfg",
    "requirements.txt",
    "poetry.lock",
    ".git",
]


class CacheHandler:
    def __init__(self, ruleset: RuleSet) -> None:
        self.project_root = self._get_project_root()
        self.cache_folder = self.project_root / ".pydolce" / "cache"
        self.cache_folder.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_folder / f"check_{hash_ruleset(ruleset)}.json"
        self.cache_data: dict = {}

        self.load_cache()

    def load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                with self.cache_file.open("r", encoding="utf-8") as f:
                    self.cache_data = json.load(f)
            except Exception as e:
                logger.warning("Failed to load cache file: %s", e)
                self.cache_data = {}
        else:
            self.cache_data = {}

    def sync_cache(self) -> None:
        try:
            with self.cache_file.open("w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, indent=4)
        except Exception as e:
            logger.warning("Failed to write cache file: %s", e)

    def _get_project_root(self) -> Path:
        current_path = Path.cwd()
        while current_path != current_path.parent:
            if any(
                (current_path / indicator).exists()
                for indicator in PROJECT_ROOT_INDICATORS
            ):
                return current_path
            current_path = current_path.parent
        raise RuntimeError(
            "Could not determine project root. Please ensure you are running within a valid Python project."
        )

    def _get_key(self, segment: CodeSegment) -> str:
        hasher = hashlib.sha256()
        hasher.update(segment.code_str.encode("utf-8"))
        hasher.update(str(segment.file_path).encode("utf-8"))
        hasher.update(str(segment.lineno).encode("utf-8"))
        hasher.update(segment.seg_type.name.encode("utf-8"))
        return hasher.hexdigest()

    def get_check(self, segment: CodeSegment) -> CodeSegmentReport | None:
        key = self._get_key(segment)

        if key in self.cache_data:
            report = self.cache_data[key]
            return CodeSegmentReport(
                segment=segment,
                status=DocStatus.from_str(report["status"]),
                issues=report.get("issues", []),
            )

        return None

    def set_check(
        self,
        segment: CodeSegment,
        report: CodeSegmentReport,
        sync: bool = False,
        override: bool = True,
    ) -> None:
        key = self._get_key(segment)
        if not override and key in self.cache_data:
            raise ValueError("Cache entry already exists and override is False")
        self.cache_data[key] = {
            "file": str(segment.code_path),
            "lineno": segment.lineno,
            "status": report.status.value,
            "issues": report.issues,
        }

        if sync:
            self.sync_cache()
