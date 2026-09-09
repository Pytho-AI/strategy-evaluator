class Component extends DCLogic {
  state = {
    view: 'docs', step: 1,
    // Dataset-backed state. Every field is a response body or a control value;
    // nothing here is computed in the browser.
    batch: 0, snap: null, details: {}, options: null, optionsNote: '',
    risks: null, risksNote: '', collection: null, collectionNote: '',
    diffs: {}, diffNote: '', assumptionEvidence: {},
    loading: true, apiError: null, chosen: null,
    ccmd: 'EUCOM', threat: 'VARE',
    decisionNote: '', decision: null,

    // ── Evidence view · GET /api/claims ──────────────────────────────────
    // `claimIndex` is the unfiltered page for the batch; it supplies the
    // filter option lists (the API serves no vocabulary endpoint) and the
    // source table. `claims` is the response for the filters in force.
    claimIndex: null,
    claims: null, claimsLoading: false, claimsError: null,
    filters: { entity: '', source: '', status: '', min_confidence: '', relationship: '' },
    claimLimit: 25, claimOffset: 0,
    claimId: null, claimDetail: null, claimDetailLoading: false, claimDetailError: null,
    kindsSeen: [],
    focusHe: null, focusAssumption: null, openReq: null,

    // ── Write API · P3 ───────────────────────────────────────────────────
    // `writeSupport` maps each capability to the path the backend declares for
    // it, or null. A null renders the endpoint's name, never a dead control.
    writeSupport: {}, writeChecked: false,
    actor: '',
    reportName: 'report.md', reportKind: 'plan', reportText: '', reportBytes: 0,
    ingestBusy: '', ingestResult: null, ingestError: null,
    reviewReason: '', reviewBusy: '', reviewError: null, reviewLog: [],
    // A proposed claim the report did not fully state: the endpoint answers
    // 422 with the field names, and the reviewer supplies exactly those.
    revisionFor: null, revisionFields: [], revision: {},
    planningBusy: '', planningError: null, planningStatus: 'reviewed', planningReason: '',
    draftQuestion: '', draftPir: '', draftAssumption: '', draftEvidence: '',
    draftOwner: '', draftGap: '', draftGapType: 'contradiction', draftLtiov: '',
    draftBusy: false, draftResult: null, draftError: null, decisionResult: null,
    routeTo: '', statusValue: '', statusReason: '',
    reqBusy: '', reqError: null, reqResult: null,
    planning: null, planningNote: '',
    resetBusy: false, resetNotice: '', resetError: null,
  };
  // ── Report intake ────────────────────────────────────────────────────────
  // The artifact's document loader, kept: it still parses .docx/.txt/.md/.pdf
  // in the browser. What changed is where the text goes. It used to be sliced
  // to 600 characters into a display field and then discarded; now the whole
  // text becomes the report body that POST /api/reports stores, hashes and
  // extracts from. Nothing is truncated and nothing is thrown away.
  async readReport(files, kind) {
    const f = files && files[0];
    if (!f) return;
    if (/\.pdf$/i.test(f.name)) {
      this._reportFile = f;
      this.setState({
        ingestBusy: '', ingestError: null, reportText: '', reportBytes: f.size,
        reportName: f.name, reportKind: kind || 'plan',
      });
      return;
    }
    this.setState({ ingestBusy: `Reading ${f.name}…`, ingestError: null });
    let doc;
    try {
      const mod = await import(new URL('assets/docreader.js', document.baseURI).href);
      doc = await mod.readDocument(f);
    } catch (e) {
      this.setState({
        ingestBusy: '',
        ingestError: {
          code: 'read_failed',
          message: `${f.name} could not be read in this browser (${e.message}). Paste the report text instead — nothing is sent to the API until you do.`,
        },
      });
      return;
    }
    const text = doc.text || '';
    if (!text.trim()) {
      this.setState({
        ingestBusy: '',
        ingestError: {
          code: 'no_text',
          message: `${f.name} yielded no extractable text. The API is not called with an empty body; paste the text instead.`,
        },
      });
      return;
    }
    this._reportFile = null;
    this.setState({
      ingestBusy: '', ingestError: null,
      reportText: text, reportBytes: text.length, reportName: f.name,
      reportKind: kind || 'plan',
    });
  }
  async fileBase64(file) {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let out = '';
    for (let i = 0; i < bytes.length; i += 0x8000) {
      out += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    }
    return btoa(out);
  }
  filesFrom(e) { e.preventDefault(); return Array.from((e.dataTransfer && e.dataTransfer.files) || (e.target && e.target.files) || []); }
  THREATS = {
    VARE: { name: 'Varenia', label: 'Varenia', desc: 'Opposing actor in the Meridian Sea theater dataset.' },
    OLV: { name: 'Olvana', label: 'Olvana (OPA)', desc: 'Olvana People\'s Army: full-scale multi-domain invasion of Sungzon and Khorathidin; battlefield nuclear use at Udon Thani 14 MAR 2026; Southern Fleet submarine and SSM threat. DIA-model adversary.' },
    PRC: { name: 'PRC', label: 'China (PRC)', desc: 'Pacing challenge; multi-domain A2/AD, maritime militia, gray-zone coercion.' },
    RUS: { name: 'Russia', label: 'Russia', desc: 'Acute threat; long-range fires, hybrid and nuclear signaling.' },
    IRN: { name: 'Iran', label: 'Iran', desc: 'Proxy networks, missiles and UAS, maritime harassment.' },
    DPRK: { name: 'DPRK', label: 'North Korea', desc: 'Nuclear-armed artillery and missile threat to allies.' },
    VEO: { name: 'VEO', label: 'Violent extremist orgs', desc: 'Dispersed, partner-enabled counter-network problem.' }
  };

  componentDidMount() {
    const v = this.props.startView, st = +this.props.startStep;
    if (v || st) this.setState({ view: v || 'docs', step: st || 1 });
    this.loadBatch(0);
    this.loadDiffs();
  }
  go(view) { this.setState({ view }); }
  goStep(step) { this.setState({ view: 'coa', step }); }
  level(v, th) { return v < th[0] ? 'Low' : v < th[1] ? 'Moderate' : v < th[2] ? 'Significant' : 'High'; }
  // JRAM four-band severity order (CJCSM 3105.01): Low is best.
  score(l) { return { Low: 4, Moderate: 3, Significant: 2, High: 1 }[l] || 0; }
  riskColor(l) { return { Low: ['rgb(19,57,41)', 'rgb(76,195,138)'], Moderate: ['rgb(63,34,0)', 'rgb(255,203,71)'], Significant: ['rgb(130,78,0)', 'rgb(254,243,221)'], High: ['rgb(174,25,85)', 'rgb(254,236,244)'] }[l]; }
  // ── Dataset-backed evaluation ────────────────────────────────────────────
  // Every number on the Strategy Option Evaluation screens comes from the API.
  // The browser sorts and formats; it computes nothing.

  // Stable dataset ids. The workbench evaluates the Blue actor of the Meridian
  // Sea game; entity and strategy names are resolved from the response, never
  // typed here.
  BLUE = { game: 'meridian', actor: 'ent_blue' };
  VALIDITY_ORDER = ['suitable', 'feasible', 'acceptable', 'distinguishable', 'complete'];
  RANGE_LABEL = 'Adversary-scenario range';
  RANGE_NOTE = 'min/max expected value across adversary COAs — not a statistical confidence interval and not a casualty estimate';
  // JP 5-0, Appendix F. Rendered from the API when it serves it (see
  // decisionOverview().caution); this is the doctrinal fallback text so the
  // caution is never absent from a comparison screen.
  APPF_CAUTION = 'JP 5-0, Appendix F: the numerical (weighted) method is not rigorous mathematical analysis. Comparison by criterion is more accurate than comparison of totals.';

  // Every load takes a sequence number and only the newest one may write state.
  // Batch controls stay live while a load is in flight, so two loads can overlap
  // and the slower one can finish last; when it does, its completion — success
  // or error — is dropped instead of pulling the screen back to an old batch.
  _loadSeq = 0;

  async loadBatch(batch) {
    const seq = ++this._loadSeq;
    const stale = () => seq !== this._loadSeq;
    this.setState({ batch, loading: true, apiError: null });
    try {
      const snap = await window.API.getSnapshot(batch);
      const blue = this.blueStrategies(snap);
      const details = {};
      await Promise.all(blue.map(async (s) => {
        details[s.strategy_id] = await window.API.getStrategy(s.strategy_id, batch);
      }));
      // A route the backend has not declared is a named gap, not a failure:
      // its panel says which endpoint would fill it. Anything else propagates.
      const optional = async (call) => {
        try { return { value: await call(), note: '' }; }
        catch (e) {
          if (e.code !== 'not_served') throw e;
          return { value: null, note: e.message };
        }
      };
      const [options, risks, collection, planning, claimIndex, writeSupport] = await Promise.all([
        optional(() => window.API.getStrategies(batch)),
        optional(() => window.API.getRisks(batch)),
        optional(() => window.API.getCollection(batch)),
        optional(() => window.API.getPlanning(batch)),
        window.API.getClaims(batch, { limit: 1000 }),
        window.API.writeSupport(),
      ]);
      if (stale()) return;
      this.setState({
        batch, snap, details,
        options: options.value, optionsNote: options.note,
        risks: risks.value, risksNote: risks.note,
        collection: collection.value, collectionNote: collection.note,
        planning: planning.value, planningNote: planning.note,
        claimIndex, writeSupport, writeChecked: true,
        assumptionEvidence: {},
        claimOffset: 0, claimId: null, claimDetail: null, claimDetailError: null,
        loading: false,
      });
      this.loadClaims(0);
    } catch (e) {
      if (stale()) return;
      this.setState({
        loading: false, snap: null, details: {}, options: null,
        risks: null, collection: null, claimIndex: null, claims: null,
        apiError: { code: e.code || 'error', message: e.message },
      });
    }
  }

  blueStrategies(snap) {
    if (!snap) return [];
    return snap.strategies.filter(s => s.game_id === this.BLUE.game && s.actor_id === this.BLUE.actor);
  }
  blueRanking(snap) {
    if (!snap) return [];
    const r = snap.rankings.find(x => x.game_id === this.BLUE.game && x.actor_id === this.BLUE.actor);
    return r ? r.strategy_ids : [];
  }
  optionFor(id) {
    const o = this.state.options;
    const list = Array.isArray(o) ? o : (o && (o.strategies || o.options)) || [];
    return list.find(x => x && x.strategy_id === id) || null;
  }

  fmt(x, dp) { return x == null || Number.isNaN(Number(x)) ? '—' : Number(x).toFixed(dp == null ? 3 : dp); }
  cap(x) { return x ? String(x)[0].toUpperCase() + String(x).slice(1) : String(x == null ? '' : x); }
  rangeText(r) { return Array.isArray(r) && r.length === 2 ? `${this.fmt(r[0])} to ${this.fmt(r[1])}` : 'unavailable'; }
  batchLabel(b) { return b === 0 ? 'Baseline' : `Intelligence update ${b}`; }

  // Text label + icon on every status, so colour is never the only cue.
  statusChip(status) {
    const m = {
      valid: ['✓ Passes screening', 'rgb(19,57,41)', 'rgb(76,195,138)'],
      invalid: ['✕ Fails screening', 'rgb(174,25,85)', 'rgb(254,236,244)'],
      infeasible: ['✕ Infeasible', 'rgb(174,25,85)', 'rgb(254,236,244)'],
      stale: ['◷ Stale', 'rgb(63,34,0)', 'rgb(255,203,71)'],
      holds: ['✓ Holds', 'rgb(19,57,41)', 'rgb(76,195,138)'],
      violated: ['✕ Violated', 'rgb(174,25,85)', 'rgb(254,236,244)'],
      unknown: ['? Unknown', 'rgb(63,34,0)', 'rgb(255,203,71)'],
    };
    const e = m[status] || [`· ${this.cap(status)}`, 'rgb(30,41,59)', 'var(--color-text)'];
    return { label: e[0], bg: e[1], fg: e[2] };
  }
  riskChip(level) {
    const c = this.riskColor(this.cap(level)) || ['rgb(30,41,59)', 'var(--color-text)'];
    const icon = { low: '○', moderate: '◔', significant: '◑', high: '●' }[level] || '·';
    return { label: `${icon} ${this.cap(level)}`, bg: c[0], fg: c[1] };
  }
  gateFailed(strategy, opt) {
    if (opt && opt.gate_failed) return [].concat(opt.gate_failed).map(g => this.cap(g)).join(', ');
    const failed = (strategy.validity || []).filter(v => !v.passed).map(v => this.cap(v.test));
    return failed.join(', ');
  }

  // ── Panels fed by GET /api/strategies?batch= ─────────────────────────────
  // Each returns rows, or an empty list; the caller turns an empty list into a
  // named "unavailable" note. No panel ever invents a number.
  // `sourced` says whether the API answered for this option at all. An empty
  // list from an endpoint that did answer is a result ("none"), not a gap; a
  // list from an endpoint that did not is unavailable, and says which one.
  panel(title, items, why, sourced) {
    const has = !!(items && items.length);
    return {
      title, has, items: has ? items : [],
      empty: !has && !!sourced,
      unavailable: !has && !sourced,
      note: has ? '' : (sourced ? 'None reported for this option.' : `Unavailable — ${why}`),
    };
  }
  detailNote() {
    return this.state.optionsNote || 'GET /api/strategies?batch= returned no entry for this option';
  }
  objectiveRows(id, opt) {
    const detail = this.state.details[id];
    const weights = (opt && opt.objectives) || (detail && detail.objectives) || [];
    return weights.map(o => ({
      label: o.name || o.objective_id,
      text: `weight ${this.fmt(o.weight, 2)} · contribution ${
        o.expected_contribution == null ? 'unavailable' : this.fmt(o.expected_contribution)
      }${o.rating_1_to_3 == null ? '' : ` · JP 5-0 App. F rating ${o.rating_1_to_3}/3`}`,
    }));
  }
  resourceRows(opt) {
    return ((opt && opt.resources) || []).map(r => ({
      label: `${r.name} (${r.unit})`,
      text: `worst-case use ${this.fmt(r.worst_case_use, 1)} of budget ${this.fmt(r.budget, 1)} · ${
        r.within_budget ? '✓ within budget' : '✕ over budget'}`,
    }));
  }
  chainRows(opt) {
    return ((opt && opt.theory_of_victory) || []).map(e => ({
      label: e.kind,
      text: `${e.from_name || e.from_id} → ${e.to_name || e.to_id} · ${e.mechanism}`,
    }));
  }
  textRows(list) { return (list || []).map((t, i) => ({ label: String(i + 1), text: t })); }
  harmfulRows(list) {
    return (list || []).map(h => ({
      label: h.he_id,
      text: `${h.statement} · ${h.problem_set_name || h.problem_set_id} · ${
        (h.horizons || []).map(x => `${x.jsps_horizon} ${this.cap(x.risk_level)}`).join(', ') || 'no horizon rating'}`,
    }));
  }
  opponentRows(opt) {
    const m = opt && opt.opponent_model;
    return ((m && m.coas) || []).map(c => ({
      label: `${c.name}${c.adversary_coa_label ? ` · ${c.adversary_coa_label.replace(/_/g, ' ')}` : ''}`,
      text: `p ${this.fmt(c.probability, 2)} · ${c.summary}`,
    }));
  }

  decide(status) {
    const ranking = this.blueRanking(this.state.snap);
    const id = ranking.indexOf(this.state.chosen) >= 0 ? this.state.chosen : ranking[0];
    const rec = this.blueStrategies(this.state.snap).find(x => x.strategy_id === id);
    if (!rec) return;
    this.setState({
      decision: {
        status, id: rec.strategy_id, name: rec.name,
        value: this.fmt(rec.value), range: this.rangeText(rec.adversary_range),
        batch: this.batchLabel(this.state.batch), asOf: this.state.snap.as_of,
        time: new Date().toISOString().replace('T', ' ').slice(0, 19) + 'Z',
        note: this.state.decisionNote, hasNote: !!this.state.decisionNote,
      },
    });
  }
  // A strategy the API's ranking does not contain is invalid or infeasible and
  // can never be selected — the guard is here, not in the markup.
  chooseStrategy(id) {
    if (this.blueRanking(this.state.snap).indexOf(id) === -1) return;
    this.setState({ chosen: id });
  }
  // The recommendation is the head of the API's ranking, which contains valid
  // strategies only. An invalid strategy can never reach this function.
  recommended() {
    const snap = this.state.snap;
    if (!snap) return null;
    const id = this.blueRanking(snap)[0];
    if (!id) return null;
    return this.blueStrategies(snap).find(s => s.strategy_id === id) || null;
  }



  // ── P3 · evidence, risk, collection, ingestion ───────────────────────────
  // Loaders first, then the write actions, then the val builders renderVals()
  // calls. No number, level, ranking or outcome is produced here: every one of
  // these functions formats a response body.

  ICD203_NOTE = 'Likelihood is the ICD 203 estimative band the source asserted; confidence is the ICD 203 confidence level in that estimate, and the numeric value beside it is what the API derives from the two. They stay separate fields.';
  BASIS_NOTE = 'current_evidence: the link the evaluator derives at this batch’s as-of date. dependency_edge: an edge in the dataset’s frozen dependency table.';

  _claimSeq = 0;

  activeFilters(filters) {
    const f = filters || this.state.filters, out = {};
    Object.keys(f).forEach(k => { if (f[k] !== '' && f[k] != null) out[k] = f[k]; });
    return out;
  }

  async loadClaims(offset, filters) {
    const seq = ++this._claimSeq;
    const batch = this.state.batch;
    const off = offset == null ? this.state.claimOffset : offset;
    this.setState({ claimsLoading: true, claimsError: null, claimOffset: off });
    try {
      const res = await window.API.getClaims(batch, Object.assign(
        {}, this.activeFilters(filters), { limit: this.state.claimLimit, offset: off }));
      if (seq !== this._claimSeq) return;
      this.setState({ claims: res, claimsLoading: false });
    } catch (e) {
      if (seq !== this._claimSeq) return;
      this.setState({ claimsLoading: false, claimsError: { code: e.code || 'error', message: e.message } });
    }
  }

  setFilter(key, value) {
    const filters = Object.assign({}, this.state.filters, { [key]: value });
    this.setState({ filters, claimOffset: 0 });
    this.loadClaims(0, filters);
  }
  clearFilters() {
    const filters = { entity: '', source: '', status: '', min_confidence: '', relationship: '' };
    this.setState({ filters, claimOffset: 0 });
    this.loadClaims(0, filters);
  }
  pageClaims(delta) {
    const s = this.state;
    const total = s.claims ? s.claims.total : 0;
    const next = Math.min(Math.max(0, s.claimOffset + delta * s.claimLimit), Math.max(0, total - 1));
    if (next === s.claimOffset) return;
    this.loadClaims(next);
  }

  // One claim in full: the exact span, the source, and the trace with every
  // edge's basis. Opening a claim always lands on the evidence screen.
  async openClaim(id) {
    this.setState({ view: 'intel', claimId: id, claimDetail: null, claimDetailError: null, claimDetailLoading: true });
    try {
      const detail = await window.API.getClaim(id, this.state.batch);
      if (this.state.claimId !== id) return;
      const kinds = {};
      this.state.kindsSeen.forEach(k => { kinds[k] = true; });
      const note = e => { if (e.basis === 'dependency_edge') kinds[e.kind] = true; };
      (detail.trace.edges || []).forEach(note);
      (detail.trace.paths || []).forEach(p => (p.edges || []).forEach(note));
      this.setState({ claimDetail: detail, claimDetailLoading: false, kindsSeen: Object.keys(kinds).sort() });
    } catch (e) {
      if (this.state.claimId !== id) return;
      this.setState({ claimDetailLoading: false, claimDetailError: { code: e.code || 'error', message: e.message } });
    }
  }
  closeClaim() { this.setState({ claimId: null, claimDetail: null, claimDetailError: null }); }

  // Every node in a trace links to the screen that owns it.
  goNode(n) {
    if (!n || !n.id) return;
    if (n.type === 'claim') return this.openClaim(n.id);
    if (n.type === 'assumption') return this.setState({ view: 'coa', step: 4, focusAssumption: n.id });
    if (n.type === 'harmful_event') return this.setState({ view: 'coa', step: 3, focusHe: n.id });
    if (n.type === 'strategy') {
      this.setState({ view: 'coa', step: 2 });
      return this.chooseStrategy(n.id);
    }
    return this.setState({ view: 'intel' });
  }

  // ── writes ───────────────────────────────────────────────────────────────
  writePath(key) { return this.state.writeSupport[key] || null; }
  actorName() { return this.state.actor.trim(); }
  reportFilename() {
    const name = this.state.reportName.trim();
    return /\.(txt|md|csv|json|docx|pdf)$/i.test(name) ? name : `${name}.md`;
  }
  needsActor(what) {
    if (this.actorName()) return null;
    return { code: 'actor_required', message: `Record who is ${what}: the API stores the actor, the time and the reason with every decision.` };
  }

  async ingestReport() {
    const s = this.state;
    const file = this._reportFile;
    if (!s.reportName.trim() || (!s.reportText.trim() && !file)) {
      this.setState({ ingestError: { code: 'incomplete', message: 'A file name — its extension picks the parser — and the report text are both required. Nothing is sent to the API until both are present.' } });
      return;
    }
    const missing = this.needsActor('submitting this report');
    if (missing) { this.setState({ ingestError: missing }); return; }
    this.setState({ ingestBusy: 'Storing the report and extracting proposed claims…', ingestError: null });
    try {
      const body = { filename: this.reportFilename(), actor: this.actorName() };
      if (file) {
        body.content_base64 = await this.fileBase64(file);
        body.content_type = file.type || 'application/pdf';
      } else {
        body.text = s.reportText;
      }
      const res = await window.API.ingestReport(body, s.batch);
      this.setState({ ingestResult: res, ingestBusy: '', revisionFor: null, revisionFields: [], revision: {} });
      await this.loadBatch(s.batch);
    } catch (e) {
      this.setState({ ingestBusy: '', ingestError: { code: e.code || 'error', message: e.message } });
    }
  }

  async decideClaim(claimId, decision) {
    const s = this.state;
    const missing = this.needsActor(`${decision === 'accept' ? 'accepting' : 'rejecting'} this claim`);
    if (missing) { this.setState({ reviewError: missing }); return; }
    if (!s.reviewReason.trim()) {
      this.setState({ reviewError: { code: 'reason_required', message: 'A decision reason is required; it is stored with the decision.' } });
      return;
    }
    const revision = s.revisionFor === claimId ? s.revision : null;
    if (revision) {
      const blank = s.revisionFields.filter(f => !String(revision[f] || '').trim());
      if (blank.length) {
        this.setState({ reviewError: { code: 'revision_incomplete', message: `The report does not state ${blank.join(', ')}. Supply them here — nothing is defaulted for you.` } });
        return;
      }
    }
    this.setState({ reviewBusy: claimId, reviewError: null });
    try {
      const body = { decision, actor: this.actorName(), reason: s.reviewReason.trim() };
      if (revision) body.revision = revision;
      const res = await window.API.decideClaim(claimId, body, s.batch);
      const decided = res.decision || {};
      this.setState(st => ({
        reviewBusy: '', reviewReason: '',
        revisionFor: null, revisionFields: [], revision: {},
        decisionResult: res,
        reviewLog: st.reviewLog.concat([{
          claim_id: claimId, decision, actor: decided.actor || this.actorName(),
          reason: decided.reason || s.reviewReason.trim(), at: decided.decided_at || '',
          graph_version: res.graph_version,
        }]),
      }));
      await this.loadBatch(s.batch);
    } catch (e) {
      // The endpoint names the fields the report never stated. Ask for exactly
      // those and resend them in `revision`; never fill one in.
      const fields = (e.detail && e.detail.missing) || [];
      this.setState({
        reviewBusy: '',
        revisionFor: fields.length ? claimId : null,
        revisionFields: fields,
        revision: fields.reduce((acc, f) => Object.assign(acc, { [f]: '' }), {}),
        reviewError: { code: e.code || 'error', message: e.message },
      });
    }
  }
  setRevision(field, value) {
    this.setState(st => ({ revision: Object.assign({}, st.revision, { [field]: value }) }));
  }

  async draftRequirement() {
    const s = this.state;
    if (!s.draftQuestion.trim() && !s.draftPir) {
      this.setState({ draftError: { code: 'incomplete', message: 'A draft needs the strategy question it answers, or the PIR it belongs to.' } });
      return;
    }
    for (const [field, label] of [[s.draftEvidence, 'the evidence that would close the gap'],
      [s.draftGap, 'the gap reason'], [s.draftOwner, 'the proposed owner'],
      [s.draftLtiov, 'the LTIOV date']]) {
      if (!String(field).trim()) {
        this.setState({ draftError: { code: 'incomplete', message: `A draft records ${label}; the endpoint requires it and nothing is defaulted here.` } });
        return;
      }
    }
    const missing = this.needsActor('drafting this requirement');
    if (missing) { this.setState({ draftError: missing }); return; }
    this.setState({ draftBusy: true, draftError: null });
    try {
      const res = await window.API.draftRequirement({
        actor: this.actorName(),
        gap_type: s.draftGapType,
        required_evidence: s.draftEvidence.trim(),
        gap_reason: s.draftGap.trim(),
        proposed_owner: s.draftOwner.trim(),
        ltiov: s.draftLtiov.trim(),
        strategy_question: s.draftQuestion.trim() || null,
        pir_id: s.draftPir || null,
        assumption_id: s.draftAssumption || null,
      }, s.batch);
      this.setState({ draftBusy: false, draftResult: res });
      await this.loadBatch(s.batch);
    } catch (e) {
      this.setState({ draftBusy: false, draftError: { code: e.code || 'error', message: e.message } });
    }
  }

  async routeRequirement(reqId) {
    const s = this.state;
    if (!s.routeTo.trim()) {
      this.setState({ reqError: { code: 'incomplete', message: 'Name the internal queue or authority the requirement is routed to.' } });
      return;
    }
    const missing = this.needsActor('routing this requirement');
    if (missing) { this.setState({ reqError: missing }); return; }
    this.setState({ reqBusy: reqId, reqError: null });
    try {
      const res = await window.API.routeRequirement(reqId, {
        queue: s.routeTo.trim(), actor: this.actorName(),
        reason: s.statusReason.trim() || null,
      }, s.batch);
      this.setState({ reqBusy: '', reqResult: { req_id: reqId, action: 'route', result: res.requirement || res } });
      await this.loadBatch(s.batch);
    } catch (e) {
      this.setState({ reqBusy: '', reqError: { code: e.code || 'error', message: e.message } });
    }
  }

  async setRequirementStatus(reqId) {
    const s = this.state;
    if (!s.statusValue.trim()) {
      this.setState({ reqError: { code: 'incomplete', message: 'Choose the status to record.' } });
      return;
    }
    const missing = this.needsActor('changing this requirement’s status');
    if (missing) { this.setState({ reqError: missing }); return; }
    this.setState({ reqBusy: reqId, reqError: null });
    try {
      const res = await window.API.setRequirementStatus(reqId, {
        status: s.statusValue.trim(), actor: this.actorName(),
        reason: s.statusReason.trim() || null,
      }, s.batch);
      this.setState({ reqBusy: '', reqResult: { req_id: reqId, action: 'status', result: res.requirement || res } });
      await this.loadBatch(s.batch);
    } catch (e) {
      this.setState({ reqBusy: '', reqError: { code: e.code || 'error', message: e.message } });
    }
  }

  // Resets the product's own demo workspace only. The frozen dataset is never
  // written to, so this cannot affect replay.
  async resetWorkspace() {
    this.setState({ resetBusy: true, resetError: null, resetNotice: '' });
    try {
      const res = await window.API.resetWorkspace({ actor: this.actorName() || 'operator' });
      const last = (res.audit || [])[(res.audit || []).length - 1] || {};
      this.setState({
        resetBusy: false,
        resetNotice: `Demo workspace “${res.workspace}” reset${last.at ? ` at ${last.at}` : ''} — ${res.reports} reports, ${res.proposed_claims} proposed claims, ${res.requirements} drafted requirements, graph version ${res.graph_version}. The frozen dataset is untouched.`,
        ingestResult: null, decisionResult: null, reviewLog: [], draftResult: null,
        reqResult: null, revisionFor: null, revisionFields: [], revision: {},
        reportText: '', reportBytes: 0, reportName: 'report.md',
      });
      this._reportFile = null;
      await this.loadBatch(0);
    } catch (e) {
      this.setState({ resetBusy: false, resetError: { code: e.code || 'error', message: e.message } });
    }
  }

  // ── formatting for evidence ──────────────────────────────────────────────
  claimLabelFor(c) {
    const value = c.value === null || c.value === undefined
      ? (c.object_name || c.object_id || '') : c.value;
    return `${c.subject_name || c.subject_id} ${c.predicate} ${value}${c.unit ? ' ' + c.unit : ''}`.trim();
  }
  claimStatusOf(c) { return (c.flags && c.flags.superseded) ? 'superseded' : c.status; }
  claimChip(status) {
    const m = {
      approved: ['✓ Approved', 'rgb(19,57,41)', 'rgb(76,195,138)'],
      proposed: ['◷ Proposed', 'rgb(63,34,0)', 'rgb(255,203,71)'],
      superseded: ['⤳ Superseded', 'rgb(30,41,59)', 'var(--color-neutral-700)'],
      rejected: ['✕ Rejected', 'rgb(174,25,85)', 'rgb(254,236,244)'],
    };
    const e = m[status] || [`· ${this.cap(status)}`, 'rgb(30,41,59)', 'var(--color-text)'];
    return { label: e[0], bg: e[1], fg: e[2] };
  }
  claimFlagText(c) {
    const f = c.flags || {}, out = [];
    if (f.proposed) out.push('Proposed — awaiting review');
    if (f.contradiction) out.push(`Contradiction with ${(f.contradicts_claim_ids || []).join(', ') || 'another claim'}`);
    if (f.stale) out.push('Stale — valid_to is before the as-of date');
    if (f.superseded) out.push(`Superseded by ${f.superseded_by_claim_id || 'a later claim'}`);
    return out.length ? out.join(' · ') : 'No flags';
  }
  validityText(c) {
    if (!c.valid_from && !c.valid_to) return 'no validity window recorded';
    return `${c.valid_from || 'open'} → ${c.valid_to || 'open'}`;
  }
  likelihoodText(c) {
    if (!c.likelihood_icd203 && !c.likelihood_surface_term) return 'not an estimative claim';
    const band = c.likelihood_icd203 ? this.cap(String(c.likelihood_icd203).replace(/_/g, ' ')) : '';
    return c.likelihood_surface_term ? `${c.likelihood_surface_term} (${band})` : band;
  }
  confidenceText(c) {
    return `${this.fmt(c.confidence, 2)}${c.confidence_icd203 ? ` · ${this.cap(c.confidence_icd203)}` : ''}`;
  }
  sourceText(c) {
    const s = c.source;
    if (!s) return 'no source record';
    return `${s.title} · reliability ${s.reliability} · credibility ${s.credibility}`;
  }

  claimRow(c) {
    const chip = this.claimChip(this.claimStatusOf(c));
    const selected = this.state.claimId === c.claim_id;
    return {
      id: c.claim_id, label: this.claimLabelFor(c),
      statusLabel: chip.label, bg: chip.bg, fg: chip.fg,
      flags: this.claimFlagText(c),
      likelihood: this.likelihoodText(c), confidence: this.confidenceText(c),
      source: this.sourceText(c),
      asserted: c.asserted_at || 'not recorded',
      validity: this.validityText(c),
      open: () => this.openClaim(c.claim_id),
      selected,
      rowBg: selected ? 'rgb(16,36,62)' : 'transparent',
      isProposed: !!(c.flags && c.flags.proposed),
      notProposed: !(c.flags && c.flags.proposed),
      accept: () => this.decideClaim(c.claim_id, 'accept'),
      reject: () => this.decideClaim(c.claim_id, 'reject'),
      reviewDisabled: !this.writePath('claimDecision') || this.state.reviewBusy === c.claim_id,
    };
  }

  // Filter vocabularies. The API serves no list endpoint for them, so they are
  // read off the batch's own unfiltered claim page (`claimIndex`) — every value
  // offered is one the API itself returned.
  optionList(pairs) {
    const seen = {};
    pairs.forEach(([value, label]) => { if (value && !seen[value]) seen[value] = label || value; });
    return Object.keys(seen)
      .map(v => ({ value: v, label: `${seen[v]} — ${v}` }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }
  filterOptions() {
    const rows = (this.state.claimIndex && this.state.claimIndex.claims) || [];
    const entities = [];
    const sources = [];
    const statuses = {};
    rows.forEach(c => {
      entities.push([c.subject_id, c.subject_name]);
      if (c.object_id) entities.push([c.object_id, c.object_name]);
      if (c.source) sources.push([c.source.source_id, c.source.title]);
      statuses[this.claimStatusOf(c)] = true;
    });
    const kinds = {};
    this.state.kindsSeen.forEach(k => { kinds[k] = true; });
    const opts = this.state.options;
    const list = (opts && (opts.strategies || opts.options)) || [];
    list.forEach(o => (o.theory_of_victory || []).forEach(e => { kinds[e.kind] = true; }));
    return {
      entity: this.optionList(entities),
      source: this.optionList(sources),
      status: Object.keys(statuses).sort().map(v => ({ value: v, label: this.cap(v) })),
      relationship: Object.keys(kinds).sort().map(v => ({ value: v, label: v })),
    };
  }

  evidenceVals() {
    const s = this.state, res = s.claims, opts = this.filterOptions();
    const rows = (res ? res.claims : []).map(c => this.claimRow(c));
    const total = res ? res.total : 0;
    const from = total ? s.claimOffset + 1 : 0;
    const to = Math.min(s.claimOffset + s.claimLimit, total);
    const select = (key, label, aria, note) => ({
      key, label, aria, note: note || '',
      value: s.filters[key] || '',
      options: [{ value: '', label: `Any ${label.toLowerCase()}` }].concat(opts[key]),
      change: e => this.setFilter(key, e.target.value),
    });
    return {
      loading: s.claimsLoading,
      hasError: !!s.claimsError, error: s.claimsError || {},
      rows, hasRows: rows.length > 0,
      empty: !!res && !s.claimsLoading && rows.length === 0,
      emptyNote: 'No claim in this evidence period matches these filters. Clear one, or select another evidence update.',
      countLabel: res
        ? `${from}–${to} of ${total} claim${total === 1 ? '' : 's'} for ${this.batchLabel(s.batch)}`
        : 'Loading the evidence view…',
      selects: [
        select('entity', 'Entity', 'Filter claims by entity'),
        select('source', 'Source', 'Filter claims by source document'),
        select('status', 'Claim status', 'Filter claims by status'),
        select('relationship', 'Relationship', 'Filter claims by dependency relationship'),
      ],
      minConfidence: s.filters.min_confidence,
      onMinConfidence: e => this.setFilter('min_confidence', e.target.value),
      clear: () => this.clearFilters(),
      batchNote: `Showing ${this.batchLabel(s.batch)} evidence through ${s.snap ? s.snap.as_of : 'the selected date'}.`,
      prev: () => this.pageClaims(-1), next: () => this.pageClaims(1),
      prevDisabled: s.claimOffset === 0,
      nextDisabled: s.claimOffset + s.claimLimit >= total,
      icd: this.ICD203_NOTE,
    };
  }

  nodeVals(n) {
    const label = { source: 'Source', claim: 'Claim', assumption: 'Assumption',
      harmful_event: 'Harmful event', strategy: 'Strategy' }[n.type] || this.cap(n.type);
    return {
      id: n.id, type: label, name: n.name || n.id,
      status: n.status ? this.cap(n.status) : '', hasStatus: !!n.status,
      go: () => this.goNode(n),
      aria: `Open ${label.toLowerCase()} ${n.name || n.id}`,
    };
  }
  edgeVals(e) {
    return {
      kind: e.kind,
      basis: e.basis,
      basisLabel: e.basis === 'current_evidence' ? 'current_evidence' : 'dependency_edge',
      basisText: e.basis === 'current_evidence'
        ? 'current evidence — the link the evaluator derives at this batch’s as-of date'
        : 'dependency edge — an edge in the dataset’s frozen dependency table',
      label: `${e.from_name || e.from_id} → ${e.to_name || e.to_id}`,
      ids: `${e.from_id} → ${e.to_id}`,
      mechanism: e.mechanism || '',
    };
  }

  claimDetailVals() {
    const s = this.state;
    // Every key the panel reads exists in every state: dc-runtime warns on a
    // path that does not resolve, and a warning is a test failure here.
    const blank = {
      open: false, id: '', close: () => this.closeClaim(),
      loading: false, hasError: false, error: { code: '', message: '' },
      hasClaim: false, label: '', statusLabel: '', statusBg: 'transparent', statusFg: 'var(--color-text)',
      flags: '', span: '', spanRange: '', sourceTitle: '', sourcePath: '', sourceMeta: '',
      published: '', asserted: '', validity: '', likelihood: '', confidence: '',
      confidenceBasis: '', icd: this.ICD203_NOTE, basisNote: this.BASIS_NOTE,
      paths: [], edges: [], hasPaths: false, noPaths: false, noPathsNote: '',
      isProposed: false, reviewDisabled: true,
      accept: () => {}, reject: () => {},
    };
    if (!s.claimId) return blank;
    const base = Object.assign({}, blank, {
      open: true, id: s.claimId,
      loading: s.claimDetailLoading,
      hasError: !!s.claimDetailError,
      error: s.claimDetailError || { code: '', message: '' },
    });
    const d = s.claimDetail;
    if (!d) return base;
    const c = d.claim, src = c.source || {}, chip = this.claimChip(this.claimStatusOf(c));
    const paths = (d.trace.paths || []).map((p, i) => {
      const nodes = p.nodes || [];
      const hops = [];
      if (nodes.length > 1) {
        hops.push({
          kind: 'asserts', basisLabel: 'source span',
          basisText: 'the exact span the claim was extracted from — not a graph edge',
          label: `${nodes[0].name || nodes[0].id} → ${nodes[1].name || nodes[1].id}`,
          ids: `${nodes[0].id} → ${nodes[1].id}`,
          mechanism: `characters ${c.span_start}–${c.span_end} of ${src.path || 'the source document'}`,
        });
      }
      (p.edges || []).forEach(e => hops.push(this.edgeVals(e)));
      return {
        n: i + 1,
        title: `Path ${i + 1} · ${nodes.map(x => x.type).join(' → ')}`,
        nodes: nodes.map(x => this.nodeVals(x)),
        hops,
      };
    });
    return Object.assign(base, {
      label: this.claimLabelFor(c),
      statusLabel: chip.label, statusBg: chip.bg, statusFg: chip.fg,
      flags: this.claimFlagText(c),
      span: c.span_text || 'the API returned no span text for this claim',
      spanRange: `characters ${c.span_start}–${c.span_end} of ${src.path || 'the source'}`,
      sourceTitle: src.title || 'no source record',
      sourcePath: src.path || '—',
      sourceMeta: `${src.doc_type || 'unknown type'} · ${src.author_org || 'no author org'} · reliability ${src.reliability || '—'} · credibility ${src.credibility || '—'}`,
      published: src.published_at || 'not recorded',
      asserted: c.asserted_at || 'not recorded',
      validity: this.validityText(c),
      likelihood: this.likelihoodText(c),
      confidence: this.confidenceText(c),
      confidenceBasis: c.confidence_basis || '',
      icd: this.ICD203_NOTE,
      basisNote: this.BASIS_NOTE,
      hasClaim: true,
      accept: () => this.decideClaim(c.claim_id, 'accept'),
      reject: () => this.decideClaim(c.claim_id, 'reject'),
      reviewDisabled: !this.writePath('claimDecision') || s.reviewBusy === c.claim_id,
      paths, hasPaths: paths.length > 0, noPaths: paths.length === 0,
      noPathsNote: 'The API returns no trace path from this claim to an assumption, risk driver or option at this batch.',
      edges: (d.trace.edges || []).map(e => this.edgeVals(e)),
      isProposed: !!(c.flags && c.flags.proposed),
    });
  }

  // ── Risk view · GET /api/risks ───────────────────────────────────────────
  horizonLabel(h) { return `${this.cap(h)}-term`; }
  cascadeVals(e) {
    return {
      names: `${e.from_statement} → ${e.to_statement}`,
      ids: `${e.from_he_id} → ${e.to_he_id}`,
      detail: `lift ${this.fmt(e.lift, 2)} · ${e.mechanism}`,
    };
  }
  riskVals() {
    const s = this.state, r = s.risks;
    if (!r) {
      return { has: false, missing: true,
        note: s.risksNote || 'GET /api/risks returned nothing for this batch.',
        problemSets: [], events: [], escalation: [] };
    }
    const events = (r.harmful_events || []).map(he => {
      const focused = s.focusHe === he.he_id;
      return {
        id: he.he_id, statement: he.statement,
        problemSet: he.problem_set_name || he.problem_set_id,
        riskType: `${he.risk_type}${he.risk_subset ? ` · ${he.risk_subset}` : ''}`,
        thing: he.thing_of_value_name || he.thing_of_value_id || 'not recorded',
        condition: `${he.condition} · base p ${this.fmt(he.base_p, 2)}`,
        posture: (he.posture_subject_names || []).join('; ') || 'no posture subjects',
        sources: (he.sources_of_risk || []).map(x => `${x.source_kind}: ${x.entity_name || x.entity_id}`).join('; ') || 'none recorded',
        focused, border: focused ? 'var(--color-accent)' : 'var(--color-divider)',
        horizons: (he.horizons || []).map(h => {
          const chip = this.riskChip(h.risk_level);
          return {
            horizon: this.horizonLabel(h.jsps_horizon),
            probability: `${this.cap(h.p_level)} (p_raw ${this.fmt(h.p_raw, 2)})`,
            consequence: this.cap(h.c_level),
            levelLabel: chip.label, bg: chip.bg, fg: chip.fg,
            trend: `Trend ${this.cap(h.trend)}`,
            statement: h.statement_text,
            forced: !!h.forced_choice_applied,
            rationale: h.posture_rationale || '',
            drivers: (h.active_drivers || []).map(d => ({
              label: d.label,
              kind: `${d.driver_kind} · ${d.locus}`,
              test: `${d.claim_subject_name || d.claim_subject_id} ${d.claim_predicate} ${d.op} ${d.value}`,
              delta: `+${this.fmt(d.delta, 2)} to P_raw`,
              dominant: !!d.dominant,
              dominantLabel: d.dominant ? '★ dominant driver' : '',
              claims: (d.claims || []).map(c => ({
                id: c.claim_id, label: c.label,
                meta: `${this.cap(c.status)} · confidence ${this.fmt(c.confidence, 2)} · ${c.source_title || c.source_id}`,
                open: () => this.openClaim(c.claim_id),
                aria: `Open claim ${c.claim_id}`,
              })),
              noClaims: !(d.claims || []).length,
            })),
            noDrivers: !(h.active_drivers || []).length,
          };
        }),
        cascadeDown: ((he.cascade || {}).downstream_edges || []).map(e => this.cascadeVals(e)),
        cascadeUp: ((he.cascade || {}).upstream_edges || []).map(e => this.cascadeVals(e)),
        paths: ((he.cascade || {}).upstream_paths || []).map(p => ({ label: [].concat(p).join(' → ') })),
        noCascade: !((he.cascade || {}).downstream_edges || []).length
          && !((he.cascade || {}).upstream_edges || []).length,
      };
    });
    return {
      has: true, missing: false, note: '',
      problemSets: (r.problem_sets || []).map(ps => ({
        id: ps.problem_set_id, name: ps.name,
        owner: ps.risk_owner_role || 'no owner recorded',
        tolerance: ps.tolerance_statement || 'no tolerance statement recorded',
        context: ps.strategic_context || '',
        things: (ps.thing_of_value_names || []).join('; ') || 'none recorded',
        source: ps.risk_context_source
          ? `${ps.risk_context_source.title} · ${ps.risk_context_source.path}`
          : 'no risk-context source in the dataset',
        horizons: (ps.horizons || []).map(h => {
          const chip = this.riskChip(h.max_risk_level);
          return {
            horizon: this.horizonLabel(h.jsps_horizon),
            levelLabel: chip.label, bg: chip.bg, fg: chip.fg,
            events: (h.he_ids || []).map(id => {
              const he = (r.harmful_events || []).find(x => x.he_id === id);
              return he ? `${he.statement} (${id})` : id;
            }).join('; ') || 'none',
            statement: h.aggregated_statement_text,
          };
        }),
      })),
      events,
      escalation: (r.escalation_edges || []).map(e => this.cascadeVals(e)),
    };
  }

  // ── Collection view · GET /api/collection ────────────────────────────────
  priorityBasisText(b) {
    if (!b) return 'no priority basis served';
    if (b.basis === 'evpi') {
      return `EVPI ${this.fmt(b.evpi)} on assumption ${b.assumption_id}`;
    }
    return `Fallback — current claim ${b.claim_id} at confidence ${this.fmt(b.confidence, 2)}, dependency degree ${b.degree}`;
  }
  closureBasisText(r) {
    if (!r.closure_basis) return 'Open — no closure recorded at this batch.';
    if (r.closure_basis === 'manifest_replay') {
      return 'Closure basis: manifest replay — the inject manifest’s expected effect closed it. That is labelled replay, not detection of satisfaction from an independently ingested report.';
    }
    if (r.closure_basis === 'reviewed_evidence') {
      return 'Closure basis: reviewed evidence — accepted claims met the requirement.';
    }
    return `Closure basis: ${r.closure_basis}`;
  }
  collectionVals() {
    const s = this.state, c = s.collection;
    const blue = this.blueStrategies(s.snap);
    const reqs = (c ? c.requirements : []).map(r => {
      const expanded = s.openReq === r.req_id;
      const closed = r.jipcl_rank == null;
      return {
        id: r.req_id,
        rank: closed ? 'closed · unranked' : `JIPCL #${r.jipcl_rank}`,
        status: this.cap(r.status), statusRaw: r.status,
        pir: r.pir_statement || 'no PIR text served',
        pirMeta: `${r.pir_id || 'no PIR id'} · commander’s priority ${r.pir_priority_rank == null ? 'unranked' : `#${r.pir_priority_rank}`} · ${r.commander_role || 'no role recorded'}`,
        eei: r.eei || 'no EEI recorded',
        indicators: (r.indicators || []).map(i => ({ text: i })),
        noIndicators: !(r.indicators || []).length,
        sir: r.sir || 'no specific information requirement recorded',
        gap: `Gap type ${r.gap_type}`,
        ltiov: r.ltiov ? `LTIOV ${r.ltiov}` : 'no LTIOV recorded',
        created: r.created_at ? `raised ${r.created_at}` : '',
        routing: r.routing || 'unrouted',
        authority: r.routing_authority
          ? `${r.routing_authority.name} (${r.routing_authority.approver_role}) approves ${r.routing_authority.recommendation_type} at ${r.routing_authority.risk_level_threshold} risk`
          : 'no approval authority in the dataset for this requirement',
        disposition: r.rfi_disposition ? `RFI disposition ${r.rfi_disposition.replace(/_/g, ' ')}` : '',
        subject: `${r.subject_name || r.subject_id} · ${r.predicate}`,
        priority: `priority ${this.fmt(r.priority)}`,
        basis: this.priorityBasisText(r.priority_basis),
        closure: this.closureBasisText(r),
        answered: r.answered_by_source
          ? `Answered by ${r.answered_by_source.title} · ${r.answered_by_source.path} · published ${r.answered_by_source.published_at}`
          : '',
        hasAnswer: !!r.answered_by_source,
        reopen: r.reopen_reason || r.reopened_reason || '',
        hasReopen: !!(r.reopen_reason || r.reopened_reason),
        assumption: r.assumption ? `${r.assumption.assumption_id} · ${r.assumption.statement} · ${this.cap(r.assumption.status)}` : '',
        hasAssumption: !!r.assumption,
        goAssumption: r.assumption
          ? () => this.goNode({ type: 'assumption', id: r.assumption.assumption_id })
          : () => {},
        affected: (r.affected_strategies || []).map(a => ({
          label: `${a.name} (${a.strategy_id}) · ${this.cap(a.status)}`,
          go: () => this.goNode({ type: 'strategy', id: a.strategy_id }),
        })),
        noAffected: !(r.affected_strategies || []).length,
        assets: (r.candidate_assets || []).map(a => ({
          label: `${a.name} · ${a.discipline} · ${a.owner_org}`,
          detail: `p(success) ${this.fmt(a.p_success, 2)} · latency ${a.latency_periods} periods · cost ${this.fmt(a.cost_per_task, 2)} · ${a.range_ok ? 'in range' : 'out of range'} · ${a.timeliness_ok ? 'timely' : 'not timely'}`,
        })),
        noAssets: !(r.candidate_assets || []).length,
        disciplines: (r.disciplines || []).join(', ') || 'none recorded',
        expanded,
        toggle: () => this.setState({ openReq: expanded ? null : r.req_id }),
        toggleLabel: expanded ? 'Hide routing and status controls' : 'Route or update status',
        route: () => this.routeRequirement(r.req_id),
        setStatus: () => this.setRequirementStatus(r.req_id),
        busy: s.reqBusy === r.req_id,
      };
    });
    const pirs = {};
    (c ? c.requirements : []).forEach(r => { if (r.pir_id) pirs[r.pir_id] = r.pir_statement || r.pir_id; });
    return {
      has: !!c, missing: !c,
      note: s.collectionNote || 'GET /api/collection returned nothing for this batch.',
      requirements: reqs, hasRequirements: reqs.length > 0,
      empty: !!c && reqs.length === 0,
      pirOptions: [{ value: '', label: 'No PIR — a strategy question instead' }].concat(
        Object.keys(pirs).sort().map(k => ({ value: k, label: `${k} — ${pirs[k]}` }))),
      assumptionOptions: [{ value: '', label: 'No assumption linked' }].concat(
        (s.snap ? s.snap.assumptions : [])
          .filter(a => blue.some(b => b.strategy_id === a.strategy_id))
          .map(a => ({ value: a.assumption_id, label: `${a.assumption_id} — ${a.statement}` }))),
    };
  }

  // ── Change explanation · GET /api/injects/{batch}/diff ───────────────────
  // One builder serves both the inject timeline panel and the "what changed"
  // panel after a review decision, because both describe the same six
  // categories of movement.
  nameOf(id) {
    const st = this.blueStrategies(this.state.snap).find(x => x.strategy_id === id);
    return st ? `${st.name} (${id})` : id;
  }
  changePanels(d) {
    if (!d) return [];
    const noop = () => {};
    const panel = (title, rows, empty) => ({
      title, rows, has: rows.length > 0, empty: rows.length === 0,
      emptyNote: empty || 'No change in this category.',
    });
    const ev = d.evidence || {};
    const claimRow = (prefix) => (c) => ({
      label: `${prefix} ${c.claim_id}`,
      text: `${c.label} · ${this.cap(c.status)} · confidence ${this.fmt(c.confidence, 2)} · ${c.source_title || c.source_id}`,
      go: () => this.openClaim(c.claim_id),
    });
    const rank = (list) => (list || []).map(id => this.nameOf(id)).join(' → ') || 'none';
    const rankingRows = [];
    if (d.ranking_before || d.ranking_after) {
      rankingRows.push({
        label: 'Valid ranking',
        text: `${rank(d.ranking_before)}  ⇒  ${rank(d.ranking_after)}`,
        go: noop,
      });
    }
    (d.strategies_restated || []).forEach(x => rankingRows.push({
      label: x.name || x.strategy_id,
      text: `expected value ${this.fmt(x.value_before)} → ${this.fmt(x.value_after)} · ${this.cap(x.status_before)} → ${this.cap(x.status_after)}`,
      go: () => this.goNode({ type: 'strategy', id: x.strategy_id }),
    }));
    return [
      panel('New or changed evidence', [].concat(
        (ev.claims_added || []).map(claimRow('added')),
        (ev.claims_superseded || []).map(claimRow('superseded')),
        (ev.claims_contradicted || []).map(claimRow('contradicted')),
      )),
      panel('Assumption state changes', (d.assumptions_changed || []).map(a => ({
        label: a.assumption_id,
        text: `${a.statement}: ${a.from} → ${a.to} · p(holds) ${this.fmt(a.p_holds_before, 2)} → ${this.fmt(a.p_holds_after, 2)}`,
        go: () => this.goNode({ type: 'assumption', id: a.assumption_id }),
      }))),
      panel('Validity changes', (d.validity_changed || []).map(v => ({
        label: `${v.name || v.strategy_id} · ${this.cap(v.test)}`,
        text: `${v.before ? 'PASS' : 'FAIL'} → ${v.after ? 'PASS' : 'FAIL'}${v.evidence_after ? ` · ${v.evidence_after}` : ''}`,
        go: () => this.goNode({ type: 'strategy', id: v.strategy_id }),
      }))),
      panel('Ranking and value changes', rankingRows),
      panel('Risk changes and cascade paths', (d.risk_assessments_changed || []).map(r => ({
        label: `${r.he_id} · ${r.horizon}-term`,
        text: `${r.statement}: ${this.cap(r.level_before)} → ${this.cap(r.level_after)} · p ${this.fmt(r.p_before, 2)} → ${this.fmt(r.p_after, 2)} · trend ${this.cap(r.trend_before)} → ${this.cap(r.trend_after)}${
          (r.cascade_paths || []).length
            ? ` · cascade ${(r.cascade_paths || []).map(p => [].concat(p).join(' → ')).join('; ')}`
            : ''}`,
        go: () => this.goNode({ type: 'harmful_event', id: r.he_id }),
      })).concat((d.problem_sets_moved || []).map(p => ({
        label: `${p.name || p.problem_set_id} · ${p.jsps_horizon}-term`,
        text: `problem set ${this.cap(p.level_before)} → ${this.cap(p.level_after)}`,
        go: noop,
      })))),
      panel('Collection requirement changes', [].concat(
        // the diff serves closed requirements as bare ids, matching the
        // manifest's own `expected_effects` shape
        (d.requirements_closed || []).map(r => {
          const id = typeof r === 'string' ? r : (r.req_id || r.id || '');
          return {
            label: id,
            text: `closed at this batch${typeof r === 'string' ? '' : (
              r.answered_by_source_id ? ` · answered by ${r.answered_by_source_id}` : '')}`,
            go: noop,
          };
        }),
        (d.jipcl_changed || []).map(r => ({
          label: r.req_id,
          text: `JIPCL rank ${r.rank_before == null ? 'unranked' : r.rank_before} → ${r.rank_after == null ? 'unranked' : r.rank_after} · ${this.cap(r.status_before)} → ${this.cap(r.status_after)}${r.new ? ' · new requirement' : ''}`,
          go: noop,
        })),
      )),
    ];
  }
  diffVals() {
    const s = this.state, d = s.diffs[s.batch] || null;
    if (s.batch === 0) {
      return {
        has: false, baseline: true, unavailable: false, panels: [], note: '',
        heading: 'T0 — no changes; baseline',
        sub: 'T0 is the baseline snapshot. There is no preceding batch to compare it with, so no change is shown.',
      };
    }
    if (!d) {
      return {
        has: false, baseline: false, unavailable: true, panels: [],
        note: s.diffNote || `GET /api/injects/${s.batch}/diff has not answered for this batch.`,
        heading: `${this.batchLabel(s.batch)} — change explanation unavailable`, sub: '',
      };
    }
    return {
      has: true, baseline: false, unavailable: false, panels: this.changePanels(d), note: '',
      heading: `What ${this.batchLabel(s.batch)} changed`,
      sub: `Computed by the API from the ${d.as_of_before} and ${d.as_of_after} snapshots.`,
    };
  }

  // ── Ingest and review · POST /api/reports ────────────────────────────────
  pick(obj, keys) {
    for (const k of keys) {
      if (obj && obj[k] !== null && obj[k] !== undefined) return obj[k];
    }
    return null;
  }
  proposedVals(list) {
    const s = this.state;
    return (list || []).map(c => {
      const flags = [].concat(c.flags || []);
      const notes = [].concat(c.notes || []);
      const contradicts = [].concat(c.contradicts || []);
      return {
        id: c.claim_id,
        label: this.claimLabelFor(c),
        span: c.span_text || 'no span served',
        spanRange: c.span_start == null
          ? 'no offsets served'
          : `characters ${c.span_start}–${c.span_end} of the stored report`,
        asserted: `Asserted ${c.asserted_at || 'not stated in the report'}`,
        validity: `Valid ${this.validityText(c)}`,
        likelihood: this.likelihoodText(c),
        confidence: c.confidence == null
          ? 'not stated in the report'
          : this.confidenceText(c),
        flags: flags.length
          ? `Flagged for review: ${flags.join(', ')}`
          : 'No field flagged',
        notes: notes.map(n => ({ text: n })),
        hasNotes: notes.length > 0,
        contradiction: contradicts.length
          ? `Contradicts ${contradicts.join(', ')}${c.contradicts_reason ? ` — ${c.contradicts_reason}` : ''}. The approved claim is not replaced; both stay on the evidence screen.`
          : '',
        hasContradiction: contradicts.length > 0,
        accept: () => this.decideClaim(c.claim_id, 'accept'),
        reject: () => this.decideClaim(c.claim_id, 'reject'),
        busy: s.reviewBusy === c.claim_id,
        reviewDisabled: !this.writePath('claimDecision') || s.reviewBusy === c.claim_id,
        open: () => this.openClaim(c.claim_id),
        // the fields the report never stated, asked for by name
        needsRevision: s.revisionFor === c.claim_id,
        revisionFields: (s.revisionFor === c.claim_id ? s.revisionFields : []).map(f => ({
          name: f,
          value: s.revision[f] || '',
          change: e => this.setRevision(f, e.target.value),
          aria: `Value for ${f}`,
        })),
      };
    });
  }
  ingestVals() {
    const s = this.state;
    const path = this.writePath('ingestReport');
    const res = s.ingestResult;
    const report = (res && res.report) || {};
    const proposed = (res && res.proposed_claims) || [];
    const instructions = (res && res.instruction_like_spans) || [];
    const decision = s.decisionResult;
    return {
      supported: !!path, notSupported: !path, path: path || '',
      note: path ? '' : 'POST /api/reports is not served by this backend yet. The report stays in the form; nothing is sent and nothing is faked.',
      name: s.reportName, onName: e => this.setState({ reportName: e.target.value }),
      kind: s.reportKind,
      isPlan: s.reportKind === 'plan' && (!!s.reportText || !!this._reportFile),
      isGuidance: s.reportKind === 'guidance' && (!!s.reportText || !!this._reportFile),
      hasFile: !!s.reportText || !!this._reportFile,
      nameNote: 'The extension picks the parser: .txt, .md, .csv, .json are sent as text; a dropped .pdf is sent as its own bytes.',
      text: s.reportText,
      onText: e => this.setState({ reportText: e.target.value, reportBytes: e.target.value.length }),
      actor: s.actor, onActor: e => this.setState({ actor: e.target.value }),
      reason: s.reviewReason, onReason: e => this.setState({ reviewReason: e.target.value }),
      bytes: this._reportFile
        ? `${this._reportFile.size.toLocaleString()} bytes held for local API parsing`
        : s.reportText
        ? `${s.reportText.length.toLocaleString()} characters held in the form`
        : 'no report text yet',
      busy: s.ingestBusy, isBusy: !!s.ingestBusy,
      hasError: !!s.ingestError, error: s.ingestError || { code: '', message: '' },
      submit: () => this.ingestReport(),
      submitLabel: 'Ingest report',
      has: !!res,
      storedTitle: report.filename || s.reportName,
      sourceId: `${report.report_id || 'no report id'} · source ${report.source_id || 'not assigned'}`,
      storedMeta: `${report.format || 'unknown format'} · ${report.text_length || 0} characters stored · uploaded ${report.uploaded_at || 'not recorded'} by ${report.actor || 'unknown actor'}`,
      hash: report.sha256 ? `SHA-256 ${report.sha256}` : 'no content hash served',
      extractor: res ? `Extractor: ${res.extractor || report.extractor || 'not named'}` : '',
      reportDate: report.report_date ? `Report date ${report.report_date}` : 'No report date stated in the document',
      proposed: this.proposedVals(proposed),
      hasProposed: proposed.length > 0,
      noProposed: !!res && proposed.length === 0,
      instructions: instructions.map(x => ({
        text: x.text,
        range: `characters ${x.span_start}–${x.span_end}`,
      })),
      hasInstructions: instructions.length > 0,
      instructionNote: 'Sentences in the report that read as instructions. They are quoted document content, never an action this workbench takes.',
      dedup: res && res.duplicate
        ? `Duplicate of a report already in this workspace — ${report.report_id} was stored once. Re-ingesting it created no second report, claim or requirement.`
        : '',
      isDedup: !!(res && res.duplicate),
      // what the accepted evidence changed
      changePanels: decision ? this.changePanels(decision.changes) : [],
      hasChanges: !!decision,
      graphVersion: decision ? `Graph version ${decision.graph_version} · evaluated at ${decision.as_of}` : '',
      contradiction: decision && (decision.contradicts || []).length
        ? `This claim contradicts ${decision.contradicts.join(', ')}. ${decision.contradiction_reason || ''} The evaluator uses ${decision.chosen_claim_id} as current; both claims stay on the evidence screen.`
        : '',
      hasContradiction: !!(decision && (decision.contradicts || []).length),
      requirementsChanged: decision
        ? (decision.requirements_changed || []).map(r => ({
            label: typeof r === 'string' ? r : (r.req_id || ''),
            text: typeof r === 'string' ? 'requirement state changed'
              : `${this.cap(r.status || '')}${r.closure_basis ? ` · closure basis ${r.closure_basis.replace(/_/g, ' ')}` : ''}`,
          }))
        : [],
      planningFlags: decision
        ? (decision.planning_flags || []).map(f => ({
            label: `${f.object_id} · ${f.kind}`,
            text: `${f.text} — ${f.reason}`,
            options: (f.dependent_options || []).join(', ') || 'no dependent option',
          }))
        : [],
      hasPlanningFlags: !!(decision && (decision.planning_flags || []).length),
    };
  }

  // ── Tracked planning objects ─────────────────────────────────────────────
  // Assumptions, constraints and restraints, with whatever provenance the
  // dataset actually carries. Where it carries none, the row says so; nothing
  // is invented to fill a column.
  async loadAssumptionEvidence(id) {
    this.setState(s => ({ assumptionEvidence: Object.assign({}, s.assumptionEvidence, { [id]: { loading: true } }) }));
    try {
      const res = await window.API.getClaims(this.state.batch, { assumption: id, limit: 50 });
      this.setState(s => ({ assumptionEvidence: Object.assign({}, s.assumptionEvidence, { [id]: { loading: false, claims: res.claims } }) }));
    } catch (e) {
      this.setState(s => ({ assumptionEvidence: Object.assign({}, s.assumptionEvidence, { [id]: { loading: false, error: e.message } }) }));
    }
  }
  // Every batch's diff, once. Feeds the change explanation panel and the
  // per-object change history.
  async loadDiffs() {
    const meta = window.API_META;
    const batches = (meta ? meta.batches.map(b => b.batch) : [0, 1, 2, 3]).filter(b => b > 0);
    const out = {};
    let note = '';
    await Promise.all(batches.map(async (b) => {
      try { out[b] = await window.API.getDiff(b); }
      catch (e) { if (e.code !== 'not_served') throw e; note = e.message; }
    }));
    this.setState({ diffs: out, diffNote: note });
  }
  flaggedObjects() {
    const res = this.state.ingestResult;
    const changes = this.pick(res, ['changes', 'recompute', 'effects']) || res;
    const flagged = this.pick(changes, ['flagged_planning_objects', 'flagged', 'affected_planning_objects']) || [];
    return [].concat(flagged).map(x => (typeof x === 'string' ? x : (x.id || x.object_id || '')));
  }
  planningVals() {
    const s = this.state, blue = this.blueStrategies(s.snap);
    const flagged = this.flaggedObjects();
    const list = (s.options && (s.options.strategies || s.options.options)) || [];
    const history = id => {
      const rows = [];
      Object.keys(s.diffs).sort().forEach(b => {
        (s.diffs[b].assumptions_changed || []).forEach(a => {
          if (a.assumption_id === id) {
            rows.push({ text: `Inject batch ${b}: ${a.from} → ${a.to} · p(holds) ${this.fmt(a.p_holds_before, 2)} → ${this.fmt(a.p_holds_after, 2)}` });
          }
        });
      });
      return rows;
    };
    const textRows = (option, kind, items) => (items || []).map((t, i) => ({
      id: `${option.strategy_id} · ${kind} ${i + 1}`,
      option: option.name, text: t,
    }));
    const assumptions = (s.snap ? s.snap.assumptions : [])
      .filter(a => blue.some(b => b.strategy_id === a.strategy_id))
      .map(a => {
        const chip = this.statusChip(a.status);
        const ev = s.assumptionEvidence[a.assumption_id] || null;
        const h = history(a.assumption_id);
        return {
          id: a.assumption_id, statement: a.statement,
          option: (blue.find(x => x.strategy_id === a.strategy_id) || {}).name || a.strategy_id,
          statusLabel: chip.label, bg: chip.bg, fg: chip.fg,
          detail: `p(holds) ${this.fmt(a.p_holds, 2)} · sensitivity ${this.fmt(a.sensitivity)} · EVPI ${this.fmt(a.evpi)}`,
          screen: `Predicate ${a.subject_name || a.subject_id} ${a.predicate} ${a.tolerance_op} ${a.tolerance_value} · role ${a.role} · origin ${a.origin}`,
          jp50: `JP 5-0 screen — logical ${a.jp50_logical ? 'yes' : 'no'}, realistic ${a.jp50_realistic ? 'yes' : 'no'}, essential ${a.jp50_essential ? 'yes' : 'no'}; in the decision matrix: ${a.in_decision_matrix ? 'yes' : 'no'}`,
          review: s.planning
            ? (this.pick((s.planning.assumptions || []).find(x => x.assumption_id === a.assumption_id) || {}, ['review_status', 'status']) || 'no review recorded')
            : 'Product review state is not served yet — GET /api/planning would carry it.',
          history: h, hasHistory: h.length > 0,
          historyNote: 'No state change across the inject batches the API serves.',
          flagged: flagged.indexOf(a.assumption_id) >= 0,
          flagLabel: '⚑ Flagged — accepted evidence moved this object',
          evidenceLoading: !!(ev && ev.loading),
          evidenceError: (ev && ev.error) || '',
          hasEvidenceError: !!(ev && ev.error),
          evidence: ev && ev.claims ? ev.claims.map(c => ({
            id: c.claim_id,
            label: this.claimLabelFor(c),
            source: this.sourceText(c),
            span: c.span_text || 'no span served',
            validity: this.validityText(c),
            confidence: this.confidenceText(c),
            open: () => this.openClaim(c.claim_id),
          })) : [],
          hasEvidence: !!(ev && ev.claims && ev.claims.length),
          emptyEvidence: !!(ev && ev.claims && !ev.claims.length),
          loadEvidence: () => this.loadAssumptionEvidence(a.assumption_id),
          evidenceNote: 'Claims the frozen dependency table records as grounding this assumption. The claim the evaluator actually uses at this batch may be a newer one with no dependency edge — open a claim to see its current_evidence link.',
          go: () => this.goNode({ type: 'assumption', id: a.assumption_id }),
        };
      });
    return {
      assumptions, hasAssumptions: assumptions.length > 0,
      constraints: [].concat.apply([], list.map(o => textRows(o, 'constraint', o.constraints))),
      restraints: [].concat.apply([], list.map(o => textRows(o, 'restraint', o.restraints))),
      note: s.optionsNote,
      provenanceNote: 'The dataset carries constraints and restraints as option text only: no source span, validity window, confidence or review state. Those columns are absent, not empty — nothing is invented to fill them.',
      planningNote: s.planning ? '' : (this.writePath('planning')
        ? 'GET /api/planning answered with nothing for this batch.'
        : 'Product-owned review state and change links need GET /api/planning, which this backend does not declare yet.'),
    };
  }

  // ── The workspace indicator, on every wired screen ───────────────────────
  // The read endpoints omit the overlay keys entirely until reviewed evidence
  // has been applied, so their presence — not their value — is the test.
  overlayVals() {
    const snap = this.state.snap || {};
    const applied = 'overlay_applied' in snap;
    if (!applied) {
      return {
        has: false,
        label: 'Graph v0 · no workspace overlay',
        note: 'Frozen dataset only: nothing accepted in this demo workspace has changed this batch.',
      };
    }
    return {
      has: true,
      label: `Graph v${snap.graph_version} · workspace overlay applied`,
      note: `Reviewed evidence in workspace “${snap.workspace}” is applied over the frozen dataset. Evaluated at ${snap.as_of}; the inject batch's own date is ${snap.batch_as_of}, and the gap between them is the newly reported evidence.`,
    };
  }
  reviewVals() {
    const s = this.state;
    return {
      rows: s.reviewLog.map(r => ({
        label: `${r.claim_id} · ${r.decision}`,
        text: `${r.actor}${r.at ? ` · ${r.at}` : ''} · ${r.reason}`,
      })),
      has: s.reviewLog.length > 0,
      hasError: !!s.reviewError, error: s.reviewError || {},
      note: this.writePath('claimDecision')
        ? ''
        : 'Accept / reject needs POST /api/claims/proposed/{id}/decision, which this backend does not declare yet. The controls stay disabled until it is.',
      supported: !!this.writePath('claimDecision'),
      notSupported: !this.writePath('claimDecision'),
    };
  }
  draftVals() {
    const s = this.state, c = this.collectionVals();
    const path = this.writePath('draftRequirement');
    const dedup = this.pick(s.draftResult, ['duplicate_of', 'duplicate', 'existing_req_id', 'deduplicated']);
    const result = (s.draftResult && s.draftResult.requirement) || s.draftResult;
    return {
      supported: !!path, notSupported: !path, path: path || '',
      note: path ? '' : 'POST /api/collection/drafts is not served by this backend yet; the form records nothing until it is.',
      question: s.draftQuestion, onQuestion: e => this.setState({ draftQuestion: e.target.value }),
      pir: s.draftPir, onPir: e => this.setState({ draftPir: e.target.value }),
      pirOptions: c.pirOptions,
      assumption: s.draftAssumption, onAssumption: e => this.setState({ draftAssumption: e.target.value }),
      assumptionOptions: c.assumptionOptions,
      evidence: s.draftEvidence, onEvidence: e => this.setState({ draftEvidence: e.target.value }),
      gap: s.draftGap, onGap: e => this.setState({ draftGap: e.target.value }),
      gapType: s.draftGapType, onGapType: e => this.setState({ draftGapType: e.target.value }),
      gapTypes: ['missing', 'stale', 'low_confidence', 'contradiction'].map(value => ({
        value, label: value.replace(/_/g, ' '), selected: value === s.draftGapType,
      })),
      owner: s.draftOwner, onOwner: e => this.setState({ draftOwner: e.target.value }),
      ltiov: s.draftLtiov, onLtiov: e => this.setState({ draftLtiov: e.target.value }),
      submit: () => this.draftRequirement(),
      busy: s.draftBusy,
      hasError: !!s.draftError, error: s.draftError || {},
      has: !!s.draftResult,
      resultId: this.pick(result, ['req_id', 'requirement_id', 'id']) || '',
      resultStatus: this.pick(result, ['status']) || '',
      dedup: dedup ? `Deduplicated — this gap is already tracked as ${typeof dedup === 'string' ? dedup : JSON.stringify(dedup)}. No second requirement was created.` : '',
      isDedup: !!dedup,
      raw: s.draftResult ? JSON.stringify(s.draftResult, null, 1).slice(0, 1500) : '',
    };
  }
  requirementControlVals() {
    const s = this.state;
    return {
      routeSupported: !!this.writePath('routeRequirement'),
      statusSupported: !!this.writePath('statusRequirement'),
      routeDisabled: !this.writePath('routeRequirement') || !!s.reqBusy,
      statusDisabled: !this.writePath('statusRequirement') || !!s.reqBusy,
      notSupported: !(this.writePath('routeRequirement') && this.writePath('statusRequirement')),
      note: this.writePath('routeRequirement') && this.writePath('statusRequirement')
        ? ''
        : 'Routing and status updates need the POST …/route and …/status endpoints, which this backend does not declare yet.',
      routeTo: s.routeTo, onRouteTo: e => this.setState({ routeTo: e.target.value }),
      statusValue: s.statusValue, onStatusValue: e => this.setState({ statusValue: e.target.value }),
      statusOptions: [
        { value: '', label: 'Choose status' },
        { value: 'research', label: 'Research' },
        { value: 'validation', label: 'Validation' },
        { value: 'submission', label: 'Submission' },
      ],
      statusReason: s.statusReason, onStatusReason: e => this.setState({ statusReason: e.target.value }),
      hasError: !!s.reqError, error: s.reqError || {},
      has: !!s.reqResult,
      resultText: s.reqResult
        ? `${s.reqResult.req_id} · ${s.reqResult.action} recorded${this.pick(s.reqResult.result, ['status']) ? ` · status ${this.pick(s.reqResult.result, ['status'])}` : ''}`
        : '',
    };
  }

  // The source table on the evidence screen: every document the batch's claims
  // cite, with how many claims cite it. Clicking one filters the claim list.
  sourceVals() {
    const rows = (this.state.claimIndex && this.state.claimIndex.claims) || [];
    const by = {};
    rows.forEach(c => {
      const src = c.source;
      if (!src) return;
      const e = by[src.source_id] || (by[src.source_id] = { src, n: 0 });
      e.n += 1;
    });
    return Object.keys(by)
      .map(id => ({
        id, title: by[id].src.title,
        type: by[id].src.doc_type,
        org: by[id].src.author_org || 'no author org',
        rating: `${by[id].src.reliability} / ${by[id].src.credibility}`,
        published: by[id].src.published_at || 'not recorded',
        batch: by[id].src.batch,
        batchLabel: by[id].src.batch === 0 ? 'T0' : `batch ${by[id].src.batch}`,
        claims: `${by[id].n} claim${by[id].n === 1 ? '' : 's'}`,
        pick: () => this.setFilter('source', id),
        aria: `Filter the claim list to ${by[id].src.title}`,
      }))
      .sort((a, b) => (b.batch - a.batch) || a.title.localeCompare(b.title));
  }

  // The RFI screen: the same requirements, seen as the routing queue.
  routingQueueVals() {
    const c = this.state.collection;
    return (c ? c.requirements : []).map(r => ({
      id: r.req_id,
      question: r.eei || r.pir_statement || r.sir || 'no question text served',
      routing: r.routing || 'unrouted',
      authority: r.routing_authority ? r.routing_authority.name : 'no approval authority in the dataset',
      ties: r.assumption
        ? `${r.assumption.assumption_id} · ${r.assumption.statement}`
        : ((r.affected_strategies || []).map(a => a.name).join(', ') || 'no linked assumption or option'),
      status: this.cap(r.status),
      disposition: r.rfi_disposition ? r.rfi_disposition.replace(/_/g, ' ') : 'no disposition recorded',
      ltiov: r.ltiov || 'no LTIOV',
      go: () => this.setState({ view: 'collection', openReq: r.req_id }),
    }));
  }

  renderVals() {
    const s = this.state, T = this.THREATS[s.threat];
    const stage = s.view === 'coa' ? (s.step === 3 ? 3 : s.step === 5 ? 4 : 1) : ['collection', 'rfi'].includes(s.view) ? 2 : ['intel', 'docs', 'posture'].includes(s.view) ? 5 : 0;
    // Everything the COA screens render comes off these four API responses.
    const snap = s.snap, meta = window.API_META || null;
    const blue = this.blueStrategies(snap), ranking = this.blueRanking(snap);
    const rec = this.recommended();
    const selectedId = ranking.indexOf(s.chosen) >= 0 ? s.chosen : (rec ? rec.strategy_id : null);
    const assumptionsFor = id => (snap ? snap.assumptions.filter(a => a.strategy_id === id) : []);
    const ov = (snap && snap.decision_overview) || null;
    const missingOverview = 'Unavailable — /api/snapshot serves no decision_overview block yet';
    const set = k => e => this.setState({ [k]: e.target.value });
    const B = window.BRANDING;
    return {
      brandMark: B.teamMark, brandTitle: B.title, brandProduct: B.productName,
      crumb: { coa: { 1: 'Strategy Evaluation / Decision Overview', 2: 'Strategy Evaluation / COA Comparison', 3: 'Interconnected Risk', 4: 'Strategy Evaluation / Assumptions', 5: 'Recommend Strategy', 6: 'Strategy Evaluation / Evidence Updates' }[s.step], docs: 'Plans & Strategic Guidance', intel: 'Intelligence', collection: 'Collection Management', rfi: 'RFI Management', posture: 'Force Posture & GFM', doctrine: 'Doctrine' }[s.view],
      showWorkflow: s.view !== 'doctrine',
      isCoa: s.view === 'coa', isIntel: s.view === 'intel', isCollection: s.view === 'collection', isRfi: s.view === 'rfi', isPosture: s.view === 'posture', isDoctrine: s.view === 'doctrine',
      stages: [['Strategy Evaluation', 'Compare COAs against objectives, resources, assumptions, and the five JP 5-0 screening tests.', 1], ['Collection Management', 'Turn intelligence gaps into requirements, route them, and track their status.', 2], ['Interconnected Risk', 'Show how a change to one condition affects related problem sets and COAs.', 3], ['Recommend Strategy', 'Present the recommended COA, its assumptions, tradeoffs, and accepted risk.', 4]].map(([label, sub, n]) => { const active = stage === n; const done = n === 1 ? !!snap : n === 2 ? !!(s.collection && s.collection.requirements.some(r => r.closure_basis)) : n === 3 ? !!s.risks : !!s.decision; return { n, label, sub, lineShow: n < 4 ? 'block' : 'none', go: () => n === 1 ? this.setState({ view: 'coa', step: [1, 2, 4, 6].includes(s.step) ? s.step : 1 }) : n === 2 ? this.go('collection') : n === 3 ? this.setState({ view: 'coa', step: 3 }) : this.setState({ view: 'coa', step: 5 }), ring: active || done ? 'var(--color-accent)' : 'var(--color-divider)', bg: active ? 'rgb(16,42,76)' : done ? 'rgb(9,84,165)' : 'var(--color-surface)', fg: active || done ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: active ? 1 : 0.65 }; }),
      foundation: { go: () => this.go('intel'), ring: stage === 5 ? 'var(--color-accent)' : 'var(--color-divider)', bg: stage === 5 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: stage === 5 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', stat: s.claimIndex ? `${s.claimIndex.total} claims · ${this.sourceVals().length} source documents · ${(s.collection ? s.collection.requirements.length : 0)} collection requirements` : 'waiting on /api/claims' },
      hasSubtabs: stage === 1 || stage === 5,
      subtabs: stage === 1 ? [['Decision Overview', 1], ['COA Comparison', 2], ['Assumptions', 4], ['Evidence Updates', 6]].map(([label, st]) => ({ label, go: () => this.goStep(st), line: s.step === st ? 'var(--color-accent)' : 'transparent', opacity: s.step === st ? 1 : 0.65 })) : [['Intelligence', 'intel'], ['Plans & Strategic Guidance', 'docs'], ['Force Posture & GFM', 'posture']].map(([label, v]) => ({ label, go: () => this.go(v), line: s.view === v ? 'var(--color-accent)' : 'transparent', opacity: s.view === v ? 1 : 0.65 })),
      step2: s.step === 2, step3: s.step === 3, step4: s.step === 4, step5: s.step === 5,
      step6: s.step === 6,
      goHome: () => this.setState({ view: 'docs', step: 1 }),
      goUpdates: () => this.setState({ view: 'coa', step: 6 }),
      goCollection: () => this.go('collection'), goIntel: () => this.go('intel'),
      goDocs: () => this.go('docs'), goPosture: () => this.go('posture'),
      goRfi: () => this.go('rfi'), goDoctrine: () => this.go('doctrine'),
      scenarioLabel: ov ? ov.scenario_name : 'Scenario unavailable',
      ccmd: s.ccmd, threatName: ov ? ov.adversary_name : T.name,
      dataSourceNote: ov
        ? `Source: ${ov.scenario_name} dataset · ${ov.friendly_force_name} COAs · validity computed by the API using the five JP 5-0 screening tests · evidence current through ${snap.as_of}.`
        : 'Scenario source information is unavailable.',
      // ── Inject timeline ────────────────────────────────────────────────
      // T0 plus the three inject batches. Selecting one refetches the backend
      // snapshot for that batch; nothing is mutated, so any batch can be
      // revisited in any order.
      batchButtons: (meta ? meta.batches.map(b => b.batch) : [0, 1, 2, 3]).map(b => ({
        n: b, label: b === 0 ? 'Baseline' : `Update ${b}`,
        aria: `Show ${this.batchLabel(b)}`,
        pressed: s.batch === b,
        border: s.batch === b ? 'var(--color-accent)' : 'var(--color-divider)',
        bg: s.batch === b ? 'rgb(16,36,62)' : 'transparent',
        pick: () => this.loadBatch(b),
      })),
      recompute: () => this.loadBatch(s.batch),
      batchName: this.batchLabel(s.batch),
      asOf: snap ? snap.as_of : '—',
      asOfLabel: snap ? `As of ${snap.as_of}` : 'No snapshot',
      batchStatus: s.loading
        ? `Loading ${this.batchLabel(s.batch)}…`
        : (snap ? `${this.batchLabel(s.batch)} · evidence through ${snap.as_of} · ${blue.length} COAs evaluated · ${ranking.length} pass all five screening tests` : 'No evaluation loaded'),
      hasApiError: !!s.apiError, apiError: s.apiError || {},
      retry: () => this.loadBatch(s.batch),
      marking: (window.BRANDING && window.BRANDING.marking) || '',
      steps: [['Strategy Preparation', 'Mission Analysis & Guidance'], ['Development', 'Concepts & Screening'], ['Option Adjudication', 'Wargames · ARC'], ['Option\nComparison', 'Decision Matrix'], ['Strategy Decision', "Commander's decision"]].map(([label, sub], i) => ({ n: i + 1, label, sub, go: () => this.goStep(i + 1),
        lineShow: i < 4 ? 'block' : 'none', ring: s.step >= i + 1 ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.step > i + 1 ? 'rgb(9,84,165)' : s.step === i + 1 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: s.step >= i + 1 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: s.step === i + 1 ? 1 : 0.6 })),

      // ══ Decision overview (entry screen and Option Recommendation) ══════
      showOverview: s.step === 1 || s.step === 5,
      hasSnapshot: !!snap && !s.loading,
      noSnapshot: !snap && !s.apiError,
      hasRec: !!rec,
      noRec: !!snap && !rec,
      rangeLabel: this.RANGE_LABEL, rangeNote: this.RANGE_NOTE,
      // JP 5-0 App. F. From the API when it serves it; the doctrinal text
      // otherwise, labelled with where it came from.
      caution: (ov && ov.caution) || this.APPF_CAUTION,
      cautionSource: ov && ov.caution ? 'GET /api/snapshot · decision_overview.caution' : 'JP 5-0 Appendix F (API does not serve decision_overview.caution yet)',
      rec: rec ? {
        id: rec.strategy_id, name: rec.name,
        statusLabel: this.statusChip(rec.status).label,
        statusBg: this.statusChip(rec.status).bg, statusFg: this.statusChip(rec.status).fg,
        value: this.fmt(rec.value),
        range: this.rangeText(rec.adversary_range),
        robustness: this.fmt(rec.robustness),
        riskFunctional: ov && ov.recommended && ov.recommended.risk_functional
          ? `${ov.recommended.risk_functional}${ov.recommended.risk_alpha == null ? '' : ` (α ${this.fmt(ov.recommended.risk_alpha, 2)})`}`
          : (this.optionFor(rec.strategy_id) ? this.optionFor(rec.strategy_id).risk_functional : 'unavailable'),
        rankNote: `Ranks first among the ${ranking.length} COA${ranking.length === 1 ? '' : 's'} that pass all five screening tests.`,
      } : { id: '', name: '', statusLabel: '', value: '', range: '', robustness: '', riskFunctional: '', rankNote: '' },
      briefingRationale: rec
        ? `${rec.name} is recommended because it has the highest evaluated value (${this.fmt(rec.value)}) against the adversary COAs and passes all five JP 5-0 screening tests.${ranking.length > 1 ? ` ${((blue.find(x => x.strategy_id === ranking[1]) || {}).name || 'The next-ranked COA')} has ${Number((blue.find(x => x.strategy_id === ranking[1]) || {}).robustness) > Number(rec.robustness) ? 'stronger' : 'weaker'} worst-case performance; that is the main tradeoff.` : ''}`
        : '',
      // "Why does it rank first?" — the API's criterion breakdown when served,
      // otherwise the validity evidence and the value gap it does serve.
      whyRows: ov && ov.why
        ? ov.why.winning_criteria.map(c => ({
            label: c.name || c.objective_id,
            text: `weight ${this.fmt(c.weight, 2)} · contribution ${this.fmt(c.contribution)}${
              c.runner_up_contribution == null ? '' : ` vs runner-up ${this.fmt(c.runner_up_contribution)}`}`,
          }))
        : (rec ? (rec.validity || []).filter(v => v.passed).map(v => ({ label: this.cap(v.test), text: v.evidence })) : []),
      whySource: ov && ov.why
        ? 'GET /api/snapshot · decision_overview.why.winning_criteria'
        : `Criterion breakdown ${missingOverview.toLowerCase()}. Shown instead: the validity evidence the API serves for ${rec ? rec.name : 'the recommended option'}.`,
      tradeoff: ov && ov.why && ov.why.tradeoff
        ? `Against ${ov.why.tradeoff.runner_up_name}: ${this.fmt(ov.why.tradeoff.value_gap)} of expected value, ${
            ov.why.tradeoff.objectives_favouring_runner_up.length
              ? `${ov.why.tradeoff.objectives_favouring_runner_up.map(c => c.name || c.objective_id).join(', ')} favour${
                  ov.why.tradeoff.objectives_favouring_runner_up.length === 1 ? 's' : ''}`
              : 'no objective favours'} the runner-up.`
        : (ranking.length > 1 && rec
          ? `Runner-up ${(blue.find(x => x.strategy_id === ranking[1]) || {}).name}: expected value ${this.fmt((blue.find(x => x.strategy_id === ranking[1]) || {}).value)} against ${this.fmt(rec.value)}, robustness ${this.fmt((blue.find(x => x.strategy_id === ranking[1]) || {}).robustness)} against ${this.fmt(rec.robustness)}.`
          : 'No runner-up: only one valid option.'),
      tradeoffSource: ov && ov.why && ov.why.tradeoff
        ? 'GET /api/snapshot · decision_overview.why.tradeoff'
        : `Per-objective tradeoff ${missingOverview.toLowerCase()}. Shown instead: value and robustness against the runner-up.`,
      topSensitivities: (ov && ov.highest_sensitivity_assumptions && ov.highest_sensitivity_assumptions.length
        ? ov.highest_sensitivity_assumptions
        : (snap ? snap.assumptions.filter(a => blue.some(b => b.strategy_id === a.strategy_id)) : [])
          .slice().sort((a, b) => (b.sensitivity || 0) - (a.sensitivity || 0)).slice(0, 4)
      ).map(a => ({
        id: a.assumption_id, statement: a.statement,
        strategy: (blue.find(x => x.strategy_id === a.strategy_id) || {}).name || a.strategy_id,
        statusLabel: this.statusChip(a.status).label,
        bg: this.statusChip(a.status).bg, fg: this.statusChip(a.status).fg,
        sens: this.fmt(a.sensitivity), evpi: this.fmt(a.evpi),
        go: () => this.goStep(4),
      })),
      topReq: (() => {
        const r = (ov && ov.top_collection_requirement) || (snap
          ? snap.collection_requirements.filter(x => x.jipcl_rank != null)
            .slice().sort((a, b) => a.jipcl_rank - b.jipcl_rank)[0]
          : null);
        if (!r) return { has: false, id: '', line: '', pir: '', gap: '' };
        return {
          has: true, id: r.req_id,
          line: `${this.cap(r.status)} · JIPCL rank ${r.jipcl_rank == null ? 'unranked' : r.jipcl_rank} · priority ${this.fmt(r.priority)}${
            r.priority_basis ? ` (basis ${r.priority_basis.basis})` : ''}`,
          pir: r.pir_statement || (r.pir_id ? `PIR ${r.pir_id}` : `Requirement text unavailable — /api/collection is not wired into this screen yet`),
          gap: r.gap_type ? `Gap type ${r.gap_type}${r.ltiov ? ` · LTIOV ${r.ltiov}` : ''}` : '',
        };
      })(),
      topRisks: (ov && ov.highest_risks && ov.highest_risks.length
        ? ov.highest_risks.map(h => ({
            label: h.problem_set_name || h.problem_set_id,
            chip: this.riskChip(h.risk_level),
            text: `${h.statement} · ${h.jsps_horizon}-term · trend ${h.trend}`,
          }))
        : (snap ? snap.problem_set_assessments : [])
          .slice()
          .sort((a, b) => this.score(this.cap(a.max_risk_level)) - this.score(this.cap(b.max_risk_level)))
          .slice(0, 4)
          .map(pS => ({
            label: pS.problem_set_id,
            chip: this.riskChip(pS.max_risk_level),
            text: `${pS.jsps_horizon}-term · ${pS.he_ids.length} harmful event${pS.he_ids.length === 1 ? '' : 's'} · ${pS.aggregated_statement_text}`,
          }))
      ).map(r => ({ ...r, chipLabel: r.chip.label, chipBg: r.chip.bg, chipFg: r.chip.fg, go: () => this.goStep(3) })),
      goCompare: () => this.goStep(2),

      // ══ Strategy comparison (step 2) ═══════════════════════════════════
      options: blue.map(st => {
        const o = this.optionFor(st.strategy_id);
        const rank = ranking.indexOf(st.strategy_id);
        const chip = this.statusChip(st.status);
        const gate = this.gateFailed(st, o);
        const recommendable = rank >= 0;
        const isSel = st.strategy_id === selectedId;
        const why = this.detailNote();
        return {
          id: st.strategy_id, name: st.name,
          summary: o ? o.summary : '',
          hasSummary: !!(o && o.summary),
          statusLabel: chip.label, statusBg: chip.bg, statusFg: chip.fg,
          rankLabel: recommendable ? `Rank ${rank + 1} of ${ranking.length} valid` : 'Not ranked',
          recommendable, notRecommendable: !recommendable,
          gateNote: recommendable
            ? 'All five validity tests pass — eligible for recommendation.'
            : `Cannot be recommended — ${gate || 'no gate reported'} gate failed.`,
          selected: isSel,
          selectLabel: isSel ? 'Selected for the record of decision' : 'Record as recommendation',
          select: recommendable ? () => this.chooseStrategy(st.strategy_id) : () => {},
          selectDisabled: !recommendable,
          border: isSel ? 'var(--color-accent)' : 'var(--color-divider)',
          value: this.fmt(st.value),
          range: this.rangeText(st.adversary_range),
          robustness: this.fmt(st.robustness),
          riskFunctional: o ? `${o.risk_functional}${o.risk_alpha == null ? '' : ` (α ${this.fmt(o.risk_alpha, 2)})`}` : 'unavailable',
          aspiration: o ? this.fmt(o.aspiration) : 'unavailable',
          validity: this.VALIDITY_ORDER.map(name => {
            const v = (st.validity || []).find(x => x.test === name) || { passed: false, evidence: 'not reported' };
            return {
              test: this.cap(name),
              verdict: v.passed ? '✓ PASS' : '✕ FAIL',
              bg: v.passed ? 'rgb(19,57,41)' : 'rgb(174,25,85)',
              fg: v.passed ? 'rgb(76,195,138)' : 'rgb(254,236,244)',
              evidence: v.evidence,
            };
          }),
          assumptions: assumptionsFor(st.strategy_id).map(a => {
            const c = this.statusChip(a.status);
            return {
              id: a.assumption_id, k: a.index_k, statement: a.statement,
              statusLabel: c.label, bg: c.bg, fg: c.fg,
              detail: `p(holds) ${this.fmt(a.p_holds, 2)} · sensitivity ${this.fmt(a.sensitivity)} · EVPI ${this.fmt(a.evpi)}`,
            };
          }),
          panels: [
            this.panel('Objective weights and contributions', this.objectiveRows(st.strategy_id, o), why, !!(o || this.state.details[st.strategy_id])),
            this.panel('Resources — budget vs expected use', this.resourceRows(o), why, !!o),
            this.panel('Theory of victory', this.chainRows(o), why, !!o),
            this.panel('Constraints (must do)', this.textRows(o && o.constraints), why, !!o),
            this.panel('Restraints (cannot do)', this.textRows(o && o.restraints), why, !!o),
            this.panel('Mitigated harmful events', this.harmfulRows(o && o.mitigated_harmful_events), why, !!o),
            this.panel('Unmitigated harmful events', this.harmfulRows(o && o.unmitigated_harmful_events), why, !!o),
            this.panel('Opponent model', this.opponentRows(o), why, !!o),
          ],
        };
      }),

      // ══ Risk (step 3) ══════════════════════════════════════════════════
      assumptionRows: (snap ? snap.assumptions : []).filter(a => blue.some(b => b.strategy_id === a.strategy_id)).map(a => {
        const c = this.statusChip(a.status);
        return {
          id: a.assumption_id, k: a.index_k, statement: a.statement,
          strategy: (blue.find(x => x.strategy_id === a.strategy_id) || {}).name || a.strategy_id,
          statusLabel: c.label, bg: c.bg, fg: c.fg,
          pHolds: this.fmt(a.p_holds, 2), sens: this.fmt(a.sensitivity), evpi: this.fmt(a.evpi),
        };
      }),
      rankedCards: blue.slice().sort((a, b) => {
        const ra = ranking.indexOf(a.strategy_id), rb = ranking.indexOf(b.strategy_id);
        return (ra < 0 ? 99 : ra) - (rb < 0 ? 99 : rb);
      }).map(st => {
        const rank = ranking.indexOf(st.strategy_id);
        const chip = this.statusChip(st.status);
        const isSel = st.strategy_id === selectedId;
        return {
          id: st.strategy_id, name: st.name,
          rankLabel: rank >= 0 ? `Rank #${rank + 1}` : 'Not ranked',
          statusLabel: chip.label, bg: chip.bg, fg: chip.fg,
          value: this.fmt(st.value), range: this.rangeText(st.adversary_range),
          note: rank >= 0
            ? 'Valid — eligible for recommendation.'
            : `Cannot be recommended — ${this.gateFailed(st, this.optionFor(st.strategy_id)) || 'no gate reported'} gate failed.`,
          selected: isSel,
          selectLabel: isSel ? '✓ Selected' : 'Record as recommendation',
          select: rank >= 0 ? () => this.chooseStrategy(st.strategy_id) : () => {},
          selectDisabled: rank < 0,
          border: isSel ? 'var(--color-accent)' : 'var(--color-divider)',
          chooseBg: isSel ? 'color-mix(in srgb,var(--color-accent) 8%,transparent)' : 'transparent',
        };
      }),

      decisionNote: s.decisionNote, onDecisionNote: set('decisionNote'),
      approve: () => this.decide('Approved'), approveMod: () => this.decide('Approved with modifications'), returnRework: () => this.decide('Returned for rework'),
      hasDecision: !!s.decision, noDecision: !s.decision, decision: s.decision || {},
      isDocs: s.view === 'docs', prevent: e => e.preventDefault(),
      mapSrc: './assets/jipoe-map/index.html?threat=' + encodeURIComponent(T.name),
      ipoe: s.threat === 'OLV' ? { likely: 'OPA consolidates territorial gains in Sungzon and Khorathidin, shifts to deliberate defense-in-depth, and employs hybrid warfare — cyber attacks, information operations and limited precision fires — to attrit coalition will. Nuclear posturing continues as a strategic deterrent against MNFA operations inside Olvanan territory.', dangerous: 'OPA launches renewed offensive operations into southern Khorathidin to seize the Gulf of Khorathidin coast; conducts amphibious operations against key coalition staging ports; employs additional nuclear or WMD strikes to fracture coalition will; and conducts prolonged maritime interdiction of the South Olvanan Sea and Straits of Malacca approaches.', terrain: 'Bangkok political-logistical hub; Udon Thani CBRN hazard zone; Da Nang and Ho Chi Minh City; Gulf of Khorathidin coast; South Olvanan Sea and Straits of Malacca approaches (mine and submarine threat).' }
        : { likely: `${T.name} escalates gray-zone coercion into a limited seizure of a peripheral objective under cover of an exercise, seeking a fait accompli within 72 hours.`, dangerous: `${T.name} opens with pre-emptive long-range fires on regional bases and cyber attacks on logistics, then commits amphibious and airborne forces simultaneously.`, terrain: 'Maritime chokepoints, forward airfields within 500 nm of the objective, undersea cable landing sites.' },
      // ══ P3 · evidence, risk, collection, ingestion ══════════════════════
      // Each of these is a val builder above: a response body, formatted.
      overlay: this.overlayVals(),
      evidence: this.evidenceVals(),
      claimDetail: this.claimDetailVals(),
      sources: this.sourceVals(),
      riskView: this.riskVals(),
      collectionView: this.collectionVals(),
      routingQueue: this.routingQueueVals(),
      diffView: this.diffVals(),
      ingestView: this.ingestVals(),
      review: this.reviewVals(),
      draft: this.draftVals(),
      reqControls: this.requirementControlVals(),
      planningView: this.planningVals(),
      // Report intake, reusing the artifact's drop zones and file pickers.
      dropReport: e => this.readReport(this.filesFrom(e), 'plan'),
      pickReport: e => this.readReport(this.filesFrom(e), 'plan'),
      dropGuidance: e => this.readReport(this.filesFrom(e), 'guidance'),
      pickGuidance: e => this.readReport(this.filesFrom(e), 'guidance'),
      // The demo workspace: product-owned state, separate from the dataset.
      workspaceLabel: `Demo workspace “${window.API.workspace()}”`,
      resetWorkspace: () => this.resetWorkspace(),
      resetBusy: s.resetBusy,
      resetSupported: !!this.writePath('resetWorkspace'),
      resetDisabled: !this.writePath('resetWorkspace') || s.resetBusy,
      resetNote: this.writePath('resetWorkspace')
        ? 'Discards the demo workspace: ingested reports, review decisions and drafted requirements. The frozen dataset is never written to.'
        : 'POST /api/workspace/reset is not served by this backend yet.',
      hasResetNotice: !!s.resetNotice, resetNotice: s.resetNotice,
      hasResetError: !!s.resetError, resetError: s.resetError || {},
      postureStats: [{ label: 'Component commands', value: '5' }, { label: 'Designated for MNFA', value: '4 packages' }, { label: 'C-1 / C-2 ready', value: '82%' }, { label: 'Peak COA demand', value: 'Unavailable' }],
      forces: [
        { unit: 'Army BCT + division enablers (USAREUR-AF)', domain: 'Land', source: 'Assigned', loc: 'Grafenwöhr / Vilseck', c: 'C-1', avail: 'C-Day' },
        { unit: 'Fighter wing + enablers (USAFE-AFAFRICA)', domain: 'Air', source: 'Assigned', loc: 'Spangdahlem / Aviano', c: 'C-1', avail: 'C-Day' },
        { unit: 'Carrier Strike Group (NAVEUR-NAVAF)', domain: 'Maritime', source: 'Allocated', loc: 'Mediterranean', c: 'C-2', avail: 'C+5' },
        { unit: 'ARG / MEU (MARFOREUR)', domain: 'Maritime / Land', source: 'Allocated', loc: 'Rota', c: 'C-2', avail: 'C+7' },
        { unit: 'SOCEUR SOF task force', domain: 'SOF', source: 'Assigned', loc: 'Stuttgart', c: 'C-1', avail: 'C-Day' },
        { unit: 'CBRN consequence management units', domain: 'CBRN', source: 'Assigned', loc: 'Germany', c: 'C-2', avail: 'D-Day' },
        { unit: 'Air refueling / strategic airlift hubs', domain: 'Mobility', source: 'Assigned', loc: 'Ramstein / Lajes', c: 'C-1', avail: 'Now' },
        { unit: 'eFP battlegroups / Enhanced Air Policing', domain: 'Land / Air', source: 'Assigned', loc: 'Poland / Baltics', c: 'C-1', avail: 'Retained in AOR' },
        { unit: 'Strategic staging hubs (Ramstein, Rota, Sigonella, Lajes)', domain: 'Logistics', source: 'HNS', loc: 'DEU / ESP / ITA / PRT', c: 'C-1', avail: 'Now' }
      ],
      doctrine: [
        { ref: 'CJCSI 3100.01F · 29 Jan 2024', title: 'Joint Strategic Planning System', note: 'Directs three types of campaign plans (GCP, FCP, CCP), integrated contingency plan sets and Strategic Planning Frameworks; frames advice around risk to strategy, risk to force and readiness.', used: 'Plan type selector, CCMD selection, GFM inputs' },
        { ref: 'JP 5-0 · Joint Planning', title: 'Joint Planning Process', note: 'Mission analysis, COA development, COA analysis and wargaming, COA comparison and approval; screening for feasibility, acceptability, suitability, distinguishability and completeness.', used: 'Five-step lifecycle, COA screening tags' },
        { ref: 'CJCSM 3105.01 · JRAM', title: 'Joint Risk Analysis Methodology', note: 'Risk appraised on a four-level scale (Low, Moderate, Significant, High) against probability and consequence; risk-to-mission and risk-to-force as governing lenses.', used: 'Risk scale, decision matrix' },
        { ref: 'JP 2-01.3 · JIPOE', title: 'Intelligence Preparation of the Operational Environment', note: 'Defines the environment, evaluates the adversary, and determines adversary most likely and most dangerous courses of action.', used: 'JIPOE panel, red-cell reactions in the ARC table' },
        { ref: 'USEUCOM OPORD 26-002 · 25 MAR 2026', title: 'Operation ENDURING PHOENIX', note: 'EUCOM force contribution and support to MNFA under USINDOPACOM lead; two lines of effort (force contribution, theater deterrence and enablement) phased to Isolate / Secure / Dominate / Transition.', used: 'Strategy under adjudication, assumptions, constraints, force posture' },
        { ref: 'JP 2-0 · Joint Intelligence', title: 'Collection management', note: 'PIRs decomposed into indicators and specific information requirements, tasked to collection assets with latest time information is of value.', used: 'Collection Management, RFI routing' }
      ]
    };
  }
}
