import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("health route file exists", () => {
  const content = readFileSync("src/app/api/health/route.ts", "utf8");
  assert.match(content, /export async function GET/);
});