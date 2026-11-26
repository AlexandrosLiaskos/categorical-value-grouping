// The shared test cases of spec/vectors.json, which the Python package runs as well.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  GroupingError,
  assignColours,
  carryOver,
  classesOf,
  coloursOf,
  keyOf,
  legendOf,
  matchExpression,
  numberText,
  validate,
} from "../src/index.js";

const VECTORS = JSON.parse(readFileSync(new URL("../../spec/vectors.json", import.meta.url), "utf-8"));
const NAMES: string[] = VECTORS.colour_names;
const made = (c: any) => classesOf(c.field, c.kind, c.categories, c.groups, NAMES);

describe("keys", () => {
  for (const c of VECTORS.keys) it(`${c.kind}: ${c.value}`, () => expect(keyOf(c.kind, c.value)).toEqual(c.key));
});

describe("number texts", () => {
  for (const c of VECTORS.number_texts) it(c.text, () => expect(numberText(c.number)).toBe(c.text));
});

describe("colours", () => {
  for (const c of VECTORS.colours) it(c.about, () => expect(assignColours(c.groups, NAMES)).toEqual(c.expected));
});

describe("validate", () => {
  for (const c of VECTORS.validate_ok) it(c.about, () => expect(validate(c.field, c.config, NAMES)).toEqual(c.expected));
  for (const c of VECTORS.validate_errors) {
    it(`refuses: ${c.code}`, () => {
      let caught: unknown;
      try {
        validate(c.field, c.config, NAMES);
      } catch (error) {
        caught = error;
      }
      expect(caught).toBeInstanceOf(GroupingError);
      expect([(caught as GroupingError).code, (caught as GroupingError).message]).toEqual([c.code, c.message]);
    });
  }
});

describe("carry over", () => {
  for (const c of VECTORS.carry_over) it(c.about, () => expect(carryOver(c.previous, c.field)).toEqual(c.expected));
});

describe("classes", () => {
  for (const c of VECTORS.classes) {
    it(c.about, () => {
      const classes = made(c);
      expect(classes.grouped).toBe(c.grouped);
      expect(classes.labels).toEqual(c.labels);
      expect(classes.members).toEqual(c.members);
      expect(coloursOf(classes, NAMES)).toEqual(c.colours);
      expect(Object.fromEntries(Object.keys(c.class_of).map((value) => [value, classes.classOf(value)]))).toEqual(c.class_of);
    });
  }
});

describe("legend", () => {
  for (const c of VECTORS.legend) it(c.about, () => expect(legendOf(made(VECTORS.classes[c.classes]), c.counted, NAMES)).toEqual(c.rows));
});

describe("match", () => {
  for (const c of VECTORS.match)
    it(c.about, () => expect(matchExpression(made(VECTORS.classes[c.classes]), NAMES, "OTHER", "PLAIN")).toEqual(c.expression));
});
