export function buildSourceIndex(groundingReport) {
  const sources = Array.isArray(groundingReport?.sources)
    ? groundingReport.sources
    : [];

  return new Map(
    sources.map((source, index) => [source.sourceId, { ...source, number: index + 1 }]),
  );
}

export function getClaimsForSection(groundingReport, section, itemIndex = null) {
  const claims = Array.isArray(groundingReport?.claims)
    ? groundingReport.claims
    : [];

  return claims.filter((claim) => {
    if (claim.section !== section) return false;
    if (itemIndex == null) return claim.itemIndex == null;
    return claim.itemIndex === itemIndex;
  });
}

export function getCitationSources(groundingReport, section, itemIndex = null) {
  const sourceIndex = buildSourceIndex(groundingReport);
  const claims = getClaimsForSection(groundingReport, section, itemIndex);
  const sourceIds = [...new Set(claims.flatMap((claim) => claim.sourceIds || []))];
  return sourceIds.map((sourceId) => sourceIndex.get(sourceId)).filter(Boolean);
}

export function getSectionVerificationState(groundingReport, section, itemIndex = null) {
  const claims = getClaimsForSection(groundingReport, section, itemIndex);
  if (claims.some((claim) => claim.status === "contradicted")) return "contradicted";
  if (claims.some((claim) => claim.status === "unverified")) return "unverified";
  if (claims.some((claim) => claim.status === "supported")) return "supported";
  return "not_applicable";
}
