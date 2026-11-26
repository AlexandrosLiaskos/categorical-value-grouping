/**
 * Categorical Value Grouping for Thematic Symbology.
 *
 * Named groups of the values of a categorical field for unique values symbology: checked, carried over to new data,
 * coloured, counted in a legend and written as a map style expression, with the same rules as the Python package of the
 * same name. Both packages pass the shared cases of spec/vectors.json.
 *
 * Copyright (C) 2026 Alexandros Liaskos
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/** The names of the colours of the symbology, in the order of the palette. */
export const DEFAULT_COLOUR_NAMES: readonly string[] = ["teal", "orange", "red", "blue", "violet", "amber", "pink", "lime"];
/** The colours themselves, and a lighter ring of each, in the same order. */
export const DEFAULT_PALETTE: readonly string[] = ["#0d9488", "#f97316", "#dc2626", "#2563eb", "#7c3aed", "#ca8a04", "#db2777", "#65a30d"];
export const DEFAULT_RINGS: readonly string[] = ["#5eead4", "#fdba74", "#f87171", "#93c5fd", "#c4b5fd", "#fde047", "#f9a8d4", "#bef264"];
/** The longest label of a group and the longest legend heading. */
export const MAX_LABEL = 120;

/** A value as it is compared: a number by its value, any other value as text. */
export type Key = number | string;

/** A field as a column profile: its name, kind ("number", "date", "yes/no", "text"), filter, and listed values. */
export interface Field {
  readonly name: string;
  readonly kind?: string | null;
  readonly filter?: string | null;
  readonly values?: readonly (readonly [string, number] | readonly unknown[])[];
}

/** A named group of values, with the name of its colour. */
export interface ValueGroup {
  readonly label: string;
  readonly values: readonly string[];
  readonly colour?: string | null;
}

/** The groups and legend heading of a configuration, as `validate` and `carryOver` return them. */
export interface Grouping {
  groups?: { label: string; values: string[]; colour: string }[];
  legend_heading?: string;
}

const NUMBER = /^\s*[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?\s*$/;

/**
 * A value as it is compared: a number by its value ("2.50" and "2.5" are the same), yes or no without case, any other
 * value as written. A value of a number field that is not written as a number is compared as written.
 */
export function keyOf(kind: string | null | undefined, value: unknown): Key {
  const text = String(value);
  if (kind === "number" && NUMBER.test(text)) return Number(text);
  return kind === "yes/no" ? text.toLowerCase() : text;
}

/** A number as JavaScript writes it: "1", "2.5", "0.00001", "1e-7", "1e+21". */
export const numberText = (value: number): string => String(value);

/** A key as the text that a map style compares. */
export const keyText = (key: Key): string => (typeof key === "number" ? numberText(key) : key);

/** The keys of the values of a field, or null for a field that is not filtered by a list of its values. */
export function valuesOf(field: Field | null | undefined): Set<Key> | null {
  if (!field || field.filter !== "list" || !field.values) return null;
  return new Set(field.values.map((entry) => keyOf(field.kind, entry[0])));
}

/** A label with its runs of spaces made one and no space at either end. */
export const tidy = (text: unknown): string =>
  String(text ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .join(" ");

/**
 * The colour of each group, by name. A group keeps its own colour when it is one of `names` and no earlier group has it;
 * any other group takes the first colour that no group has, or the first colour when none is free.
 */
export function assignColours(groups: readonly { colour?: string | null }[], names: readonly string[] = DEFAULT_COLOUR_NAMES): string[] {
  const taken = new Set<string>();
  const own = groups.map((group) => {
    const colour = group.colour ?? "";
    if (names.includes(colour) && !taken.has(colour)) {
      taken.add(colour);
      return colour;
    }
    return null;
  });
  return own.map((colour) => {
    if (colour !== null) return colour;
    const free = names.find((name) => !taken.has(name)) ?? names[0] ?? "";
    taken.add(free);
    return free;
  });
}

/**
 * Groups that cannot be kept. `code` names the problem; `message` is a sentence for the person; `details` holds the
 * values it names. The codes are those of the Python package.
 */
export class GroupingError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown>;
  constructor(code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "GroupingError";
    this.code = code;
    this.details = details;
  }
}

const FORMAT = "The groups of values are not in the expected format.";
const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null && !Array.isArray(value);

/**
 * The groups and the legend heading of `config`, checked and tidied; {} when there are none. `field` is the field of the
 * symbology, or null for a single symbol. Values are compared by their keys and kept as written. A group without a
 * colour takes the first colour that no other group has. Throws GroupingError.
 */
export function validate(
  field: Field | null | undefined,
  config: Record<string, unknown>,
  colourNames: readonly string[] = DEFAULT_COLOUR_NAMES,
): Grouping {
  const groups = config["groups"];
  const heading = config["legend_heading"];
  if (
    (groups === undefined || groups === null || (Array.isArray(groups) && groups.length === 0)) &&
    (heading === undefined || heading === null || heading === "")
  ) {
    return {};
  }
  if (
    (groups !== undefined && groups !== null && !Array.isArray(groups)) ||
    (heading !== undefined && heading !== null && typeof heading !== "string")
  ) {
    throw new GroupingError("format", FORMAT);
  }
  if (!field) throw new GroupingError("needs_unique_values", "Groups of values and a legend heading require unique values symbology.");
  const found: Grouping = {};
  const tidied = tidy(heading);
  if (tidied.length > MAX_LABEL)
    throw new GroupingError("heading_too_long", `The legend heading exceeds ${MAX_LABEL} characters.`, { limit: MAX_LABEL });
  if (tidied) found.legend_heading = tidied;
  const list = (groups as unknown[] | null | undefined) ?? [];
  if (list.length === 0) return found;
  if (list.length > colourNames.length) {
    throw new GroupingError(
      "too_many_groups",
      `The groups of values are limited to ${colourNames.length}, one for each colour of the symbology.`,
      {
        limit: colourNames.length,
      },
    );
  }
  const known = valuesOf(field);
  if (known === null) throw new GroupingError("needs_value_list", "Groups of values are available for fields with a list of values.");
  const labels = new Set<string>();
  const placed = new Set<Key>();
  const colours = new Set<string>();
  const result: { label: string; values: string[]; colour: string | null }[] = [];
  for (const group of list) {
    if (!isRecord(group) || !Array.isArray(group["values"])) throw new GroupingError("format", FORMAT);
    const sent = group["values"] as unknown[];
    if (sent.some((value) => typeof value !== "string")) throw new GroupingError("format", FORMAT);
    const label = tidy(group["label"]);
    if (!label) throw new GroupingError("missing_label", "Enter the label of each group.");
    if (label.length > MAX_LABEL)
      throw new GroupingError("label_too_long", `A group label exceeds ${MAX_LABEL} characters.`, { limit: MAX_LABEL });
    if (labels.has(label.toLowerCase()))
      throw new GroupingError("duplicate_label", `The label “${label}” is used by more than one group.`, { label });
    labels.add(label.toLowerCase());
    const values: string[] = [];
    for (const value of sent as string[]) {
      const key = keyOf(field.kind, value);
      if (!known.has(key))
        throw new GroupingError("unknown_value", `The value “${value}” does not occur in the field of the symbology.`, { value });
      if (placed.has(key)) throw new GroupingError("value_in_two_groups", `The value “${value}” is in more than one group.`, { value });
      placed.add(key);
      values.push(value);
    }
    if (values.length === 0) throw new GroupingError("empty_group", `The group “${label}” contains no values.`, { label });
    const colour = typeof group["colour"] === "string" && group["colour"] ? group["colour"] : null;
    if (colour !== null && !colourNames.includes(colour)) {
      throw new GroupingError("unknown_colour", `The colour of the group “${label}” is not a colour of the symbology.`, { label });
    }
    if (colour !== null && colours.has(colour))
      throw new GroupingError("duplicate_colour", "Each group must have a colour of its own.", { colour });
    if (colour !== null) colours.add(colour);
    result.push({ label, values, colour });
  }
  const free = colourNames.filter((name) => !colours.has(name));
  found.groups = result.map((group) => ({ ...group, colour: group.colour ?? free.shift() ?? "" }));
  return found;
}

/**
 * The groups and the legend heading of `previous` for the same field in new data. The heading is kept. Each group keeps
 * the values that the field still has, and a group left without any is dropped. A value in two groups stays with the
 * first. A field without a list of its values keeps no groups.
 */
export function carryOver(previous: Record<string, unknown>, field: Field | null | undefined): Grouping {
  const found: Grouping = {};
  const heading = tidy(typeof previous["legend_heading"] === "string" ? previous["legend_heading"] : "");
  if (heading) found.legend_heading = heading.slice(0, MAX_LABEL);
  const known = valuesOf(field);
  if (!field || known === null) return found;
  const placed = new Set<Key>();
  const groups: { label: string; values: string[]; colour: string }[] = [];
  for (const group of Array.isArray(previous["groups"]) ? previous["groups"] : []) {
    if (!isRecord(group)) continue;
    const values: string[] = [];
    for (const value of Array.isArray(group["values"]) ? group["values"] : []) {
      if (typeof value !== "string") continue;
      const key = keyOf(field.kind, value);
      if (known.has(key) && !placed.has(key)) {
        placed.add(key);
        values.push(value);
      }
    }
    if (values.length > 0) groups.push({ ...(group as { label: string; colour: string }), values });
  }
  if (groups.length > 0) found.groups = groups;
  return found;
}

/**
 * The classes of a field, in the order of the legend: `labels`, `members` (the values of each class, as written) and
 * `places` (the place of the colour of each class in the palette) run in parallel.
 */
export interface Classes {
  readonly field: string | null;
  readonly kind: string | null;
  readonly grouped: boolean;
  readonly labels: readonly string[];
  readonly members: readonly (readonly string[])[];
  readonly places: readonly number[];
  /** The class of a value, or -1 for a value drawn as Other. */
  classOf(value: unknown): number;
}

/**
 * The classes of unique values symbology. Without groups, each of the most frequent values (`categories`, the most
 * frequent first) is a class of its own, in the colour of its place. With groups, each group with values is a class, in
 * the colour of its name; a value named in two groups stays with the first. Values are compared by their keys.
 */
export function classesOf(
  field: string | null,
  kind: string | null | undefined,
  categories: readonly string[],
  groups: readonly ValueGroup[] | null | undefined,
  colourNames: readonly string[] = DEFAULT_COLOUR_NAMES,
): Classes {
  const k = kind ?? null;
  if (!field) return { field: null, kind: k, grouped: false, labels: [], members: [], places: [], classOf: () => -1 };
  const place = new Map<Key, number>();
  const classOf = (value: unknown) => place.get(keyOf(k, value)) ?? -1;
  const listed = (groups ?? []).filter((group) => group.values.length > 0).slice(0, colourNames.length);
  if (listed.length === 0) {
    const used = categories.slice(0, colourNames.length);
    used.forEach((value, at) => place.set(keyOf(k, value), at));
    return {
      field,
      kind: k,
      grouped: false,
      labels: used,
      members: used.map((value) => [value]),
      places: used.map((_, at) => at),
      classOf,
    };
  }
  const members = listed.map((group, at) => {
    const own: string[] = [];
    for (const value of group.values) {
      const key = keyOf(k, value);
      if (place.has(key)) continue;
      place.set(key, at);
      own.push(value);
    }
    return own;
  });
  const names = assignColours(listed, colourNames);
  return {
    field,
    kind: k,
    grouped: true,
    labels: listed.map((group) => group.label),
    members,
    places: names.map((name) => colourNames.indexOf(name)),
    classOf,
  };
}

/** The colour of each class from a palette in the order of the colour names. */
export const coloursOf = (classes: Classes, palette: readonly string[]): string[] =>
  classes.places.map((at) => palette[at] ?? palette[0] ?? "");

export interface LegendRow {
  readonly label: string;
  readonly colour: string;
  readonly count: number;
}

/**
 * The rows of the legend. Without groups, the values that have a colour, in the order of `counted` (each value with its
 * number of records); with groups, every group in its order with the records of its values.
 */
export function legendOf(classes: Classes, counted: readonly (readonly [string, number])[], palette: readonly string[]): LegendRow[] {
  const colours = coloursOf(classes, palette);
  if (!classes.grouped) {
    return counted.flatMap(([value, count]) => {
      const at = classes.classOf(value);
      return at < 0 ? [] : [{ label: value, colour: colours[at] ?? "", count }];
    });
  }
  const totals = classes.labels.map(() => 0);
  for (const [value, count] of counted) {
    const at = classes.classOf(value);
    if (at >= 0) totals[at] = (totals[at] ?? 0) + count;
  }
  return classes.labels.map((label, at) => ({ label, colour: colours[at] ?? "", count: totals[at] ?? 0 }));
}

/**
 * The colour of the records as a MapLibre GL / Mapbox GL style expression: a "match" of the value of the field, with
 * `other` for every value in no class. Values are matched by their keys: a number by the text JavaScript gives it, yes or
 * no in lower case. Without a field the records take `plain`.
 */
export function matchExpression(classes: Classes, palette: readonly string[], other: unknown, plain: unknown): unknown {
  if (!classes.field) return plain;
  const value = classes.kind === "yes/no" ? ["downcase", ["to-string", ["get", classes.field]]] : ["to-string", ["get", classes.field]];
  const colours = coloursOf(classes, palette);
  const branches = classes.members.flatMap((members, at) => {
    const labels = [...new Set(members.map((member) => keyText(keyOf(classes.kind, member))))];
    return labels.length === 0 ? [] : [labels.length === 1 ? labels[0] : labels, colours[at]];
  });
  if (branches.length === 0) return classes.grouped ? other : plain;
  return ["match", value, ...branches, other];
}
