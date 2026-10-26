function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Find where `span` occurs in `text`, case-insensitively and tolerant of
 * whitespace differences (each whitespace run in the span matches \s+).
 * Returns [start, end) in the original text, or null.
 */
export function findSpan(text: string, span: string | null | undefined): [number, number] | null {
  if (!text || !span) return null
  const pattern = span
    .trim()
    .split(/\s+/)
    .map(escapeRegex)
    .join('\\s+')
  const m = new RegExp(pattern, 'i').exec(text)
  if (!m) return null
  return [m.index, m.index + m[0].length]
}

/**
 * Render `text` as escaped HTML with `spans` wrapped in <mark class="cls">.
 * Spans are applied non-overlapping, in document order. Model output is
 * never injected raw: only source text is emitted, escaped.
 */
export function markSpans(text: string, spans: (string | null | undefined)[], cls: string): string {
  if (!text) return ''
  const hits: [number, number][] = []
  for (const span of spans) {
    const hit = findSpan(text, span)
    if (hit) hits.push(hit)
  }
  hits.sort((a, b) => a[0] - b[0])
  const clean: [number, number][] = []
  let last = -1
  for (const h of hits) {
    if (h[0] >= last) {
      clean.push(h)
      last = h[1]
    }
  }
  let out = ''
  let pos = 0
  for (const [s, e] of clean) {
    out += escapeHtml(text.slice(pos, s))
    out += `<mark class="${cls}">${escapeHtml(text.slice(s, e))}</mark>`
    pos = e
  }
  out += escapeHtml(text.slice(pos))
  return out
}
