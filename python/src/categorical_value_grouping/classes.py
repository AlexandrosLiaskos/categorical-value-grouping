"""The classes of unique values symbology: which colour each value takes, the legend, and the map style expression."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .model import DEFAULT_COLOUR_NAMES, Key, assign_colours, key_of, key_text


@dataclass(frozen=True)
class Classes:
    """The classes of a field, in the order of the legend.

    `labels`, `members` (the values of each class, as written) and `places` (the place of the colour of each class in
    the palette) run in parallel. `grouped` tells whether the classes are groups or single values.
    """

    field: str | None
    kind: str | None = None
    grouped: bool = False
    labels: tuple[str, ...] = ()
    members: tuple[tuple[str, ...], ...] = ()
    places: tuple[int, ...] = ()
    _class_of: Mapping[Key, int] = field(default_factory=dict, repr=False)

    def class_of(self, value: Any) -> int:
        """The class of a value, or -1 for a value drawn as Other."""
        return self._class_of.get(key_of(self.kind, value), -1)

    def colours(self, palette: Sequence[str]) -> list[str]:
        """The colour of each class from a palette in the order of the colour names."""
        return [palette[place] if place < len(palette) else palette[0] for place in self.places]


def classes_of(
    field_name: str | None,
    kind: str | None,
    categories: Sequence[str],
    groups: Sequence[Mapping[str, Any]] | None,
    colour_names: Sequence[str] = DEFAULT_COLOUR_NAMES,
) -> Classes:
    """The classes of unique values symbology.

    Without groups, each of the most frequent values (`categories`, the most frequent first) is a class of its own, in
    the colour of its place. With groups, each group with values is a class, in the colour of its name; a value named
    in two groups stays with the first. Values are compared by their keys (see key_of).
    """
    if not field_name:
        return Classes(field=None, kind=kind)
    size = len(colour_names)
    listed = [group for group in (groups or []) if group.get("values")][:size]
    if not listed:
        used = list(categories[:size])
        return Classes(
            field=field_name,
            kind=kind,
            grouped=False,
            labels=tuple(used),
            members=tuple((value,) for value in used),
            places=tuple(range(len(used))),
            _class_of={key_of(kind, value): at for at, value in enumerate(used)},
        )
    places: dict[Key, int] = {}
    members = []
    for at, group in enumerate(listed):
        own = []
        for value in group["values"]:
            key = key_of(kind, value)
            if key in places:
                continue
            places[key] = at
            own.append(value)
        members.append(tuple(own))
    names = assign_colours(listed, colour_names)
    return Classes(
        field=field_name,
        kind=kind,
        grouped=True,
        labels=tuple(str(group.get("label", "")) for group in listed),
        members=tuple(members),
        places=tuple(colour_names.index(name) for name in names),
        _class_of=places,
    )


def legend_of(classes: Classes, counted: Sequence[Sequence[Any]], palette: Sequence[str]) -> list[dict[str, Any]]:
    """The rows of the legend, each with a label, a colour and a number of records. Without groups, the values that
    have a colour, in the order of `counted` (each value with its number of records); with groups, every group in its
    order with the records of its values."""
    colours = classes.colours(palette)
    if not classes.grouped:
        rows = []
        for value, number in counted:
            at = classes.class_of(value)
            if at >= 0:
                rows.append({"label": str(value), "colour": colours[at], "count": number})
        return rows
    totals = [0] * len(classes.labels)
    for value, number in counted:
        at = classes.class_of(value)
        if at >= 0:
            totals[at] += number
    return [{"label": label, "colour": colours[at], "count": totals[at]} for at, label in enumerate(classes.labels)]


def match_expression(classes: Classes, palette: Sequence[str], other: Any, plain: Any) -> Any:
    """The colour of the records as a MapLibre GL / Mapbox GL style expression: a "match" of the value of the field,
    with `other` for every value in no class. Values are matched by their keys: a number by the text JavaScript gives
    it, yes or no in lower case. Without a field the records take `plain`."""
    if not classes.field:
        return plain
    if classes.kind == "yes/no":
        value: list = ["downcase", ["to-string", ["get", classes.field]]]
    else:
        value = ["to-string", ["get", classes.field]]
    colours = classes.colours(palette)
    branches: list[Any] = []
    for at, members in enumerate(classes.members):
        labels = list(dict.fromkeys(key_text(key_of(classes.kind, member)) for member in members))
        if labels:
            branches += [labels[0] if len(labels) == 1 else labels, colours[at]]
    if not branches:
        return other if classes.grouped else plain
    return ["match", value, *branches, other]
