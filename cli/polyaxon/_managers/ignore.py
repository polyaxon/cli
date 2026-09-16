from collections import namedtuple
import io
import os
from pathlib import PurePath
import re
from typing import List, Optional, Tuple

from clipped.utils.lists import to_list
from clipped.utils.paths import unix_style_path
from polyaxon._config.manager import ConfigManager
from polyaxon._utils import cli_constants
from polyaxon._utils.cli_constants import SYMLINK_MODES
from polyaxon.exceptions import PolyaxonClientException
from polyaxon.logger import logger


class Pattern(namedtuple("Pattern", "pattern is_exclude re")):
    @staticmethod
    def create(pattern: str) -> "Pattern":
        if pattern[0:1] == "!":
            is_exclude = False
            pattern = pattern[1:]
        else:
            if pattern[0:1] == "\\":
                pattern = pattern[1:]
            is_exclude = True
        return Pattern(
            pattern=pattern,
            is_exclude=is_exclude,
            re=re.compile(translate(pattern), re.IGNORECASE),
        )

    def match(self, path: str) -> bool:
        return bool(self.re.match(path))


def translate(pat: str) -> str:
    def _translate_segment():
        # pylint:disable=undefined-loop-variable
        if segment == "*":
            return "[^/]+"
        res = ""
        i, n = 0, len(segment)
        while i < n:
            c = segment[i : i + 1]
            i = i + 1
            if c == "*":
                res += "[^/]*"
            elif c == "?":
                res += "[^/]"
            elif c == "[":
                j = i
                if j < n and segment[j : j + 1] == "!":
                    j = j + 1
                if j < n and segment[j : j + 1] == "]":
                    j = j + 1
                while j < n and segment[j : j + 1] != "]":
                    j = j + 1
                if j >= n:
                    res += "\\["
                else:
                    stuff = segment[i:j].replace("\\", "\\\\")
                    i = j + 1
                    if stuff.startswith("!"):
                        stuff = "^" + stuff[1:]
                    elif stuff.startswith("^"):
                        stuff = "\\" + stuff
                    res += "[" + stuff + "]"
            else:
                res += re.escape(c)
        return res

    res = "(?ms)"

    if pat.startswith("**/"):
        pat = pat[2:]
        res += "(.*/)?"

    if pat.startswith("/"):
        pat = pat[1:]
    else:
        res += "(.*/)?"

    for i, segment in enumerate(pat.split("/")):
        if segment == "**":
            res += "(/.*)?"
            continue
        else:
            res += (re.escape("/") if i > 0 else "") + _translate_segment()

    if not pat.endswith("/"):
        res += "/?"

    return res + "\\Z"


class IgnoreConfigManager(ConfigManager):
    """Manages .polyaxonignore file in the current directory"""

    VISIBILITY = ConfigManager.Visibility.LOCAL
    CONFIG_FILE_NAME = ".polyaxonignore"

    @staticmethod
    def _is_empty_or_comment(line: str) -> bool:
        return not line or line.startswith("#")

    @staticmethod
    def _remove_trailing_spaces(line: str) -> str:
        """Remove trailing spaces unless they are quoted with a backslash."""
        while line.endswith(" ") and not line.endswith("\\ "):
            line = line[:-1]
        return line.replace("\\ ", " ")

    @classmethod
    def init_config(cls):
        cls.set_config(cli_constants.DEFAULT_IGNORE_LIST, init=True)

    @classmethod
    def find_matching(cls, path: str, patterns: List[Pattern]) -> List[Pattern]:
        """Yield all matching patterns for path."""
        for pattern in patterns:
            if pattern.match(path):
                yield pattern

    @classmethod
    def is_ignored(
        cls, path: str, patterns: List[Pattern], is_dir: bool = False
    ) -> bool:
        """Check whether a path is ignored. For directories, include a trailing slash."""
        status = None
        path = "{}/".format(path.rstrip("/")) if is_dir else path
        for pattern in cls.find_matching(path, patterns):
            status = pattern.is_exclude
        return status

    @classmethod
    def read_file(cls, ignore_file: List[str]) -> List[str]:
        for line in ignore_file:
            line = line.rstrip("\r\n")

            if cls._is_empty_or_comment(line):
                continue

            yield cls._remove_trailing_spaces(line)

    @classmethod
    def get_patterns(cls, ignore_file: List[str]) -> List[Pattern]:
        return [Pattern.create(line) for line in cls.read_file(ignore_file)]

    @staticmethod
    def get_push_patterns() -> List[Pattern]:
        return [
            Pattern.create("*.plx.json"),
            Pattern.create("*.plx.index"),
            Pattern.create("./.polyaxon"),
        ]

    @classmethod
    def get_config(cls) -> List[Pattern]:
        config_filepath = cls.get_config_filepath()

        if not os.path.isfile(config_filepath):
            # Return default patterns
            return cls.get_patterns(io.StringIO(cli_constants.DEFAULT_IGNORE_LIST))

        with open(config_filepath) as ignore_file:
            return cls.get_patterns(ignore_file)

    @staticmethod
    def _is_inside_root(target: str, upload_root: str) -> bool:
        try:
            return os.path.commonpath([upload_root, target]) == upload_root
        except ValueError:
            return False

    @classmethod
    def _is_ignored_target(
        cls,
        target: str,
        is_dir: bool,
        path: str,
        upload_root: str,
        config: List[Pattern],
    ) -> bool:
        relative = os.path.relpath(target, upload_root)
        while relative != ".":
            target_path = unix_style_path(os.path.join(path, relative))
            if cls.is_ignored(target_path, config, is_dir=is_dir):
                return True
            relative = os.path.dirname(relative) or "."
            is_dir = True
        return False

    @classmethod
    def _check_path(
        cls,
        filepath: str,
        path: str,
        upload_root: str,
        config: List[Pattern],
        symlink_mode: str,
        is_dir: bool = False,
        through_link: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Return whether to include the path and any symlink report reason."""
        if cls.is_ignored(unix_style_path(filepath), config, is_dir=is_dir):
            if is_dir:
                logger.debug("Ignoring directory : %s", filepath)
            return False, None
        is_link = os.path.islink(filepath)
        resolve_links = symlink_mode in ("resolve-safe", "resolve-all")
        if is_link and not resolve_links:
            return False, (
                "skipped" if symlink_mode == "skip" else "symlinks are forbidden"
            )

        if not is_link and not through_link:
            return True, None

        target = os.path.realpath(filepath)
        internal = cls._is_inside_root(target, upload_root)
        if (
            resolve_links
            and internal
            and cls._is_ignored_target(target, is_dir, path, upload_root, config)
        ):
            if is_dir:
                logger.debug("Ignoring directory : %s", filepath)
            return False, None
        if not is_link:
            return True, None

        reason: Optional[str] = None
        if symlink_mode == "resolve-safe" and not internal:
            reason = "link target is outside the upload root"
        elif not os.path.exists(filepath):
            reason = "broken link or symlink cycle"
        elif is_dir and any(
            target == os.path.realpath(os.path.join(path, parent))
            for parent in PurePath(os.path.relpath(filepath, path)).parents
        ):
            reason = "directory symlink cycle"
        elif not is_dir and not os.path.isfile(filepath):
            reason = "target is not a regular file or directory"
        return reason is None, reason

    @classmethod
    def get_unignored_filepaths(
        cls,
        path: Optional[str] = None,
        addtional_patterns: Optional[List[Pattern]] = None,
        symlink_mode: str = "skip",
        symlink_report_limit: int = 20,
    ) -> List[str]:
        if symlink_mode not in SYMLINK_MODES:
            raise PolyaxonClientException(
                "Unknown symlink mode '{}'. Choose from: {}.".format(
                    symlink_mode, ", ".join(SYMLINK_MODES)
                )
            )
        if symlink_report_limit < 0:
            raise PolyaxonClientException("Symlink report limit must be nonnegative.")

        config = to_list(cls.get_config(), check_none=True)
        config += to_list(addtional_patterns, check_none=True)
        unignored_files: List[str] = []
        path = path or "."
        upload_root = os.path.realpath(path)
        resolve_links = symlink_mode in ("resolve-safe", "resolve-all")
        details: List[str] = []
        link_count = 0

        def report(filepath, reason):
            nonlocal link_count
            link_count += 1
            if len(details) < symlink_report_limit:
                details.append(
                    "{} -> {}: {}".format(filepath, os.readlink(filepath), reason)
                )

        for root, dirs, files in os.walk(path, followlinks=resolve_links):
            logger.debug("Root:%s, Dirs:%s", root, dirs)
            if cls.is_ignored(unix_style_path(root), config, is_dir=True):
                dirs[:] = []
                logger.debug("Ignoring directory : %s", root)
                continue

            through_link = resolve_links and os.path.realpath(root) != os.path.normpath(
                os.path.join(upload_root, os.path.relpath(root, path))
            )
            # Keep directory entries reached through links, including empty ones.
            if through_link:
                unignored_files.append(root)

            for name in dirs[:]:
                filepath = os.path.join(root, name)
                include, reason = cls._check_path(
                    filepath,
                    path=path,
                    upload_root=upload_root,
                    config=config,
                    symlink_mode=symlink_mode,
                    is_dir=True,
                    through_link=through_link,
                )
                if reason:
                    report(filepath, reason)
                if not include:
                    dirs.remove(name)

            for file_name in files:
                filepath = os.path.join(root, file_name)
                include, reason = cls._check_path(
                    filepath,
                    path=path,
                    upload_root=upload_root,
                    config=config,
                    symlink_mode=symlink_mode,
                    through_link=through_link,
                )
                if reason:
                    report(filepath, reason)
                if include:
                    unignored_files.append(filepath)

        if link_count:
            action = "Skipped" if symlink_mode == "skip" else "Rejected"
            message = "{} {} symlink(s) under '{}' in '{}' mode.".format(
                action, link_count, path, symlink_mode
            )
            if details:
                message += "\n" + "\n".join(details)
            if link_count > len(details):
                message += "\n{} more symlink(s) not shown.".format(
                    link_count - len(details)
                )
            if symlink_mode == "skip":
                logger.warning(message)
            else:
                raise PolyaxonClientException(
                    message + "\nRepair the links, add them to .polyaxonignore, or use "
                    "--symlink-mode skip. Use resolve-safe to materialize internal links; "
                    "choose resolve-all only to intentionally include external targets."
                )

        return unignored_files

    @staticmethod
    def _matches_patterns(path: str, patterns: List[str]) -> bool:
        """Given a list of patterns, returns a if a path matches any pattern."""
        for glob in patterns:
            try:
                if PurePath(path).match(glob):
                    return True
            except TypeError:
                pass
        return False

    @classmethod
    def _ignore_path(
        cls,
        path: str,
        ignore_list: Optional[List[str]] = None,
        allowed_list: Optional[List[str]] = None,
    ) -> bool:
        """Returns a whether a path should be ignored or not."""
        ignore_list = ignore_list or []
        allowed_list = allowed_list or []
        return cls._matches_patterns(path, ignore_list) and not cls._matches_patterns(
            path, allowed_list
        )

    @classmethod
    def get_value(cls, key: str):
        pass
