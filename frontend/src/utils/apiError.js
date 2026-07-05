export function formatApiError(detail, fallback) {
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || d.message || JSON.stringify(d)).join(". ");
  }
  return detail || fallback;
}
