"""Load test data from JSON files in the project's data/ directory.

Single resolution point for the data path. Test modules import
`load_data` and pass a filename; the helper returns the parsed JSON
list, ready to feed `@pytest.mark.parametrize`.

Why a helper at all (and not inline `json.load` per test): the path
resolution is identical across files, and a typo in `Path(__file__).parent.parent`
would silently look in the wrong place. Centralising it keeps each
test file focused on its cases, not on how to find them.
"""

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"


def load_data(filename: str) -> list[dict[str, Any]]:
    """Read `data/<filename>` and return the parsed JSON list of cases."""
    return json.loads((DATA_DIR / filename).read_text())
