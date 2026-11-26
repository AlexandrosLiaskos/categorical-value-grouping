"""The phrases of the activity log, from the cases of the WebGIS Builder."""

from categorical_value_grouping import describe_changes

MED = ["Mediterranean Sea", "Aegean Sea", "Ionian Sea", "Black Sea"]
INDO = ["Indian Ocean", "Red Sea", "Persian Gulf", "Pacific Ocean"]
ATL = ["Atlantic Ocean", "Caribbean Sea", "Lake"]


def name(field):
    return {"ocean_sea": "“Ocean sea”", "country": "“Country”"}.get(field, f"“{field}”")


def group(label, values, colour):
    return {"label": label, "values": values, "colour": colour}


med, indo, atl = group("Mediterranean", MED, "red"), group("Indo-Pacific", INDO, "teal"), group("Atlantic & other waters", ATL, "orange")
PLAIN = {"colour_by": "ocean_sea"}
GROUPED = {"colour_by": "ocean_sea", "groups": [med, indo, atl], "legend_heading": "Ocean basin"}


def test_groups_added_and_removed():
    assert describe_changes(PLAIN, GROUPED, name) == [
        "grouped the values of “Ocean sea” into “Mediterranean”, “Indo-Pacific”, “Atlantic & other waters”",
        "set the legend heading to “Ocean basin”",
    ]
    assert describe_changes(GROUPED, PLAIN, name) == ["removed the groups of values of “Ocean sea”", "removed the legend heading"]


def test_a_group_renamed_recoloured_or_given_other_values():
    renamed = dict(GROUPED, groups=[dict(med, label="Mediterranean & Black Sea"), indo, atl])
    assert describe_changes(GROUPED, renamed, name) == ["changed the label of the group “Mediterranean” to “Mediterranean & Black Sea”"]
    recoloured = dict(GROUPED, groups=[dict(med, colour="blue"), indo, atl])
    assert describe_changes(GROUPED, recoloured, name) == ["changed the colour of the group “Mediterranean” to blue"]
    moved = dict(GROUPED, groups=[dict(med, values=MED[:-1]), dict(indo, values=[*INDO, "Black Sea"]), atl])
    assert describe_changes(GROUPED, moved, name) == [
        "changed the values of the group “Mediterranean”",
        "changed the values of the group “Indo-Pacific”",
    ]


def test_groups_reordered_added_or_removed():
    assert describe_changes(GROUPED, dict(GROUPED, groups=[atl, med, indo]), name) == ["changed the order of the groups of values"]
    fewer = dict(GROUPED, groups=[med, indo])
    assert describe_changes(GROUPED, fewer, name) == ["removed “Atlantic & other waters” from the groups of values"]
    assert describe_changes(fewer, GROUPED, name) == ["added “Atlantic & other waters” to the groups of values"]


def test_the_groups_of_another_field_are_not_compared():
    assert describe_changes(GROUPED, {"colour_by": "country"}, name) == ["removed the legend heading"]


def test_the_heading_changed():
    assert describe_changes(GROUPED, dict(GROUPED, legend_heading="Basin"), name) == ["changed the legend heading to “Basin”"]
