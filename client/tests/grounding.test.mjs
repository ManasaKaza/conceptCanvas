import test from "node:test";
import assert from "node:assert/strict";
import {
  buildSourceIndex,
  getCitationSources,
  getClaimsForSection,
  getSectionVerificationState,
} from "../src/utils/grounding.js";

const report = {
  sources: [
    { sourceId: "source_one", title: "Source One", url: "https://example.org/one" },
    { sourceId: "source_two", title: "Source Two", url: "https://example.org/two" },
  ],
  claims: [
    {
      claimId: "claim_1",
      section: "stepByStep",
      itemIndex: 0,
      status: "supported",
      sourceIds: ["source_one"],
    },
    {
      claimId: "claim_2",
      section: "stepByStep",
      itemIndex: 1,
      status: "unverified",
      sourceIds: [],
    },
    {
      claimId: "claim_3",
      section: "summary",
      itemIndex: null,
      status: "contradicted",
      sourceIds: ["source_two"],
    },
  ],
};

test("numbers sources in stable report order", () => {
  const index = buildSourceIndex(report);
  assert.equal(index.get("source_one").number, 1);
  assert.equal(index.get("source_two").number, 2);
});

test("finds claims by explanation section and item index", () => {
  const claims = getClaimsForSection(report, "stepByStep", 1);
  assert.equal(claims.length, 1);
  assert.equal(claims[0].claimId, "claim_2");
});

test("returns source records for claim-level citations", () => {
  const sources = getCitationSources(report, "stepByStep", 0);
  assert.deepEqual(sources.map((source) => source.number), [1]);
});

test("surfaces unverified and contradicted states", () => {
  assert.equal(getSectionVerificationState(report, "stepByStep", 1), "unverified");
  assert.equal(getSectionVerificationState(report, "summary"), "contradicted");
});
