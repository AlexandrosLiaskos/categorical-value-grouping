"""The check of the groups and the legend heading that a person sends, and their carry-over to new data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .model import DEFAULT_COLOUR_NAMES, MAX_LABEL, key_of, tidy, values_of

FORMAT = "The groups of values are not in the expected format."


class GroupingError(ValueError):
    """Groups that cannot be kept. `code` names the problem; `message` is a sentence for the person; `details` holds
    the values it names.

    Codes: format, needs_unique_values, heading_too_long, too_many_groups, needs_value_list, missing_label,
    label_too_long, duplicate_label, unknown_value, value_in_two_groups, empty_group, unknown_colour, duplicate_colour.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def validate(field: Mapping[str, Any] | None, config: Mapping[str, Any], colour_names: Sequence[str] = DEFAULT_COLOUR_NAMES) -> dict:
    """The groups and the legend heading of `config`, checked and tidied; {} when there are none.

    `field` is the field of the symbology (a column profile), or None for a single symbol. Labels and the heading lose
    their extra spaces. Values are compared by their keys (see key_of) and kept as written. A group without a colour
    takes the first colour that no other group has. Raises GroupingError.
    """
    groups, heading = config.get("groups"), config.get("legend_heading")
    if groups in (None, []) and heading in (None, ""):
        return {}
    if (groups is not None and not isinstance(groups, list)) or (heading is not None and not isinstance(heading, str)):
        raise GroupingError("format", FORMAT)
    if field is None:
        raise GroupingError("needs_unique_values", "Groups of values and a legend heading require unique values symbology.")
    found: dict[str, Any] = {}
    heading = tidy(heading)
    if len(heading) > MAX_LABEL:
        raise GroupingError("heading_too_long", f"The legend heading exceeds {MAX_LABEL} characters.", limit=MAX_LABEL)
    if heading:
        found["legend_heading"] = heading
    groups = groups or []
    if not groups:
        return found
    if len(groups) > len(colour_names):
        raise GroupingError(
            "too_many_groups",
            f"The groups of values are limited to {len(colour_names)}, one for each colour of the symbology.",
            limit=len(colour_names),
        )
    known = values_of(field)
    if known is None:
        raise GroupingError("needs_value_list", "Groups of values are available for fields with a list of values.")
    kind = field.get("kind")
    labels: set[str] = set()
    placed: set = set()
    colours: set[str] = set()
    result = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("values"), list):
            raise GroupingError("format", FORMAT)
        if any(not isinstance(value, str) for value in group["values"]):
            raise GroupingError("format", FORMAT)
        label = tidy(group.get("label"))
        if not label:
            raise GroupingError("missing_label", "Enter the label of each group.")
        if len(label) > MAX_LABEL:
            raise GroupingError("label_too_long", f"A group label exceeds {MAX_LABEL} characters.", limit=MAX_LABEL)
        if label.lower() in labels:
            raise GroupingError("duplicate_label", f"The label “{label}” is used by more than one group.", label=label)
        labels.add(label.lower())
        values = []
        for value in group["values"]:
            key = key_of(kind, value)
            if key not in known:
                raise GroupingError("unknown_value", f"The value “{value}” does not occur in the field of the symbology.", value=value)
            if key in placed:
                raise GroupingError("value_in_two_groups", f"The value “{value}” is in more than one group.", value=value)
            placed.add(key)
            values.append(value)
        if not values:
            raise GroupingError("empty_group", f"The group “{label}” contains no values.", label=label)
        colour = group.get("colour") or None
        if colour is not None and colour not in colour_names:
            raise GroupingError("unknown_colour", f"The colour of the group “{label}” is not a colour of the symbology.", label=label)
        if colour in colours:
            raise GroupingError("duplicate_colour", "Each group must have a colour of its own.", colour=colour)
        if colour:
            colours.add(colour)
        result.append({"label": label, "values": values, "colour": colour})
    free = [name for name in colour_names if name not in colours]
    for item in result:
        if item["colour"] is None:
            item["colour"] = free.pop(0)
    found["groups"] = result
    return found


def carry_over(previous: Mapping[str, Any], field: Mapping[str, Any] | None) -> dict:
    """The groups and the legend heading of `previous` for the same field in new data.

    The heading is kept. Each group keeps the values that the field still has, and a group left without any is dropped.
    A value in two groups stays with the first. A field without a list of its values keeps no groups.
    """
    found: dict[str, Any] = {}
    heading = tidy(previous.get("legend_heading") if isinstance(previous.get("legend_heading"), str) else "")
    if heading:
        found["legend_heading"] = heading[:MAX_LABEL]
    known = values_of(field)
    if field is None or known is None:
        return found
    kind = field.get("kind")
    groups, placed = [], set()
    for group in previous.get("groups") or []:
        if not isinstance(group, dict):
            continue
        values = []
        for value in group.get("values") or []:
            key = key_of(kind, value) if isinstance(value, str) else None
            if key is not None and key in known and key not in placed:
                placed.add(key)
                values.append(value)
        if values:
            groups.append({**group, "values": values})
    if groups:
        found["groups"] = groups
    return found
