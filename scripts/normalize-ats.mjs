/**
 * ATS text normalization — ensures PDF text is parseable by ATS systems.
 * Replaces typographic characters with ASCII equivalents.
 */
export function normalizeTextForATS(html) {
  // Preserve style and script blocks
  const preserved = [];
  let normalized = html.replace(/<(style|script)[^>]*>[\s\S]*?<\/\1>/gi, (match) => {
    preserved.push(match);
    return `__PRESERVED_${preserved.length - 1}__`;
  });

  // Normalize only text content (outside HTML tags)
  normalized = normalized.replace(/>([^<]+)</g, (match, text) => {
    let clean = text
      .replace(/[\u2014\u2015]/g, '-')        // em dash -> hyphen
      .replace(/[\u2013\u2012]/g, '-')         // en dash -> hyphen
      .replace(/[\u2018\u2019\u201B]/g, "'")   // smart single quotes
      .replace(/[\u201C\u201D\u201F]/g, '"')   // smart double quotes
      .replace(/\u2026/g, '...')               // ellipsis
      .replace(/[\u200B\u200C\u200D\uFEFF]/g, '') // zero-width chars
      .replace(/\u00A0/g, ' ');                // NBSP -> space
    return `>${clean}<`;
  });

  // Restore preserved blocks
  preserved.forEach((block, i) => {
    normalized = normalized.replace(`__PRESERVED_${i}__`, block);
  });

  return normalized;
}
