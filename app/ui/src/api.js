/* Same-origin client for the Strategy Option Evaluation API.
 *
 * One FastAPI process serves this page at `/` and the API at `/api`, so every
 * request here is a same-origin absolute path. There is no base-URL setting and
 * no CORS.
 *
 * Rules this file exists to enforce:
 *   - it is the only place the UI talks to the network;
 *   - a failure is raised as an ApiError carrying the backend's own
 *     {"error": {code, message, detail}} envelope, so a screen can print the
 *     code and the message the backend wrote;
 *   - nothing is retried. A retry that eventually succeeds hides a backend that
 *     is failing half the time, and a retry that fails just delays the error.
 *   - nothing is defaulted, smoothed or filled in. A field the API does not
 *     send arrives here as undefined and the screen must say so.
 */

const BASE = "/api";

export class ApiError extends Error {
  constructor(status, code, message, detail, path) {
    super(message);
    this.name = "ApiError";
    this.status = status;   // HTTP status, or 0 when the request never completed
    this.code = code;       // the backend's error code, or a transport code
    this.detail = detail;   // whatever the backend put in error.detail
    this.path = path;       // the /api path that failed
  }
  /** One line, safe to render: "unknown_id (404) — no strategy str_x at batch 0". */
  get line() {
    return `${this.code} (${this.status || "no response"}) — ${this.message}`;
  }
}

function query(params) {
  const q = new URLSearchParams();
  Object.keys(params || {}).forEach((k) => {
    const v = params[k];
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  });
  const s = q.toString();
  return s ? "?" + s : "";
}

async function getJSON(path) {
  let res;
  try {
    res = await fetch(BASE + path, { headers: { accept: "application/json" } });
  } catch (e) {
    // DNS, connection refused, offline, aborted: the request never completed.
    throw new ApiError(0, "unreachable", `the API did not answer: ${e && e.message ? e.message : e}`, null, path);
  }
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch (_) { body = null; }
  if (!res.ok) {
    const err = body && body.error;
    throw new ApiError(
      res.status,
      (err && err.code) || "http_error",
      (err && err.message) || (text ? text.slice(0, 300) : `HTTP ${res.status}`),
      (err && err.detail) || null,
      path,
    );
  }
  if (body === null) {
    throw new ApiError(res.status, "unreadable_response", "the API answered with something that is not JSON", null, path);
  }
  return body;
}

/** The five weight keys the comparison screen and every ranking endpoint use. */
export const WEIGHT_KEYS = ["mission", "personnel", "escalation", "time", "resources"];

function weightParams(weights) {
  const out = {};
  WEIGHT_KEYS.forEach((k) => { if (weights && weights[k] !== undefined) out[k] = weights[k]; });
  return out;
}

export function meta() {
  return getJSON("/meta");
}

export function options(weights, scope) {
  return getJSON("/options" + query({ ...(scope || {}), ...weightParams(weights) }));
}

export function rank(weights, scope) {
  return getJSON("/options/rank" + query({ ...(scope || {}), ...weightParams(weights) }));
}

/** The comparison screen's two halves, fetched together: the options and their ranking
 *  under one weighting. Both carry the same `caution`, `weights` and `level_thresholds`. */
export async function loadOptions(weights, scope) {
  const [opts, ranking] = await Promise.all([options(weights, scope), rank(weights, scope)]);
  return { options: opts, rank: ranking };
}

/** Ten-bin enumerated outcome distribution. Omit `strategy` for every option. */
export function outcomeDistribution(strategy, scope) {
  return getJSON("/options/outcome-distribution" + query({ ...(scope || {}), strategy }));
}

/** The comparison recomputed with one assumption failing. */
export function whatIf(assumptionId, scope) {
  return getJSON("/options/what-if" + query({ ...(scope || {}), assumption: assumptionId }));
}

export function risks(scope) {
  return getJSON("/risks" + query(scope || {}));
}

export function collection(scope) {
  return getJSON("/collection" + query(scope || {}));
}

export function claims(params) {
  return getJSON("/claims" + query(params || {}));
}
