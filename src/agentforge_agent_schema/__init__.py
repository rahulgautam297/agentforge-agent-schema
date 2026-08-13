"""Python accessor for the AgentForge agent YAML JSON Schema.

The schema itself is authored once, at the repository root (``agent.schema.json``),
and packaged into this wheel by hatchling's ``force-include`` mechanism (see
``pyproject.toml``) so there is a single source of truth on disk.
"""

from __future__ import annotations

import json
from importlib import resources
from importlib.resources.abc import Traversable

__all__ = ["SCHEMA_PATH", "load_schema"]

_SCHEMA_FILENAME = "agent.schema.json"

#: A ``Traversable`` pointing at the packaged schema file. Prefer
#: :func:`load_schema` for reading; this is exposed for callers that need a
#: path-like handle (e.g. to pass to another tool).
SCHEMA_PATH: Traversable = resources.files("agentforge_agent_schema").joinpath(
    _SCHEMA_FILENAME
)


def load_schema() -> dict:
    """Load and parse the AgentForge agent JSON Schema.

    Returns:
        The schema as a plain ``dict``, ready to hand to a JSON Schema
        validator such as ``jsonschema.Draft202012Validator``.
    """
    with resources.as_file(SCHEMA_PATH) as path:
        return json.loads(path.read_text(encoding="utf-8"))
