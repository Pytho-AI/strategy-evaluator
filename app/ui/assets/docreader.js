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

export async function readDocx(buf) {
  const xml = await unzipEntry(buf, 'word/document.xml');
  const paras = [];
  xml.replace(/<w:p[ >][\s\S]*?<\/w:p>/g, m => { const t = (m.match(/<w:t[^>]*>([^<]*)<\/w:t>/g) || []).map(x => x.replace(/<[^>]+>/g, '')).join(''); if (t.trim()) paras.push(t.trim()); return ''; });
  return paras.join('\n');
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
export function extractPlan(text) {
  const grab = re => { const m = text.match(re); return m ? m[1].trim().slice(0, 400) : ''; };
  return {
    mission: grab(/(?:^|\n)\s*(?:2\.\s*)?Mission[.:\s]+([\s\S]{20,600}?)(?:\n\s*\n|\n\s*(?:3\.|Execution))/i),
    intent: grab(/Commander'?s Intent[.:\s]+([\s\S]{20,600}?)(?:\n\s*\n)/i),
    endState: grab(/End State[.:\s]+([\s\S]{10,400}?)(?:\n\s*\n|\n)/i),
    assumptions: (text.match(/(?:^|\n)\s*(?:\(?[a-z0-9]\)?[.)]\s*)?(?:Assumption|It is assumed)[^\n]{10,240}/gi) || []).slice(0, 6).map(s => s.trim()),
    phases: (text.match(/Phase\s+(?:[0IVX]+|\d)[^\n]{0,80}/g) || []).slice(0, 6),
  };
}

// Keyword-based signal scoring used by the risk comparison. Returns 0–1 indices.
export function signalIndex(text) {
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
