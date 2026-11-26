"""Categorical Value Grouping for Thematic Symbology.

Named groups of the values of a categorical field for unique values symbology: checked, carried over to new data,
coloured, counted in a legend and written as a map style expression, with the same rules as the TypeScript package of
the same name.

Copyright (C) 2026 Alexandros Liaskos
SPDX-License-Identifier: AGPL-3.0-only
"""

from .changes import describe_changes
from .classes import Classes, classes_of, legend_of, match_expression
from .model import (
    DEFAULT_COLOUR_NAMES,
    DEFAULT_PALETTE,
    DEFAULT_RINGS,
    MAX_LABEL,
    assign_colours,
    key_of,
    key_text,
    number_text,
    tidy,
    values_of,
)
from .validation import GroupingError, carry_over, validate

__all__ = [
    "DEFAULT_COLOUR_NAMES",
    "DEFAULT_PALETTE",
    "DEFAULT_RINGS",
    "MAX_LABEL",
    "Classes",
    "GroupingError",
    "assign_colours",
    "carry_over",
    "classes_of",
    "describe_changes",
    "key_of",
    "key_text",
    "legend_of",
    "match_expression",
    "number_text",
    "tidy",
    "validate",
    "values_of",
]
__version__ = "0.1.0"
