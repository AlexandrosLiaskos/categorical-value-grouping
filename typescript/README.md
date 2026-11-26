# Categorical Value Grouping for Thematic Symbology

[![Checks](https://github.com/AlexandrosLiaskos/categorical-value-grouping/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandrosLiaskos/categorical-value-grouping/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/categorical-value-grouping.svg)](https://pypi.org/project/categorical-value-grouping/)
[![npm](https://img.shields.io/npm/v/categorical-value-grouping.svg)](https://www.npmjs.com/package/categorical-value-grouping)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24554514.svg)](https://doi.org/10.5281/zenodo.24554514)
[![Licence: AGPL-3.0](https://img.shields.io/badge/licence-AGPL--3.0-blue.svg)](LICENSE)

A thematic map coloured by a categorical field (unique values symbology) gives each value its own colour. With many
values, a map is clearer when values are put into named groups: "Mediterranean & Black Sea", "Indo-Pacific",
"Atlantic & other waters". Each group has one colour and one row in the legend.

This library holds the rules of such groups. It comes as two packages with the same rules: Python for the server
that checks and stores the groups, and TypeScript for the browser that draws them.

| Rule                                                                                            | Python             | TypeScript        |
| ----------------------------------------------------------------------------------------------- | ------------------ | ----------------- |
| Compare values: numbers by value ("2.50" = "2.5"), yes/no without case, other values as written | `key_of`           | `keyOf`           |
| Give each group a colour by name, without two groups sharing one                                | `assign_colours`   | `assignColours`   |
| Check groups and a legend heading sent by a person, with a message for each problem             | `validate`         | `validate`        |
| Carry groups over to new data of the same field                                                 | `carry_over`       | `carryOver`       |
| Make the classes of the symbology and find the class of a value                                 | `classes_of`       | `classesOf`       |
| Count the records of each class for the legend                                                  | `legend_of`        | `legendOf`        |
| Write the colours as a MapLibre GL / Mapbox GL style expression                                 | `match_expression` | `matchExpression` |
| Describe what changed, for an activity log                                                      | `describe_changes` |                   |

Both packages pass the same test cases, [spec/vectors.json](spec/vectors.json), so a group that the server accepts is
drawn in the browser exactly as checked.

## Installation

```sh
pip install categorical-value-grouping     # Python 3.10 or later, no dependencies
npm install categorical-value-grouping     # ES module with types, no dependencies
```

## Use

A field is described as a column profile, a mapping with `name`, `kind` ("number", "date", "yes/no" or "text"),
`filter` and, for a field filtered by a list, `values`: its values with their numbers of records. A group has a
`label`, the `values` it holds (as text) and a `colour`, the name of a colour of the palette.

On the server:

```python
from categorical_value_grouping import GroupingError, validate

ocean = {"name": "ocean_sea", "kind": "text", "filter": "list", "values": [["Aegean Sea", 65], ["Ionian Sea", 8], ["Red Sea", 8]]}
try:
    checked = validate(ocean, {"groups": [{"label": "Mediterranean", "values": ["Aegean Sea", "Ionian Sea"]}], "legend_heading": "Basin"})
except GroupingError as problem:
    print(problem.code, problem.message)
else:
    print(checked)  # {'legend_heading': 'Basin', 'groups': [{'label': 'Mediterranean', 'values': [...], 'colour': 'teal'}]}
```

In the browser, with MapLibre GL JS:

```ts
import { DEFAULT_PALETTE, classesOf, legendOf, matchExpression } from "categorical-value-grouping";

const classes = classesOf("ocean_sea", "text", valuesByFrequency, config.groups);
map.setPaintProperty("records", "circle-color", matchExpression(classes, DEFAULT_PALETTE, "#94a3b8", "#0d9488"));
const rows = legendOf(classes, countsOfValues, DEFAULT_PALETTE); // [{ label, colour, count }, …]
```

## The rules

- **Values.** A value is compared by its key.
  - In a number field, a value written as a number is compared by its number, so a group that names "1.0" holds the
    records whose value is 1.
  - In a yes/no field, a value is compared without case.
  - Any other value is compared as written.
- **Groups.** A group needs a label of at most 120 characters, unique without case, and at least one value. A value
  must occur in the field and may be in only one group. There are at most as many groups as colours.
- **Colours.** A group keeps its own colour when it is a colour of the palette and no earlier group has it. A group
  without one takes the first colour that no group has. The default palette has eight colours, named teal, orange,
  red, blue, violet, amber, pink and lime; pass your own names and colours to use others.
- **Classes.** Without groups, each of the most frequent values is a class of its own, in palette order. With groups,
  each group with values is a class, and a value named twice stays with the first group. The records whose value is in
  no class are drawn as "other".
- **New data.** When the data of a field are replaced, each group keeps the values that the field still has, a group
  left without values is dropped, and the legend heading is kept.
- **Map style.** The expression is a `match` of the field's value. A number is matched by the text JavaScript gives
  it, and yes/no in lower case, so that the map colours what the server checked.

## Problems

`GroupingError` (Python) and `GroupingError` (TypeScript) carry a `code`, a `message` for the person and `details`:

`format`, `needs_unique_values`, `heading_too_long`, `too_many_groups`, `needs_value_list`, `missing_label`,
`label_too_long`, `duplicate_label`, `unknown_value`, `value_in_two_groups`, `empty_group`, `unknown_colour`,
`duplicate_colour`.

## Origin

The rules come from the WebGIS Builder of the National and Kapodistrian University of Athens. There they were written
twice, for the server and for the browser, and numbers were compared by value on the server but as text in the
browser. One set of tests for both packages ends that difference.

## Citation

Liaskos, A. (2026). _Categorical Value Grouping for Thematic Symbology_ (Version 0.1.0) [Computer software]. Zenodo.
https://doi.org/10.5281/zenodo.24554514

To cite every version at once, use the concept DOI [10.5281/zenodo.24554513](https://doi.org/10.5281/zenodo.24554513),
which always resolves to the latest release. The citation is also given in [CITATION.cff](CITATION.cff), which GitHub
offers under "Cite this repository". Each release is archived on Zenodo with its own DOI.

## Licence

Copyright © 2026 Alexandros Liaskos, National and Kapodistrian University of Athens.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
Public License, version 3, as published by the Free Software Foundation ([LICENSE](LICENSE)). It is distributed in the
hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness
for a particular purpose.
