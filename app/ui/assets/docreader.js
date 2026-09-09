// Client-side document readers for the wargaming prototype. No network, no build step.
// readDocument(file) -> Promise<{ name, kind, text, words, pages }>
// .docx: unzip (DecompressionStream) and pull <w:t> runs from word/document.xml
// .txt/.md/.json: plain read.  .pdf: pdf-parse from CDN (falls back to metadata only offline).

async function unzipEntry(buf, wanted) {
  const dv = new DataView(buf); const u8 = new Uint8Array(buf);
  // Locate End Of Central Directory
  let eocd = -1;
  for (let i = u8.length - 22; i >= Math.max(0, u8.length - 70000); i--) { if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; } }
  if (eocd < 0) throw new Error('Not a zip/docx');
  const count = dv.getUint16(eocd + 10, true); let p = dv.getUint32(eocd + 16, true);
  const dec = new TextDecoder();
  for (let n = 0; n < count; n++) {
    const nameLen = dv.getUint16(p + 28, true), extraLen = dv.getUint16(p + 30, true), cmtLen = dv.getUint16(p + 32, true);
    const name = dec.decode(u8.subarray(p + 46, p + 46 + nameLen));
    const method = dv.getUint16(p + 10, true), csize = dv.getUint32(p + 20, true), lho = dv.getUint32(p + 42, true);
    if (name === wanted) {
      const lnl = dv.getUint16(lho + 26, true), lel = dv.getUint16(lho + 28, true);
      const start = lho + 30 + lnl + lel; const data = u8.subarray(start, start + csize);
      if (method === 0) return dec.decode(data);
      const ds = new DecompressionStream('deflate-raw');
      const out = await new Response(new Blob([data]).stream().pipeThrough(ds)).arrayBuffer();
      return dec.decode(out);
    }
    p += 46 + nameLen + extraLen + cmtLen;
  }
  throw new Error(wanted + ' not found');
}

// Word writes apostrophes and ampersands as XML entities. The run text is pulled out
// with a regex rather than a parser, so entities have to be decoded here or the text
// literally contains "Commander&apos;s Intent" and no heading pattern can match it.
function unescapeXml(s) {
  return (s || '')
    .replace(/&apos;/g, "'").replace(/&#0*39;/g, "'").replace(/&#x0*27;/gi, "'")
    .replace(/&quot;/g, '"').replace(/&#0*34;/g, '"').replace(/&#x0*22;/gi, '"')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&amp;/g, '&');
}

export async function readDocx(buf) {
  const xml = await unzipEntry(buf, 'word/document.xml');
  const paras = [];
  xml.replace(/<w:p[ >][\s\S]*?<\/w:p>/g, m => { const t = unescapeXml((m.match(/<w:t[^>]*>([^<]*)<\/w:t>/g) || []).map(x => x.replace(/<[^>]+>/g, '')).join('')); paras.push(t.trim()); return ''; });
  // Empty paragraphs are kept as blank lines: they are the section breaks a plan relies on.
  return paras.join('\n').replace(/\n{3,}/g, '\n\n');
}

export async function readDocument(file) {
  const name = file.name, ext = name.split('.').pop().toLowerCase();
  let text = '';
  if (ext === 'docx') text = await readDocx(await file.arrayBuffer());
  else if (ext === 'pdf') {
    try {
      const { PDFParse } = await import('https://cdn.jsdelivr.net/npm/pdf-parse@2.4.5/dist/pdf-parse/web/pdf-parse.es.js');
      PDFParse.setWorker('https://cdn.jsdelivr.net/npm/pdf-parse@2.4.5/dist/pdf-parse/web/pdf.worker.min.mjs');
      text = (await new PDFParse({ data: new Uint8Array(await file.arrayBuffer()) }).getText()).text;
    } catch (e) { text = ''; }
  } else text = await file.text();
  const words = text.split(/\s+/).filter(Boolean).length;
  return { name, kind: ext.toUpperCase(), text, words, pages: Math.max(1, Math.round(words / 450)) };
}

// Lightweight structure extraction from plan text (JP 5-0 paragraph headings).
const normalize = s => (s || '')
  .replace(/[\u2018\u2019\u02BC\u2032]/g, "'")
  .replace(/[\u201C\u201D\u2033]/g, '"')
  .replace(/[\u2013\u2014]/g, '-')
  .replace(/\u00A0/g, ' ')
  .replace(/\r\n?/g, '\n');

// A section ends at a blank line, the next numbered or lettered heading, or one of the
// headings a plan actually uses. A .docx often supplies none of these except the headings.
// A section ends at a blank line, the next heading in the CJCS scheme (1. / a. / (1) /
// (a), each optionally carrying a "(U)" marking), or a named plan heading.
const SECTION_END = "(?:\\n\\s*\\n|\\n\\s*(?:\\d{1,2}\\s*[.)]|[a-z]\\s*[.)]\\s|\\([a-z0-9]{1,3}\\)|Key Tasks|End ?State|Purpose|Method|Concept|Execution|Assumptions?|Tasks|Scheme|Commander|Annex|Appendix|PIR|Phase)|$)";

export function extractPlan(rawText) {
  const text = normalize(rawText);
  const grab = re => { const m = text.match(re); return m ? m[1].replace(/\s+/g, ' ').trim().slice(0, 700) : ''; };
  const block = (start, len) => { const i = text.search(start); if (i < 0) return ''; return text.slice(i, i + len); };
  // Assumptions: explicit lines, or the numbered list under an "Assumptions" heading
  let assumptions = (text.match(/(?:^|\n)\s*(?:\(?[a-z0-9]\)?[.)]\s*)?(?:Assumption|It is assumed)[^\n]{10,240}/gi) || []).map(s => s.trim());
  if (!assumptions.length) { let b = block(/Assumptions?[.:]?\s*\n/i, 4000); const cutAt = b.slice(20).search(/\n\s*(?:\d\.\s*(?:\(U\)\s*)?(?:MISSION|EXECUTION|SUSTAINMENT)\s*[.:]|[a-z]\.\s*\(U\)|Commander'?s Intent|Key Tasks)/i); if (cutAt >= 0) b = b.slice(0, cutAt + 20); assumptions = (b.match(/\n\s*\d{1,2}[.)]\s*[^\n]{20,400}/g) || []).map(s => s.replace(/^\s*\d{1,2}[.)]\s*/, '').trim()); }
  // PIRs: explicit PIR lines, else questions derived from enemy most likely / most dangerous COAs
  // Anchored to the start of a line and word-bounded: an unanchored /PIR/i also matches
  // inside ordinary words ("aspirational", "expiration") and swallows the rest of the sentence.
  let pirs = [...text.matchAll(/(?:^|\n)[ \t]*(?:\(U\)[ \t]*)?(?:PIRs?|Priority Intelligence Requirements?)\b[ \t]*#?[ \t]*\d{0,2}[.):\-\s]*([^\n]{10,240})/gi)]
    .map(m => m[1].trim())
    .filter(q => /[a-z]/.test(q));
  if (!pirs.length) {
    // The plan states no PIRs. Derive requirements from the enemy courses of action it does
    // state, and phrase them so they read as questions without rewriting the document's verbs.
    const coa = label => {
      const m = text.match(new RegExp("Most " + label + " (?:COA|Course of Action)[^:]*:\\s*([\\s\\S]{20,600}?)(?:\\n|$)", "i"));
      if (!m) return [];
      const clause = m[1].replace(/\s+/g, ' ').split(/(?<=[.;])\s+/)[0].replace(/[.;]\s*$/, '').trim();
      if (clause.length < 15) return [];
      return [`Will the most ${label.toLowerCase()} course of action occur: ${clause.slice(0, 220)}?`];
    };
    pirs = [...coa('Dangerous'), ...coa('Likely')].slice(0, 4);
  }
  return {
    mission: grab(new RegExp("(?:^|\\n)\\s*(?:\\d{1,2}\\s*[.)]\\s*)?(?:\\(U\\)\\s*)?Mission\\s*[.:]\\s+([\\s\\S]{20,1400}?)" + SECTION_END, "i")),
    intent: grab(new RegExp("Commander'?s?\\s*Intent\\s*[.:]?\\s*(?:\\(1\\)\\s*)?(?:\\(U\\)\\s*)?(?:Purpose\\s*[.:]\\s*)?([\\s\\S]{20,1400}?)" + SECTION_END, "i")),
    endState: grab(new RegExp("(?:Military\\s+|Desired\\s+)?End ?State\\s*[.:]\\s+([\\s\\S]{10,1400}?)" + SECTION_END, "i")),
    assumptions: assumptions.slice(0, 8), pirs,
    phases: (text.match(/Phase\s+(?:[0IVX]+|\d)[^\n]{0,80}/g) || []).slice(0, 6),
  };
}

// Keyword-based signal scoring used by the risk comparison. Returns 0–1 indices.
export function signalIndex(rawText) {
  const text = normalize(rawText);
  const t = text.toLowerCase(); const n = Math.max(1, t.split(/\s+/).length / 1000);
  const c = re => ((t.match(re) || []).length) / n;
  return {
    offensive: c(/\b(strike|seize|destroy|offensive|attack|neutralize|preempt)\b/g),
    defensive: c(/\b(defend|deter|deny|protect|hold|screen|presence)\b/g),
    escalation: c(/\b(homeland|strategic|nuclear|mainland|regime|decapitat|unrestricted)\b/g),
    restraint: c(/\b(proportional|de-escalat|off-ramp|restraint|limited|calibrated|signal)\b/g),
    force: c(/\b(casualt|attrition|loss|exposed|contested logistics|forward)\b/g),
    partners: c(/\b(ally|allies|allied|partner|coalition|combined|host nation)\b/g),
    sustain: c(/\b(sustain|logistic|munition|magazine|resupply|tpfdd|deployment)\b/g),
    intel: c(/\b(pir|indicator|collection|isr|intelligence|ipoe)\b/g),
  };
}
