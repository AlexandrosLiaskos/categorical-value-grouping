"""The shared test cases of spec/vectors.json, which the TypeScript package runs as well."""

import json
from pathlib import Path

import pytest

from categorical_value_grouping import (
    GroupingError,
    assign_colours,
    carry_over,
    classes_of,
    key_of,
    legend_of,
    match_expression,
    number_text,
    validate,
)

VECTORS = json.loads((Path(__file__).parents[2] / "spec" / "vectors.json").read_text(encoding="utf-8"))
NAMES = VECTORS["colour_names"]


@pytest.mark.parametrize("case", VECTORS["keys"], ids=lambda c: f"{c['kind']}:{c['value']}")
def test_keys(case):
    assert key_of(case["kind"], case["value"]) == case["key"]


@pytest.mark.parametrize("case", VECTORS["number_texts"], ids=lambda c: c["text"])
def test_number_texts(case):
    assert number_text(float(case["number"])) == case["text"]


@pytest.mark.parametrize("case", VECTORS["colours"], ids=lambda c: c["about"])
def test_colours(case):
    assert assign_colours(case["groups"], NAMES) == case["expected"]


@pytest.mark.parametrize("case", VECTORS["validate_ok"], ids=lambda c: c["about"])
def test_validate(case):
    assert validate(case["field"], case["config"], NAMES) == case["expected"]


@pytest.mark.parametrize("case", VECTORS["validate_errors"], ids=lambda c: c["code"])
def test_validate_refuses(case):
    with pytest.raises(GroupingError) as refused:
        validate(case["field"], case["config"], NAMES)
    assert (refused.value.code, refused.value.message) == (case["code"], case["message"])


@pytest.mark.parametrize("case", VECTORS["carry_over"], ids=lambda c: c["about"])
def test_carry_over(case):
    assert carry_over(case["previous"], case["field"]) == case["expected"]


def made(case):
    return classes_of(case["field"], case["kind"], case["categories"], case["groups"], NAMES)


@pytest.mark.parametrize("case", VECTORS["classes"], ids=lambda c: c["about"])
def test_classes(case):
    classes = made(case)
    assert classes.grouped == case["grouped"]
    assert list(classes.labels) == case["labels"]
    assert [list(m) for m in classes.members] == case["members"]
    assert classes.colours(NAMES) == case["colours"]
    assert {value: classes.class_of(value) for value in case["class_of"]} == case["class_of"]


@pytest.mark.parametrize("case", VECTORS["legend"], ids=lambda c: c["about"])
def test_legend(case):
    rows = legend_of(made(VECTORS["classes"][case["classes"]]), case["counted"], NAMES)
    assert rows == case["rows"]


@pytest.mark.parametrize("case", VECTORS["match"], ids=lambda c: c["about"])
def test_match(case):
    assert match_expression(made(VECTORS["classes"][case["classes"]]), NAMES, "OTHER", "PLAIN") == case["expression"]
