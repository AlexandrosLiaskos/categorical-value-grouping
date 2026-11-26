"""Values, their comparison keys, and the named colours of the groups.

A field is described as a column profile: a mapping with `name`, `kind` ("number", "date", "yes/no" or "text"),
`filter` and, for a field filtered by a list, `values`, its values with their numbers of records. A group is a mapping
with a `label`, the `values` it holds, written as text, and a `colour`, the name of a colour of the palette.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

#: The names of the colours of the symbology, in the order of the palette.
DEFAULT_COLOUR_NAMES = ("teal", "orange", "red", "blue", "violet", "amber", "pink", "lime")
#: The colours themselves, and a lighter ring of each, in the same order.
DEFAULT_PALETTE = ("#0d9488", "#f97316", "#dc2626", "#2563eb", "#7c3aed", "#ca8a04", "#db2777", "#65a30d")
DEFAULT_RINGS = ("#5eead4", "#fdba74", "#f87171", "#93c5fd", "#c4b5fd", "#fde047", "#f9a8d4", "#bef264")
#: The longest label of a group and the longest legend heading.
MAX_LABEL = 120

_NUMBER = re.compile(r"^\s*[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?\s*$")

Key = float | str


def key_of(kind: str | None, value: Any) -> Key:
    """A value as it is compared: a number by its value ("2.50" and "2.5" are the same), yes or no without case, any other
    value as written. A value of a number field that is not written as a number is compared as written."""
    text = str(value)
    if kind == "number" and _NUMBER.match(text):
        return float(text)
    return text.lower() if kind == "yes/no" else text


def number_text(number: float) -> str:
    """A number as JavaScript writes it (Number.prototype.toString): "1", "2.5", "0.00001", "1e-7", "1e+21"."""
    if number != number or number in (float("inf"), float("-inf")):
        return {True: "NaN", False: "Infinity" if number > 0 else "-Infinity"}[number != number]
    if number == 0:
        return "0"
    sign = "-" if number < 0 else ""
    mantissa, _, exponent = repr(abs(float(number))).partition("e")
    digits, point = mantissa.replace(".", ""), mantissa.find(".")
    # The decimal digits and the place of the point after the first digit, from Python's shortest representation.
    place = (point if point >= 0 else len(mantissa)) + (int(exponent) if exponent else 0)
    stripped = digits.lstrip("0")
    place -= len(digits) - len(stripped)
    digits = stripped.rstrip("0") or "0"
    if -6 < place <= 21:
        if place <= 0:
            return f"{sign}0.{'0' * -place}{digits}"
        if place >= len(digits):
            return f"{sign}{digits}{'0' * (place - len(digits))}"
        return f"{sign}{digits[:place]}.{digits[place:]}"
    power = place - 1
    shown = digits[0] + (f".{digits[1:]}" if len(digits) > 1 else "")
    return f"{sign}{shown}e{'+' if power > 0 else '-'}{abs(power)}"


def key_text(key: Key) -> str:
    """A key as the text that a map style compares: a number as JavaScript writes it."""
    return number_text(key) if isinstance(key, float) else key


def values_of(field: Mapping[str, Any] | None) -> set[Key] | None:
    """The keys of the values of a field, or None for a field that is not filtered by a list of its values."""
    listed = field.get("values") if field else None
    if field is None or field.get("filter") != "list" or listed is None:
        return None
    return {key_of(field.get("kind"), value) for value, _count in listed}


def tidy(text: Any) -> str:
    """A label with its runs of spaces made one and no space at either end."""
    return " ".join(str(text or "").split())


def assign_colours(groups: Sequence[Mapping[str, Any]], names: Sequence[str] = DEFAULT_COLOUR_NAMES) -> list[str]:
    """The colour of each group, by name. A group keeps its own colour when it is one of `names` and no earlier group has
    it; any other group takes the first colour that no group has, or the first colour when none is free."""
    taken: set[str] = set()
    own: list[str | None] = []
    for group in groups:
        colour = group.get("colour")
        if colour in names and colour not in taken:
            taken.add(colour)
            own.append(colour)
        else:
            own.append(None)
    result = []
    for colour in own:
        if colour is None:
            colour = next((name for name in names if name not in taken), names[0])
            taken.add(colour)
        result.append(colour)
    return result
