"""What changed in the groups and the legend heading, as phrases for an activity log."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


def _listed(groups: Any) -> list[dict]:
    return [group for group in groups or [] if isinstance(group, dict)]


def _names(labels: list) -> str:
    return ", ".join(f"“{label}”" for label in labels)


def describe_changes(old: Mapping[str, Any], new: Mapping[str, Any], name: Callable[[str], str], field_key: str = "colour_by") -> list[str]:
    """What differs between the groups and the legend headings of two configurations, as phrases for an activity log.

    `name` gives the name of a field in quotation marks; `field_key` is the key of the field of the symbology in a
    configuration. The groups of another field are not compared: they went with the earlier symbology.
    """
    found = []
    field = new.get(field_key)
    before = _listed(old.get("groups")) if old.get(field_key) == field else []
    after = _listed(new.get("groups"))
    if after and not before:
        labels = [group.get("label") for group in after]
        found.append(f"grouped the values of {name(field)} into {_names(labels) if len(labels) <= 3 else f'{len(labels)} groups'}")
    elif before and not after:
        found.append(f"removed the groups of values of {name(field)}")
    elif before and after:
        labels_before, labels_after = [g.get("label") for g in before], [g.get("label") for g in after]
        differ = [i for i, (a, b) in enumerate(zip(labels_before, labels_after, strict=False)) if a != b]
        if len(before) == len(after) and len(differ) == 1:
            # One label differs, at one place: that group was renamed.
            found.append(f"changed the label of the group “{labels_before[differ[0]]}” to “{labels_after[differ[0]]}”")
            pairs = list(zip(before, after, strict=True))
        else:
            added = [label for label in labels_after if label not in labels_before]
            removed = [label for label in labels_before if label not in labels_after]
            for verb, side, labels in (("added", "to", added), ("removed", "from", removed)):
                if labels:
                    found.append(f"{verb} {_names(labels) if len(labels) <= 3 else f'{len(labels)} groups'} {side} the groups of values")
            pairs = [(before[labels_before.index(g.get("label"))], g) for g in after if g.get("label") in labels_before]
            places = [labels_before.index(b.get("label")) for b, _ in pairs]
            if places != sorted(places):
                found.append("changed the order of the groups of values")
        moved = [b.get("label") for a, b in pairs if sorted(a.get("values") or []) != sorted(b.get("values") or [])]
        if len(moved) > 3:
            found.append(f"changed the values of {len(moved)} groups")
        else:
            found += [f"changed the values of the group “{label}”" for label in moved]
        recoloured = [(b.get("label"), b.get("colour")) for a, b in pairs if a.get("colour") != b.get("colour")]
        if len(recoloured) > 3:
            found.append(f"changed the colours of {len(recoloured)} groups")
        else:
            found += [f"changed the colour of the group “{label}” to {colour}" for label, colour in recoloured]
    heading_before, heading_after = old.get("legend_heading") or "", new.get("legend_heading") or ""
    if heading_before != heading_after:
        if not heading_after:
            found.append("removed the legend heading")
        elif not heading_before:
            found.append(f"set the legend heading to “{heading_after}”")
        else:
            found.append(f"changed the legend heading to “{heading_after}”")
    return found
