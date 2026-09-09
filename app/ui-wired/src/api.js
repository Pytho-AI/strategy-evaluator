/* Fetch client for the Strategy Option Evaluation API.
 *
 * Plain script, not a module: `app.logic.js` is compiled by dc-runtime as a
 * `text/x-dc` script and cannot `import`. It reads `window.API`.
 *
 * Base URL: `window.API_BASE` if set, otherwise the same-origin `/api`. The UI
 * hard-codes no origin.
 *
 * Rules this client keeps:
 *  - one request per call, no retries. A failure is surfaced, never smoothed
 *    over and never replaced with a cached or fabricated body;
 *  - the backend's `{"error": {code, message, detail}}` envelope is unwrapped
 *    into an `ApiError` carrying that code, so the UI can name what went wrong;
 *  - endpoints the running backend does not declare raise `not_served`
 *    *without* issuing a request, so a missing capability never shows up as a
 *    failed request in the browser. Availability — and, for the P3 write API,
 *    the concrete path shape — is read once from the OpenAPI document the API
 *    already publishes, so the UI follows the backend rather than guessing a
 *    URL and 404ing;
 *  - the demo workspace id rides on every request as `workspace=` once the
 *    backend declares that parameter, and never before.
 */
(function () {
  'use strict';

  // Read routes that arrived after P0. Named so a backend without them renders
  // an "unavailable" panel instead of an error.
  var OPTIONAL = {
    strategies: '/api/strategies',
    diff: '/api/injects/{batch}/diff',
    risks: '/api/risks',
    collection: '/api/collection',
  };

  // The P3 write API. Matched by shape rather than by a literal path: the
  // backend owns the exact spelling (`/api/collection/drafts/{id}/route` and
  // `/api/collection/{id}/route` are both accepted), and the UI reads it out of
  // /openapi.json.
  var WRITE = {
    ingestReport: { method: 'post', match: /^\/api\/reports\/?$/ },
    claimDecision: { method: 'post', match: /^\/api\/claims\/proposed\/\{[^{}]+\}\/decision$/ },
    draftRequirement: { method: 'post', match: /^\/api\/collection\/drafts\/?$/ },
    routeRequirement: { method: 'post', match: /^\/api\/collection\/.*\/route$/ },
    statusRequirement: { method: 'post', match: /^\/api\/collection\/.*\/status$/ },
    resetWorkspace: { method: 'post', match: /^\/api\/workspace\/reset$/ },
    planning: { method: 'get', match: /^\/api\/planning\/?$/ },
    reviewPlanning: { method: 'post', match: /^\/api\/planning\/\{[^{}]+\}\/review$/ },
    report: { method: 'get', match: /^\/api\/reports\/\{[^{}]+\}$/ },
  };

  function base() {
    return String(window.API_BASE || '/api').replace(/\/+$/, '');
  }

  function schemaUrl() {
    // /api -> /openapi.json on the same origin as the API itself.
    return base().replace(/\/api$/, '') + '/openapi.json';
  }

  function ApiError(code, message, status, detail) {
    var e = new Error(message);
    e.name = 'ApiError';
    e.code = code;
    e.status = status || 0;
    e.detail = detail || {};
    return e;
  }

  var inflight = 0;

  async function request(url, options) {
    var res;
    inflight += 1;
    try {
      res = await fetch(url, options);
    } catch (e) {
      throw ApiError('network_error', url + ': ' + e.message + ' (is the API running?)', 0);
    } finally {
      inflight -= 1;
    }
    var body = null;
    try {
      body = await res.json();
    } catch (e) {
      body = null;
    }
    if (!res.ok) {
      var env = body && body.error;
      if (env) throw ApiError(env.code, env.message, res.status, env.detail);
      throw ApiError('http_error', url + ': HTTP ' + res.status, res.status);
    }
    if (body === null) throw ApiError('bad_response', url + ': response was not JSON', res.status);
    return body;
  }

  function getJson(url) {
    return request(url, { headers: { accept: 'application/json' } });
  }

  // ── the published schema ────────────────────────────────────────────────
  // Read once. `paths` maps path template -> the set of methods declared on it;
  // `params` maps path template -> the query parameter names it declares.
  var schema = null;

  function schemaDoc() {
    if (!schema) {
      schema = getJson(schemaUrl()).then(
        function (doc) {
          var paths = {}, params = {};
          Object.keys((doc && doc.paths) || {}).forEach(function (p) {
            var ops = doc.paths[p] || {};
            paths[p] = Object.keys(ops).map(function (m) { return m.toLowerCase(); });
            params[p] = [].concat.apply([], Object.keys(ops).map(function (m) {
              return ((ops[m] || {}).parameters || []).map(function (q) { return q.name; });
            }));
          });
          return { paths: paths, params: params };
        },
        function () { return { paths: {}, params: {} }; }
      );
    }
    return schema;
  }

  async function requireRoute(key) {
    var path = OPTIONAL[key];
    var doc = await schemaDoc();
    if (!doc.paths[path]) {
      throw ApiError('not_served', path + ' is not served by this backend yet', 0, { path: path });
    }
  }

  /* The concrete path template for a write capability, or null. */
  async function writePath(key) {
    var spec = WRITE[key];
    var doc = await schemaDoc();
    var found = Object.keys(doc.paths).filter(function (p) {
      return spec.match.test(p) && doc.paths[p].indexOf(spec.method) !== -1;
    });
    return found.length ? found.sort()[0] : null;
  }

  /* Which write capabilities this backend declares. Rendered as state, so a
   * screen can say exactly which endpoint it is waiting for. */
  async function writeSupport() {
    var out = {};
    var keys = Object.keys(WRITE);
    var paths = await Promise.all(keys.map(writePath));
    keys.forEach(function (k, i) { out[k] = paths[i]; });
    return out;
  }

  async function fillPath(key, args) {
    var template = await writePath(key);
    if (!template) {
      throw ApiError(
        'not_served',
        'the ' + key + ' endpoint is not served by this backend yet',
        0,
        { capability: key }
      );
    }
    var rest = (args || []).slice();
    return template.replace(/\{[^{}]+\}/g, function () {
      return encodeURIComponent(String(rest.shift()));
    });
  }

  // ── the demo workspace ──────────────────────────────────────────────────
  // Product-owned state lives beside the frozen dataset in a named workspace.
  // The id is sent only once the backend declares the parameter.
  var workspaceId = window.WORKSPACE_ID || 'demo';

  /* The key a path has in the published document: the API base's own path
   * prefix plus the route. `/snapshot` -> `/api/snapshot`. */
  function schemaKey(path) {
    var b = base();
    var m = b.match(/^[a-z]+:\/\/[^/]*(\/.*)$/i);
    return (m ? m[1] : (b.charAt(0) === '/' ? b : '/api')) + path;
  }

  async function workspaceQuery(template) {
    var doc = await schemaDoc();
    var declared = doc.params[schemaKey(template)] || [];
    return workspaceId && declared.indexOf('workspace') !== -1
      ? { workspace: workspaceId }
      : {};
  }

  function query(params) {
    var parts = [];
    Object.keys(params || {}).forEach(function (k) {
      var v = params[k];
      if (v === null || v === undefined || v === '') return;
      parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
    });
    return parts.length ? '?' + parts.join('&') : '';
  }

  async function get(path, params, template) {
    var all = Object.assign({}, params || {}, await workspaceQuery(template || path));
    return getJson(base() + path + query(all));
  }

  /* POST a typed body. `batch` and `workspace` ride in the query string, and
   * only when the endpoint declares them — the body carries the contract's own
   * fields and nothing else. */
  async function post(key, args, body, batch) {
    var template = await writePath(key);
    var path = await fillPath(key, args);
    var doc = await schemaDoc();
    var declared = doc.params[template] || [];
    var params = {};
    if (declared.indexOf('batch') !== -1 && batch != null) params.batch = batch;
    if (declared.indexOf('workspace') !== -1 && workspaceId) params.workspace = workspaceId;
    var origin = base().replace(/\/api$/, '');
    return request(origin + path + query(params), {
      method: 'POST',
      headers: { accept: 'application/json', 'content-type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
  }

  window.API = {
    ApiErrorName: 'ApiError',
    base: base,
    inflight: function () { return inflight; },
    workspace: function () { return workspaceId; },
    setWorkspace: function (id) { workspaceId = id; },
    writeSupport: writeSupport,

    getMeta: function () { return get('/meta'); },
    getInjects: function () { return get('/injects'); },
    getSnapshot: function (batch) { return get('/snapshot', { batch: batch }); },
    getStrategy: function (id, batch) {
      return get('/strategies/' + encodeURIComponent(id), { batch: batch },
        '/strategies/{strategy_id}');
    },
    /* Evidence. `filters` takes the endpoint's own parameter names:
     * entity, source, status, min_confidence, relationship, assumption,
     * harmful_event, limit, offset. */
    getClaims: function (batch, filters) {
      return get('/claims', Object.assign({ batch: batch }, filters || {}));
    },
    getClaim: function (id, batch) {
      return get('/claims/' + encodeURIComponent(id), { batch: batch }, '/claims/{claim_id}');
    },
    /* Every Blue option with weights, contributions, resources, theory of
     * victory, constraints/restraints and harmful events. Raises `not_served`
     * until the backend declares GET /api/strategies. */
    getStrategies: async function (batch) {
      await requireRoute('strategies');
      return get('/strategies', { batch: batch });
    },
    /* Problem sets, harmful events per horizon, drivers and cascade edges. */
    getRisks: async function (batch) {
      await requireRoute('risks');
      return get('/risks', { batch: batch });
    },
    /* Ranked collection requirements with PIR context and priority basis. */
    getCollection: async function (batch) {
      await requireRoute('collection');
      return get('/collection', { batch: batch });
    },
    /* What one inject batch changed. Raises `not_served` until the backend
     * declares GET /api/injects/{batch}/diff. */
    getDiff: async function (batch) {
      await requireRoute('diff');
      return get('/injects/' + encodeURIComponent(batch) + '/diff', {},
        '/injects/{batch}/diff');
    },
    /* Tracked planning objects: assumptions, constraints and restraints with
     * their source links, validity, review state and the flags accepted
     * evidence raised. */
    getPlanning: async function (batch) {
      var path = await writePath('planning');
      if (!path) {
        throw ApiError('not_served', 'GET /api/planning is not served by this backend yet',
          0, { capability: 'planning' });
      }
      var origin = base().replace(/\/api$/, '');
      return getJson(origin + path + query({ batch: batch, workspace: workspaceId }));
    },
    /* The stored report: its original text and its proposed claims. */
    getReport: async function (id, batch) {
      var template = await writePath('report');
      if (!template) {
        throw ApiError('not_served', 'GET /api/reports/{id} is not served yet', 0, {});
      }
      var origin = base().replace(/\/api$/, '');
      return getJson(origin + template.replace(/\{[^{}]+\}/, encodeURIComponent(id))
        + query({ batch: batch, workspace: workspaceId }));
    },

    // ── writes (P3) ───────────────────────────────────────────────────────
    /* Store a report and extract proposed claims. `report` is the endpoint's
     * own body: {filename, actor, text} for text/markdown/CSV/JSON, or
     * {filename, actor, content_base64, content_type} for a PDF. */
    ingestReport: function (report, batch) {
      return post('ingestReport', [], report, batch);
    },
    /* Accept or reject one proposed claim: {decision, actor, reason, revision}.
     * A missing field comes back as 422 with error.detail.missing; the caller
     * asks the reviewer for exactly those and resends them in `revision`. */
    decideClaim: function (claimId, decision, batch) {
      return post('claimDecision', [claimId], decision, batch);
    },
    /* Draft a collection requirement from a strategy question or PIR. */
    draftRequirement: function (draft, batch) {
      return post('draftRequirement', [], draft, batch);
    },
    /* Internal queue assignment. Product-owned requirements only. */
    routeRequirement: function (reqId, body, batch) {
      return post('routeRequirement', [reqId], body, batch);
    },
    setRequirementStatus: function (reqId, body, batch) {
      return post('statusRequirement', [reqId], body, batch);
    },
    reviewPlanningObject: function (objectId, body, batch) {
      return post('reviewPlanning', [objectId], body, batch);
    },
    /* Discard the demo workspace. Never touches the frozen dataset. */
    resetWorkspace: function (body) { return post('resetWorkspace', [], body); },
  };
})();
