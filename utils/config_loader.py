"""Configuration loader.

Reads `config/config.json`, picks the active profile from the `PROFILE`
env var (default: 'default'), and lets a few env vars override specific keys.

Env vars come from two places:
  1. The `.env` file — loaded once by `conftest.py` using `python-dotenv`.
  2. The shell command — vars set inline like `HEADLESS=false pytest`.
If the same var is set in both places, the shell value wins.

See README -> Configuration & Profiles for the full table.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.json"


def _parse_bool(s: str) -> bool:
    s = s.lower().strip()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    raise ValueError(f"cannot parse {s!r} as bool")


# Env vars that override matching keys in the config dict.
# Format: env_var -> (config_key, parser_function)
ENV_OVERRIDES: dict[str, tuple[str, Any]] = {
    "HEADLESS": ("headless", _parse_bool),
    "SLOW_MO": ("slow_mo", int),
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load the merged configuration: default + active profile + env overrides.

    Merge order:
        1. The `default` block (always loaded)
        2. The active profile (from `PROFILE`, falls back to `default`)
        3. Env-var overrides for selected keys (HEADLESS, SLOW_MO)

    Shallow merge: if a profile defines `thresholds`, its dict replaces the
    full `thresholds` from `default`. It does not merge inner keys.
    See README -> Limitations.
    """
    path = config_path or CONFIG_PATH
    with path.open() as f:
        raw = json.load(f)

    if "default" not in raw:
        raise RuntimeError(f"config.json missing 'default' profile at {path}")

    profile_name = os.getenv("PROFILE", "default")
    if profile_name not in raw:
        logger.warning(
            "PROFILE=%r not found in config.json, falling back to 'default'",
            profile_name,
        )
        profile_name = "default"

    config = {**raw["default"], **raw[profile_name]}

    for env_var, (config_key, parser) in ENV_OVERRIDES.items():
        raw_value = os.getenv(env_var)
        if raw_value is None:
            continue
        try:
            config[config_key] = parser(raw_value)
            logger.info(
                "env override: %s -> config[%r] = %r",
                env_var,
                config_key,
                config[config_key],
            )
        except (ValueError, TypeError) as e:
            logger.warning(
                "invalid value for %s=%r: %s -- ignoring override",
                env_var,
                raw_value,
                e,
            )

    return config


def get_credentials() -> tuple[str | None, str | None]:
    """Return (OL_USERNAME, OL_PASSWORD) from env vars. Either is None if not set."""
    return os.getenv("OL_USERNAME"), os.getenv("OL_PASSWORD")
