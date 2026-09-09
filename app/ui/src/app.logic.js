class Component extends DCLogic {
  state = {
    view: 'coa', step: 1, runId: 'R-0417',
    planType: 'OPORD', level: 3, ccmd: 'EUCOM', threat: 'RUS',
    worldState: '', intent: '', endState: '',
    // Local drafts only. The evaluated assumptions come from /api/options.
    assumptions: [],
    scenario: 0,
    newAssumption: '',
    constraints: [
      { kind: 'C', text: '2CR in attack positions in Lithuania NLT C+4; 1AD advance parties at Poznań/Powidz NLT C+7; two ABCTs combat-ready NLT C+21' },
      { kind: 'C', text: 'Establish Forward Liaison Elements at JFC Brunssum, MNC-NE and CTF Baltic NLT C-Day' },
      { kind: 'C', text: 'C-UAS coverage at all APODs, SPODs and forward airfields NLT C+3; FPCON CHARLIE or higher at staging installations' },
      { kind: 'C', text: 'Retain combat power in Germany, Italy and the Balkans sufficient for other Alliance commitments; CSG remains in the North Atlantic / Norwegian Sea' },
      { kind: 'R', text: 'Strikes on Russian or Belarusian sovereign territory require SACEUR approval; Kaliningrad and beyond the Pskov/Leningrad support zone require NAC and national approval' },
      { kind: 'R', text: 'No fires against Russian strategic nuclear forces, NC3 or early-warning infrastructure without Presidential authorization' },
      { kind: 'R', text: 'No independent de-escalation channels with the Russian General Staff below Joint Staff / USEUCOM J3' },
      { kind: 'R', text: 'Minimize collateral damage in Russophone urban terrain (Narva, Daugavpils) to deny the Russian pretext narrative' }
    ],
    newConstraint: '', constraintKind: 'C',
    // Everything numeric on these screens is fetched from /api. `null` means
    // "not fetched yet"; it is never rendered as a value.
    opts: null, rank: null, dist: null, risks: null, collection: null,
    apiError: null, loading: true, rankBusy: false, distBusy: false,
    whatIfId: null, whatIf: null, whatIfBusy: false, tornado: null, tornadoBusy: false,
    sel: 0,
    weights: { mission: 4, personnel: 3, escalation: 4, time: 2, resources: 1 },
    chosen: null, decisionNote: '', decision: null,
    intel: [
      { title: 'Rail loading of 4th Guards Tank Division armor, Moscow MD, destination assessed Pskov axis', type: 'IMINT', rel: 'B – Usually reliable', pir: 1, when: '2 h ago' },
      { title: '152nd Guards Missile Brigade Iskander-M TELs dispersed from Chernyakhovsk garrison, Kaliningrad', type: 'GEOINT', rel: 'A – Reliable', pir: 4, when: '4 h ago' },
      { title: 'Kilo-class submarine and two Karakurt corvettes departed Baltiysk; AIS dark', type: 'SIGINT', rel: 'B – Usually reliable', pir: 5, when: '6 h ago' },
      { title: 'Minefield emplacement and mobile obstacle detachment activity east of Rēzekne', type: 'HUMINT', rel: 'C – Fairly reliable', pir: 3, when: '9 h ago' },
      { title: 'Regional Grouping of Forces staging observed in the Grodno area; no bridging assets yet', type: 'IMINT', rel: 'B – Usually reliable', pir: 2, when: '14 h ago' },
      { title: 'Anomalous vessel loitering over Estlink 2 cable route, Gulf of Finland', type: 'OSINT', rel: 'C – Fairly reliable', pir: 5, when: '1 d ago' }
    ],
    newIntelTitle: '', newIntelBody: '', newIntelType: 'SIGINT',
    // Local drafts only. Requirements come from /api/collection.
    pirs: [],
    newPir: '',
    rfis: [
      { id: 'RFI-041', q: 'APS-2 draw rate at Powidz and the Dülmen/Zutendaal/Eygelshoven sites; can two ABCTs close combat-ready NLT C+21?', to: '21st TSC / 405th AFSB', ties: 'Assumption A4', status: 'Open' },
      { id: 'RFI-042', q: 'MCM Q-route clearance timeline to Klaipėda and Riga; SNMCMG1 and Allied MCM force availability.', to: 'NAVEUR / CTF Baltic', ties: 'Assumption A5', status: 'Pending' },
      { id: 'RFI-043', q: 'Confirm EU military-mobility corridor clearances and HNS agreements for Germany, Poland, Denmark and Benelux for C-Day flow.', to: 'J4 / US Mission to NATO', ties: 'Assumption A2', status: 'Open' },
      { id: 'RFI-044', q: 'Belarusian mobilization indicators and Regional Grouping of Forces order of battle in the Grodno and Vitebsk regions.', to: 'J2 / NATO Intelligence Fusion Centre', ties: 'Assumption A7', status: 'Pending' },
      { id: 'RFI-045', q: 'FMN Spiral / US BICES-X terminal availability at MNC-NE, MND-N and MND-NE for V Corps liaison.', to: 'J6', ties: 'Assumption A8', status: 'Answered' }
    ],
    newRfi: '',
    planDocs: [],
    guideDocs: [
      { name: '2022 National Defense Strategy', tier: 'SecDef', directs: 'Integrated deterrence; Russia as acute threat; campaigning with Allies.', sig: { offensive: 2, defensive: 9, escalation: 2, restraint: 7, force: 2, partners: 14, sustain: 4, intel: 3 } },
      { name: '2022 National Military Strategy', tier: 'CJCS', directs: 'Risk to force and risk to strategy framing; joint force development.', sig: { offensive: 3, defensive: 8, escalation: 3, restraint: 5, force: 4, partners: 9, sustain: 5, intel: 4 } },
      { name: 'JSCP (CJCSI 3110.01)', tier: 'CJCS', directs: 'Campaign and contingency planning tasks; plan levels; integrated plan sets.', sig: { offensive: 3, defensive: 6, escalation: 2, restraint: 4, force: 3, partners: 7, sustain: 9, intel: 6 } },
      { name: 'NAC Decision Sheet, Article 5 Invocation (06 SEP 2026)', tier: 'North Atlantic Council', directs: 'Collective defense of Estonia and Latvia; political consensus and caveats.', sig: { offensive: 2, defensive: 9, escalation: 2, restraint: 9, force: 1, partners: 16, sustain: 2, intel: 1 } },
      { name: 'CJCS EXORD, Operation AMBER SHIELD (081900Z SEP 2026)', tier: 'CJCS', directs: 'US support to NATO collective defense; national authorities; funding and reporting.', sig: { offensive: 4, defensive: 8, escalation: 4, restraint: 6, force: 3, partners: 11, sustain: 8, intel: 5 } },
      { name: 'SACEUR OPLAN 2026-BAL and ACTORD (07 SEP 2026)', tier: 'SACEUR', directs: 'Four-phase deterrence and defense of the Baltic Region; TOA; ROE.', sig: { offensive: 6, defensive: 12, escalation: 5, restraint: 7, force: 6, partners: 15, sustain: 9, intel: 8 } },
      { name: 'ATP 7-100.1 Russian Tactics (2024)', tier: 'HQDA', directs: 'Reconnaissance-strike complex, Snow Dome, maneuver defense, escalation through nuclear threat.', sig: { offensive: 6, defensive: 7, escalation: 8, restraint: 2, force: 5, partners: 1, sustain: 3, intel: 12 } }
    ],
    planSel: 0, docBusy: '', inputTab: 'strategy', details: { arc: false, sens: false, pir: false, scenario: false }, feedUrl: '', feedOn: false, feedCount: 0
  };

  async loadDocs(files, kind) {
    const mod = await import(new URL('assets/docreader.js?v=' + Date.now(), document.baseURI).href);
    for (const f of files) {
      this.setState({ docBusy: `Reading ${f.name}…` });
      let doc;
      try { doc = await mod.readDocument(f); } catch (e) { doc = { name: f.name, kind: f.name.split('.').pop().toUpperCase(), text: '', words: 0, pages: 0 }; }
      const sig = mod.signalIndex(doc.text || '');
      if (kind === 'plan') {
        const ex = mod.extractPlan(doc.text || '');
        // When a field is missing, say why: no text at all, a heading that was never
        // found, or a heading found but no section that could be delimited.
        const miss = (label, probe) => !doc.text
          ? 'Not found — no text could be read from this file (a .pdf needs network access; use .docx or .txt)'
          : (new RegExp(probe, 'i').test(doc.text)
              ? `Not found — "${label}" appears in the text but no section under it could be delimited`
              : `Not found — no "${label}" heading in this document`);
        const entry = { ...doc, status: doc.text ? 'Parsed' : 'Could not read text — metadata only', mission: ex.mission || miss('Mission', 'mission'), intent: ex.intent || miss("Commander's Intent", 'intent'), endState: ex.endState || miss('End State', 'end ?state'), assumptions: ex.assumptions.length ? ex.assumptions : ['No explicit assumptions found'], pirs: ex.pirs || [], phases: ex.phases, sig };
        this.setState(s => ({ planDocs: [...s.planDocs, entry], planSel: s.planDocs.length }));
        this.applyPlan(entry, true);
      } else if (kind === 'guide') {
        this.setState(s => ({ guideDocs: [...s.guideDocs, { name: doc.name, tier: 'Uploaded', directs: (doc.text || '').slice(0, 90).replace(/\s+/g, ' ') || 'Text not readable', sig }] }));
      } else {
        this.setState(s => ({ intel: [{ title: doc.name, type: s.newIntelType, rel: 'F – Not yet evaluated', pir: 1 + (s.intel.length % 3), when: 'just now' }, ...s.intel], newIntelBody: (doc.text || '').slice(0, 600) }));
      }
    }
    this.setState({ docBusy: '' });
  }
  applyPlan(d, fresh) {
    if (!d) return; const s = this.state; const nf = v => v && !v.startsWith('Not found');
    const parsedA = d.assumptions.filter(a => !a.startsWith('No explicit')).map(a => ({ text: a.replace(/^(Assumption:|It is assumed)\s*/i, '').replace(/^[a-z0-9]\.\s*/i, ''), status: 1, conf: 50, link: d.name.slice(0, 18), valid: 'Per document' }));
    const parsedP = (d.pirs || []).map(q => ({ q, ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], reports: 0, ltiov: 'TBD', status: 0 }));
    this.setState({ view: 'coa', step: 1, inputTab: 'strategy', results: null,
      intent: nf(d.intent) ? d.intent : s.intent, endState: nf(d.endState) ? d.endState : s.endState,
      assumptions: parsedA.length ? (fresh ? parsedA : parsedA.concat(s.assumptions).slice(0, 10)) : s.assumptions,
      pirs: parsedP.length ? (fresh ? parsedP : parsedP.concat(s.pirs)) : s.pirs,
      worldState: nf(d.mission) ? `${d.mission} ${fresh ? '' : (s.worldState || '')}`.trim() : s.worldState });
  }
  filesFrom(e) { e.preventDefault(); return Array.from((e.dataTransfer && e.dataTransfer.files) || (e.target && e.target.files) || []); }
  planRisk(d) {
    const g = this.state.guideDocs; const avg = k => g.length ? g.reduce((a, x) => a + (x.sig[k] || 0), 0) / g.length : 0;
    const s = d.sig || {};
    const escV = (s.escalation || 0) * 0.6 + Math.max(0, (s.offensive || 0) - (s.restraint || 0)) * 0.3 - (s.restraint || 0) * 0.2 + Math.max(0, (s.escalation || 0) - avg('escalation'));
    const misV = Math.max(0, avg('partners') - (s.partners || 0)) * 0.5 + Math.max(0, avg('sustain') - (s.sustain || 0)) * 0.6 + Math.max(0, 6 - (s.intel || 0)) * 0.4 + (d.mission && d.mission.startsWith('Not found') ? 4 : 0);
    const perV = (s.force || 0) * 0.6 + (s.offensive || 0) * 0.3 - (s.defensive || 0) * 0.1;
    const lv = (v, th) => this.textBand(v, th); const col = l => this.riskColor(l);
    const rm = lv(misV, [2.5, 5, 8]), rp = lv(perV, [4, 7, 10]), re = lv(escV, [2.5, 5, 8]);
    const mk = (label, short, level, why) => ({ label, short, level, why, bg: col(level)[0], fg: col(level)[1] });
    const alignLevel = x => { const gap = Math.abs((s.restraint || 0) - x.sig.restraint) + Math.abs((s.partners || 0) - x.sig.partners) * 0.5 + Math.max(0, (s.escalation || 0) - x.sig.escalation) * 1.5; return gap < 5 ? 'Aligned' : gap < 10 ? 'Tension' : 'Conflict'; };
    const alignColor = { Aligned: col('Low'), Tension: col('Moderate'), Conflict: col('High') };
    const findings = [];
    if (re !== 'Low') findings.push(`Escalation language (${(s.escalation || 0).toFixed(1)} per 1k words) exceeds the guidance-set average (${avg('escalation').toFixed(1)}); restraint / off-ramp language is ${(s.restraint || 0) < avg('restraint') ? 'below' : 'at or above'} guidance.`);
    if ((s.partners || 0) < avg('partners')) findings.push('Allied and partner integration is thinner than the strategy directs; integrated deterrence depends on it.');
    if ((s.sustain || 0) < avg('sustain')) findings.push('Sustainment and deployment (TPFDD, munitions, resupply) are under-specified relative to JSCP planning tasks.');
    if ((s.intel || 0) < 6) findings.push('Few PIRs / indicators referenced; wargame uncertainty will be wide until collection is defined.');
    if (!findings.length) findings.push('No material divergence from the guidance set detected; residual risk is inherent to the operational problem.');
    return { rm, rp, re, risks: [mk('Document language · mission nesting', 'mission language', rm, 'Nesting with guidance, partner and sustainment coverage. A reading of this document\u2019s wording, not an evaluated risk level.'), mk('Document language · force exposure', 'force language', rp, 'Force exposure and offensive tempo in the text. A reading of this document\u2019s wording, not an evaluated risk level.'), mk('Document language · escalation', 'escalation language', re, 'Escalatory vs restraint language against guidance. A reading of this document\u2019s wording, not an evaluated risk level.')],
      alignment: g.map(x => { const l = alignLevel(x); return { doc: x.name.replace(/^\d{4}\s/, ''), level: l, note: x.directs, bg: alignColor[l][0], fg: alignColor[l][1] }; }), findings };
  }

  SCENARIOS = [
    { label: 'Consolidation and freeze (MLCOA)', desc: 'Maneuver defense behind mine, obstacle and EW belt in Narva and Latgale; hybrid pressure; nuclear signaling as NATO builds', ag: 0.35 },
    { label: 'Expanded incursion (MDCOA)', desc: '1st GTA reinforces via Pskov; converging attack closes Suwałki; Baltic Fleet mines and strikes SPODs; demonstrative nuclear detonation', ag: 0.8 },
    { label: 'Horizontal escalation', desc: 'Kalibr and Kh-101 strikes on Polish and German APODs/SPODs; sabotage of undersea cables and rail LOCs', ag: 0.6 }
  ];
  PLAN_TYPES = [
    { id: 'OPORD', label: 'Operation Order', abbr: 'OPORD', desc: 'Execution order directing force contribution and support to a lead command.' },
    { id: 'CCP', label: 'Combatant Command Campaign Plan', abbr: 'CCP', desc: 'Day-to-day campaigning that operationalizes strategic guidance.' },
    { id: 'CON', label: 'Contingency Plan', abbr: 'CONPLAN / OPLAN', desc: 'Branch of the campaign for a specific threat scenario; Level 1–4 detail.' },
    { id: 'GCP', label: 'Global Campaign Plan', abbr: 'GCP', desc: 'Trans-regional, all-domain challenge integrated across CCMDs.' },
    { id: 'FCP', label: 'Functional Campaign Plan', abbr: 'FCP', desc: 'Cross-cutting functional challenge, global in scope.' }
  ];
  LEVELS = ['Level 1 – Commander\'s estimate', 'Level 2 – Base plan', 'Level 3 – CONPLAN with annexes', 'Level 4 – OPLAN with TPFDD'];
  CCMDS = {
    'Joint Staff': 'Joint Staff (J-5); global integration, JSCP-directed planning and CJCS military advice.',
    PACOM: 'Indo-Pacific theater; maritime and air-centric problem set with distributed basing.',
    EUCOM: 'European theater; NATO-integrated land, air and maritime defense.',
    CENTCOM: 'Middle East and Central Asia; counter-proxy, maritime chokepoints, air and missile defense.',
    AFRICOM: 'Africa; partner-enabled, counter-VEO and access competition.',
    SOUTHCOM: 'Central and South America; partner capacity and counter-threat network.',
    NORTHCOM: 'Homeland defense and defense support of civil authorities.',
    SPACECOM: 'Space domain operations, protection of on-orbit assets.',
    CYBERCOM: 'Cyberspace operations in support of global campaigns.',
    SOCOM: 'Functional: special operations and counter-terrorism campaign planning.',
    TRANSCOM: 'Functional: global mobility and deployment/distribution.',
    STRATCOM: 'Functional: strategic deterrence, nuclear command and control, missile defense.'
  };
  THREATS = {
    RUS: { name: 'Russia', label: 'Russian Federation', desc: 'Armed Forces of the Russian Federation: limited incursion into Narva/Ida-Viru and eastern Latgale by 6th CAA and 76th GAAD (05 SEP 2026); 11th Army Corps and Belarus-based forces threaten Suwałki; Baltic Fleet mining and Kalibr threat; Iskander-M and Oreshnik nuclear signaling. Fights per ATP 7-100.1: reconnaissance-strike complex, Snow Dome, maneuver defense.' },
    PRC: { name: 'PRC', label: 'China (PRC)', desc: 'Pacing challenge; multi-domain A2/AD, maritime militia, gray-zone coercion.' },
    IRN: { name: 'Iran', label: 'Iran', desc: 'Proxy networks, missiles and UAS, maritime harassment.' },
    DPRK: { name: 'DPRK', label: 'North Korea', desc: 'Nuclear-armed artillery and missile threat to allies.' },
    VEO: { name: 'VEO', label: 'Violent extremist orgs', desc: 'Dispersed, partner-enabled counter-network problem.' }
  };
  // Moving to another stage must put the operator at the top of that screen. Without this
  // the page keeps the old scroll position, so a button at the foot of a long screen appears
  // to land on a later stage.
  toStep(patch, after) {
    this.setState(patch);
    if (typeof document !== 'undefined') {
      // The re-render lands after this call, and the app may scroll the window or an inner
      // container, so reset every candidate a few times across the next few frames.
      const toTop = () => {
        try {
          if (typeof window !== 'undefined' && window.scrollTo) window.scrollTo(0, 0);
          const root = document.scrollingElement || document.documentElement;
          if (root) root.scrollTop = 0;
          if (document.body) document.body.scrollTop = 0;
          let node = document.querySelector('#dc-root') || document.body;
          while (node) { if (node.scrollTop) node.scrollTop = 0; node = node.parentElement; }
        } catch (e) { /* scrolling is a convenience, never a failure */ }
      };
      toTop();
      [0, 60, 200].forEach(ms => setTimeout(toTop, ms));
    }
    if (after) setTimeout(after, 200);
  }

  componentDidMount() {
    const v = this.props.startView, st = +this.props.startStep;
    if (v || st) { if (['intel', 'docs', 'posture'].includes(v)) this.setState({ view: 'coa', step: 1, inputTab: v }); else this.setState({ view: v || 'coa', step: st || 1 }); }
    this.loadAll();
  }
  go(view) { if (['intel', 'docs', 'posture'].includes(view)) return this.toStep({ view: 'coa', step: 1, inputTab: view }); this.toStep({ view }); }
  FEED_POOL = [
    { title: '1st Guards Tank Army forward logistics build observed at Ostrov and Luga', type: 'IMINT', rel: 'B – Usually reliable', pir: 1 },
    { title: 'Karakurt corvettes loitering in Kalibr launch basket off Baltiysk', type: 'SIGINT', rel: 'B – Usually reliable', pir: 5 },
    { title: 'Iskander-M TEL movement from 26th Missile Brigade garrison, Luga', type: 'GEOINT', rel: 'A – Reliable', pir: 4 },
    { title: 'Russian state media themes on NATO logistics hubs in Poland as legitimate targets', type: 'OSINT', rel: 'C – Fairly reliable', pir: 5 },
    { title: 'Bridging equipment moved to the Grodno area; Belarusian reserve call-up notices', type: 'IMINT', rel: 'B – Usually reliable', pir: 2 },
    { title: 'Latvian National Guard: forward detachment probing toward Daugavpils crossings', type: 'HUMINT', rel: 'C – Fairly reliable', pir: 3 },
    { title: 'UAS overflight of Powidz APOD and Rail Baltica works near Kaunas', type: 'HUMINT', rel: 'B – Usually reliable', pir: 6 }
  ];
  toggleFeed() {
    if (this.state.feedOn) { clearInterval(this._feed); this.setState({ feedOn: false }); return; }
    this.setState({ feedOn: true, feedCount: 0 }); let i = 0;
    this._feed = setInterval(() => { const p = this.FEED_POOL[i % this.FEED_POOL.length]; i++; this.setState(s => ({ intel: [{ ...p, when: 'just now' }, ...s.intel], feedCount: s.feedCount + 1 })); if (i >= this.FEED_POOL.length) clearInterval(this._feed); }, 4000);
  }
  componentWillUnmount() { clearInterval(this._feed); }
  goStep(step) { this.setState({ view: 'coa', step }); }
  riskColor(l) { return { Low: ['rgb(19,57,41)', 'rgb(76,195,138)'], Moderate: ['rgb(63,34,0)', 'rgb(255,203,71)'], Significant: ['rgb(130,78,0)', 'rgb(254,243,221)'], High: ['rgb(174,25,85)', 'rgb(254,236,244)'] }[l]; }
  // Word-frequency banding for the *document* analysis on the Plans screen. It says
  // something about the text of an uploaded document and nothing about a strategy;
  // every evaluated risk level on every other screen comes from /api.
  textBand(v, th) { return v < th[0] ? 'Low' : v < th[1] ? 'Moderate' : v < th[2] ? 'Significant' : 'High'; }

  // ───────────────────────────────────────────────────────────────── the API
  // `api.js` is the only network client; `boot.js` loads it as a module and puts
  // it on `window` because dc-runtime evaluates this file as a classic script.
  api() { return window.WorkbenchApi; }

  // Any failure stops the screen and shows the backend's own code and message.
  // Nothing falls back to a computed-looking number.
  fail(e, where) {
    const err = { code: e && e.code ? e.code : 'ui_error', message: e && e.message ? e.message : String(e), status: e && e.status != null ? e.status : 0, path: (e && e.path) || where };
    err.line = `${err.code} (${err.status || 'no response'}) — ${err.message}`;
    this.setState({ apiError: err, loading: false, rankBusy: false, distBusy: false, whatIfBusy: false, tornadoBusy: false });
  }

  async loadAll() {
    this.setState({ loading: true, apiError: null });
    try {
      const A = this.api();
      const [pair, risks, collection] = await Promise.all([A.loadOptions(this.state.weights), A.risks(), A.collection()]);
      this.setState({ opts: pair.options, rank: pair.rank, risks, collection, loading: false });
    } catch (e) { this.fail(e, '/api/options'); }
  }

  // A weight slider is an operator input to /api/options/rank, not a local formula.
  // The answer is a round trip, so a stale one must never overwrite a newer one.
  setWeight(key, value) {
    const weights = { ...this.state.weights, [key]: value };
    const token = (this._rankToken = (this._rankToken || 0) + 1);
    this.setState({ weights, rankBusy: true, tornado: null });
    this.api().rank(weights).then(r => {
      if (token !== this._rankToken) return;
      this.setState({ rank: r, rankBusy: false });
    }).catch(e => { if (token === this._rankToken) this.fail(e, '/api/options/rank'); });
  }

  // "Run Wargame" is a real recompute: the enumerated outcome distribution for
  // every option. There is no progress to report, so none is invented.
  runWargame() {
    if (this.state.distBusy) return;
    this.setState({ distBusy: true, apiError: null });
    this.api().outcomeDistribution().then(d => this.setState({ dist: d, distBusy: false }))
      .catch(e => this.fail(e, '/api/options/outcome-distribution'));
  }

  pickAssumption(id) {
    if (this.state.whatIfId === id) { this.setState({ whatIfId: null, whatIf: null, whatIfBusy: false }); return; }
    const token = (this._whatIfToken = (this._whatIfToken || 0) + 1);
    this.setState({ whatIfId: id, whatIf: null, whatIfBusy: true });
    this.api().whatIf(id).then(w => { if (token === this._whatIfToken) this.setState({ whatIf: w, whatIfBusy: false }); })
      .catch(e => { if (token === this._whatIfToken) this.fail(e, '/api/options/what-if'); });
  }

  // The weight tornado asks "does the #1 change if this weight moves +/-2?". That is
  // ten more rankings, so it is fetched from /api/options/rank — ten real answers,
  // not a local re-score — and only when the operator opens the panel.
  loadTornado() {
    if (this.state.tornado || this.state.tornadoBusy || !this.state.rank) return;
    const A = this.api(), w = this.state.weights;
    this.setState({ tornadoBusy: true });
    const jobs = [];
    A.WEIGHT_KEYS.forEach(key => [-2, 2].forEach(d => {
      const alt = { ...w, [key]: Math.max(0, Math.min(5, w[key] + d)) };
      jobs.push(A.rank(alt).then(r => ({ key, d, top: (r.ranked && r.ranked[0]) || null })));
    }));
    Promise.all(jobs).then(rows => this.setState({ tornado: rows, tornadoBusy: false }))
      .catch(e => this.fail(e, '/api/options/rank'));
  }

  decide(status) {
    const rk = ((this.state.rank || {}).ranked) || [];
    const ch = rk.find(r => r.number === this.state.chosen) || rk[0]; if (!ch) return;
    const levels = (ch.criteria || []).map(c => `${c.label} ${c.level_label}`).join(' · ');
    this.setState({ decision: { status, n: ch.number, title: ch.title, risk: levels, time: new Date().toLocaleString(), note: this.state.decisionNote, hasNote: !!this.state.decisionNote } });
  }

  renderVals() {
    const s = this.state, T = this.THREATS[s.threat];
    const B = window.BRANDING || {};
    const on = ['var(--color-accent)', 'var(--color-accent)', '#fff'], off = ['var(--color-divider)', 'transparent', 'var(--color-text)'];
    const navItem = (id, label, view) => ({ label, go: () => this.go(view), opacity: 1, border: s.view === view ? 'rgb(30,41,59)' : 'transparent', dot: s.view === view ? 'var(--color-accent-700)' : 'transparent' });
    const docSel = s.planDocs[s.planSel]; const docTitle = docSel ? docSel.name.replace(/\.(docx|pdf|txt|md)$/i, '').replace(/\s+[—–-]\s+.*$/, '').trim() : '';
    const stage = s.view === 'coa' ? (s.step === 3 ? 3 : s.step === 5 ? 4 : (s.step === 1 && s.inputTab !== 'strategy') ? 5 : 1) : s.view === 'collection' ? 2 : 0;
    const tog = k => () => this.setState({ details: { ...s.details, [k]: !s.details[k] } });
    const set = k => e => this.setState({ [k]: e.target.value });

    // ────────────────────────────────────────────────── what the API returned
    const env = s.opts || {};
    const optionList = env.options || [];
    const rankEnv = s.rank || {};
    const rankedRows = rankEnv.ranked || [];
    const excluded = rankEnv.excluded || [];
    const stab = rankEnv.weight_stability || null;
    const risksEnv = s.risks || {};
    const requirements = (s.collection || {}).requirements || [];
    const rankOf = id => rankedRows.find(r => r.strategy_id === id) || null;
    const excludedOf = id => excluded.find(r => r.strategy_id === id) || null;
    const distOptions = (s.dist && s.dist.options) || [];
    const distOf = id => distOptions.find(o => o.strategy_id === id) || null;
    const hasOptions = optionList.length > 0 && !s.apiError;
    const planLabel = docTitle || env.scenario_name || 'No scenario loaded';

    // The one string the UI is allowed to print for a quantity this model does not
    // produce. It is never replaced by a plausible-looking number.
    const NA = 'Unavailable';
    const f3 = x => (x === null || x === undefined) ? NA : Number(x).toFixed(3);
    const f2 = x => (x === null || x === undefined) ? NA : Number(x).toFixed(2);
    const pctOf = x => (x === null || x === undefined) ? null : Math.round(x * 100);
    const pctStr = x => (x === null || x === undefined) ? NA : Math.round(x * 100) + '%';
    const LEVEL = { low: 'Low', moderate: 'Moderate', significant: 'Significant', high: 'High' };
    const lvColor = lv => this.riskColor(LEVEL[lv]) || ['rgb(30,41,59)', 'var(--color-neutral-700)'];
    const lvLabel = lv => LEVEL[lv] || (lv ? String(lv) : NA);

    // Assumption statuses are the evaluator's words, not a 0/1/2 the UI invented.
    const ASTAT = {
      holds: ['Holds', 'rgb(19,57,41)', 'rgb(76,195,138)'],
      stale: ['Stale', 'rgb(63,34,0)', 'rgb(255,203,71)'],
      violated: ['Violated', 'rgb(174,25,85)', 'rgb(254,236,244)'],
      unsupported: ['Unsupported', 'rgb(174,25,85)', 'rgb(254,236,244)'],
      unknown: ['Unknown', 'rgb(63,34,0)', 'rgb(255,203,71)']
    };
    const aStat = st => ASTAT[st] || [String(st || 'unknown'), 'rgb(30,41,59)', 'var(--color-neutral-700)'];
    const isWeakA = a => a.status !== 'holds' || (a.p_holds != null && a.p_holds < 0.7);

    // One row per distinct evaluated assumption, numbered in first-seen order, with
    // the options that depend on it.
    const byId = new Map();
    optionList.forEach(o => (o.assumptions || []).forEach(a => {
      const e = byId.get(a.assumption_id);
      if (!e) { byId.set(a.assumption_id, { ...a, n: byId.size + 1, options: [o.number] }); return; }
      e.options.push(o.number);
      if (Math.abs(a.sensitivity || 0) > Math.abs(e.sensitivity || 0)) { e.sensitivity = a.sensitivity; e.evpi = a.evpi; }
    }));
    const evaluated = Array.from(byId.values());
    const weakEval = evaluated.filter(isWeakA);

    // An uploaded plan keeps its own wording. Where a document sentence clearly
    // restates an evaluated assumption, the document's words are shown and every
    // number still comes from the API row.
    const docAssumptionTexts = ((docSel && docSel.assumptions) || []).filter(t => typeof t === 'string' && !t.startsWith('No explicit'));
    const wordSet = t => new Set(String(t || '').toLowerCase().match(/[a-zà-ÿ]{5,}/g) || []);
    const wordingFor = statement => {
      if (!docAssumptionTexts.length) return null;
      const target = wordSet(statement); if (!target.size) return null;
      let best = null, bestScore = 0;
      docAssumptionTexts.forEach(d => {
        const ws = wordSet(d); let hit = 0;
        target.forEach(w => { if (ws.has(w)) hit++; });
        const sc = hit / target.size;
        if (sc > bestScore) { bestScore = sc; best = d; }
      });
      return bestScore >= 0.4 ? best : null;
    };
    const textOf = a => wordingFor(a.statement) || a.statement;

    const critKeys = ['mission', 'personnel', 'escalation', 'time', 'resources'];
    const critOf = (o, k) => (o.criteria || []).find(c => c.key === k) || null;
    const critLabel = k => {
      for (const o of optionList) { const c = critOf(o, k); if (c) return c.label; }
      return k;
    };

    // ───────────────────────────────────────────── step 2 · the option cards
    const coas = optionList.map(o => ({
      n: o.number, title: o.title, approach: o.approach, concept: o.concept, tasks: o.tasks || [],
      // Days to end state, force demand as a percentage of allocation, and a count
      // of decision points are not quantities this model produces.
      days: NA, res: NA, dps: NA,
      valueLine: `Expected value ${f3(o.expected_value)} · aspiration w·τ ${f3(o.aspiration)} · robustness ${f3(o.robustness)}`,
      rangeLine: `Adversary-scenario range ${f3(o.adversary_range && o.adversary_range.min)} – ${f3(o.adversary_range && o.adversary_range.max)}`,
      screen: (o.validity || []).map(v => ({
        label: v.test.charAt(0).toUpperCase() + v.test.slice(1),
        evidence: v.evidence,
        bg: v.passed ? 'rgb(19,57,41)' : 'rgb(174,25,85)',
        fg: v.passed ? 'rgb(76,195,138)' : 'rgb(254,236,244)'
      })),
      invalid: o.status !== 'valid',
      gateLine: o.status !== 'valid'
        ? `Invalid — failed the JP 5-0 ${(o.gates_failed && o.gates_failed.length ? o.gates_failed : [o.gate_failed]).filter(Boolean).join(' and ')} test. It stays on screen and cannot be recommended.`
        : ''
    }));

    // ─────────────────────── step 3 · the enumerated outcome distribution cards
    const results = optionList.map(o => {
      const d = distOf(o.strategy_id);
      const bins = (d && d.bins) || [];
      const maxMass = bins.reduce((m, b) => Math.max(m, b.mass || 0), 0) || 1;
      const asp = d ? d.aspiration : null;
      return {
        n: o.number, title: o.title,
        select: () => this.setState({ sel: o.number - 1 }),
        outline: s.sel === o.number - 1 ? '2px solid var(--color-accent)' : 'none',
        worlds: d ? `${d.assumption_worlds} assumption worlds × ${d.adversary_coas} adversary COAs` : NA,
        bins: bins.map(b => ({
          h: Math.max(2, Math.round((b.mass || 0) / maxMass * 100)),
          bg: (asp != null && b.lower >= asp) ? 'var(--color-accent-700)' : 'var(--color-accent-300)',
          tip: `${f2(b.lower)}–${f2(b.upper)}: probability mass ${f3(b.mass)}`
        })),
        aspirationPct: d ? pctStr(d.p_meets_aspiration) : NA,
        meanLine: d ? `mean ${f3(d.mean_outcome)} · sd ${f3(d.std_dev)}` : NA,
        casualties: NA,
        range: `${f3(o.adversary_range && o.adversary_range.min)} – ${f3(o.adversary_range && o.adversary_range.max)}`,
        risks: (o.criteria || []).map(c => ({ label: c.label, level: c.level_label, bg: lvColor(c.level)[0], fg: lvColor(c.level)[1] })),
        assumptions: (o.assumptions || []).map(a => {
          const st = aStat(a.status);
          return { n: (byId.get(a.assumption_id) || {}).n, text: textOf(a), tag: st[0], fg: st[2],
            stats: `p(holds) ${f3(a.p_holds)} · sensitivity ${f3(a.sensitivity)} · EVPI ${f3(a.evpi)}` };
        })
      };
    });

    // ────────────────────────────────── step 4 · the criterion comparison table
    const matrix = critKeys.map(k => ({
      label: critLabel(k),
      weight: s.weights[k],
      setWeight: e => this.setWeight(k, +e.target.value),
      cells: optionList.map(o => {
        const c = critOf(o, k);
        if (!c) return { level: NA, detail: 'the model does not measure this criterion for this option', bg: 'rgb(30,41,59)', fg: 'var(--color-neutral-700)' };
        return { level: c.level_label, detail: `E[u] ${f3(c.expected_value)} · shortfall ${f3(c.shortfall)} · ${c.score} × w${c.weight} = ${c.contribution}`, bg: lvColor(c.level)[0], fg: lvColor(c.level)[1] };
      })
    }));

    // One cell per option column, in the same order as the header row: a valid
    // option shows its weighted total and rank; an invalid one names its gate.
    const scoreRow = optionList.map(o => {
      const r = rankOf(o.strategy_id), x = excludedOf(o.strategy_id);
      if (r) return { pct: r.weighted_pct + '%', note: `Rank #${r.rank} · ${r.weighted_total} / ${rankEnv.weighted_max}` };
      return { pct: 'Not ranked', note: x ? `failed the JP 5-0 ${x.gate_failed} test` : 'not in the ranking' };
    });

    const bestRow = rankedRows[0] || null;
    const runnerRow = rankedRows[1] || null;
    const chosenNumber = s.chosen != null ? s.chosen : (bestRow ? bestRow.number : null);
    const ranked = rankedRows.map(r => ({
      n: r.number, rank: r.rank, title: r.title, pct: r.weighted_pct,
      score: `${r.weighted_total} / ${rankEnv.weighted_max}`,
      riskLine: (r.criteria || []).map(c => `${c.label} ${c.level_label}`).join(' · '),
      choose: () => this.setState({ chosen: r.number }),
      chooseBg: chosenNumber === r.number ? 'color-mix(in srgb,var(--color-accent) 8%,transparent)' : 'transparent',
      chooseBorder: chosenNumber === r.number ? 'var(--color-accent)' : 'var(--color-divider)'
    }));
    const chosenR = ranked.find(r => r.n === chosenNumber) || ranked[0] || {};

    const explain = bestRow ? critKeys.map(k => {
      const b = (bestRow.criteria || []).find(c => c.key === k) || {};
      const r = runnerRow ? ((runnerRow.criteria || []).find(c => c.key === k) || {}) : {};
      const mx = Math.max(1, (b.weight || 0) * 4);
      const d = (b.contribution || 0) - (r.contribution || 0);
      return { label: b.label || critLabel(k), bestW: Math.round((b.contribution || 0) / mx * 50), otherW: Math.round((r.contribution || 0) / mx * 50), delta: (d > 0 ? '+' : '') + d, color: d > 0 ? 'rgb(76,195,138)' : d < 0 ? 'rgb(255,120,120)' : 'var(--color-neutral-600)' };
    }) : [];
    const gains = explain.filter(x => x.delta.startsWith('+')).map(x => x.label.toLowerCase());
    const losses = explain.filter(x => x.delta.startsWith('-')).map(x => x.label.toLowerCase());
    const explainText = bestRow && runnerRow
      ? `Strategy ${bestRow.number} leads Strategy ${runnerRow.number} by ${bestRow.weighted_total - runnerRow.weighted_total} weighted points (${bestRow.weighted_total} vs ${runnerRow.weighted_total} of ${rankEnv.weighted_max}). The margin comes from ${gains.length ? gains.join(', ') : 'no single criterion'}${losses.length ? '; it gives ground on ' + losses.join(', ') : ''}. Each bar is the criterion contribution the backend computed: JRAM score × weight.`
      : (bestRow ? `Strategy ${bestRow.number} is the only ranked option under this weighting.` : '');

    const stabPct = stab ? Math.round(stab.fraction_top * 100) : null;
    const stability = stab ? (stab.per_option || []).map(x => ({ n: x.number, pct: Math.round(x.fraction_top * 100), bg: x.strategy_id === stab.top_option_id ? 'var(--color-accent)' : 'rgb(100,116,139)' })) : [];
    const stabilityText = stab
      ? `Strategy ${(stab.per_option[0] || {}).number} ranks first in ${stabPct}% of the ${stab.weightings_evaluated} weightings the backend enumerated. ${stab.method}`
      : '';
    const stabilityLabel = stab ? `Rank stability · ${stab.weightings_evaluated} weightings enumerated by /api/options/rank` : 'Rank stability';

    const tornadoTop = row => (row && row.top) ? row.top.number : null;
    const tornado = critKeys.map(k => {
      const lo = (s.tornado || []).find(x => x.key === k && x.d === -2);
      const hi = (s.tornado || []).find(x => x.key === k && x.d === 2);
      const flip = n => (bestRow && n === bestRow.number) ? ['rgb(19,57,41)', 'rgb(76,195,138)'] : ['rgb(174,25,85)', 'rgb(254,236,244)'];
      const loN = tornadoTop(lo), hiN = tornadoTop(hi);
      return { label: critLabel(k), lo: loN == null ? '…' : loN, hi: hiN == null ? '…' : hiN,
        loBg: loN == null ? 'rgb(30,41,59)' : flip(loN)[0], loFg: loN == null ? 'var(--color-neutral-700)' : flip(loN)[1],
        hiBg: hiN == null ? 'rgb(30,41,59)' : flip(hiN)[0], hiFg: hiN == null ? 'var(--color-neutral-700)' : flip(hiN)[1] };
    });

    // The adversary axis this model actually has: min / expected / max across the
    // adversary COAs in the opponent model. Never a confidence interval.
    const sweep = optionList.map(o => ({ n: o.number, lo: f3(o.adversary_range && o.adversary_range.min), mid: f3(o.expected_value), hi: f3(o.adversary_range && o.adversary_range.max) }));
    const sweepText = optionList.length ? ((optionList[0].adversary_range || {}).basis || '') : '';

    const assumptionRisk = evaluated.slice().sort((a, b) => (a.p_holds || 0) - (b.p_holds || 0)).map(a => {
      const st = aStat(a.status);
      return { n: a.n, text: textOf(a), conf: pctOf(a.p_holds), status: st[0], bg: st[1], fg: st[2] };
    });
    const topSens = evaluated.slice().sort((a, b) => Math.abs(b.sensitivity || 0) - Math.abs(a.sensitivity || 0))[0] || null;
    const assumptionText = evaluated.length
      ? `${weakEval.length} of ${evaluated.length} evaluated assumptions are stale, violated or below p(holds) 0.70. The largest single sensitivity is A${topSens ? topSens.n : '-'} at ${f3(topSens && topSens.sensitivity)}, with EVPI ${f3(topSens && topSens.evpi)}; sensitivity and EVPI are the backend's, computed over the enumerated assumption worlds.`
      : '';

    // ───────────────────────────── step 3 · what-if, from /api/options/what-if
    const wi = s.whatIf;
    const wiAssumption = wi ? wi.assumption : null;
    const propagation = wi ? (wi.options || []).map(o => {
      const d = o.delta_conditioned;
      const shift = o.status_changed
        ? `${o.status_before} → ${o.status_after_withdrawn}${(o.gates_failed_after_withdrawn || []).length ? ' · fails ' + o.gates_failed_after_withdrawn.join(', ') : ''}`
        : 'Status unchanged';
      return { n: o.number, title: o.title, delta: `${d > 0 ? '+' : ''}${f3(d)} value`, before: f3(o.value_before), after: f3(o.value_after_conditioned),
        color: d <= -0.02 ? 'rgb(255,120,120)' : d < 0 ? 'rgb(255,203,71)' : 'var(--color-neutral-600)', riskShift: shift };
    }) : [];
    const problemSets = wi ? (wi.problem_sets_moved || []).map(m => ({
      label: `${m.name} · ${m.jsps_horizon}-term`, hop: `${lvLabel(m.level_before)} → ${lvLabel(m.level_after)}`,
      w: 60, bg: lvColor(m.level_after)[1]
    })) : [];
    const harmfulMoved = wi ? (wi.harmful_events_moved || []).map(m => ({
      label: m.statement, horizon: `${m.jsps_horizon}-term`,
      move: `${lvLabel(m.level_before)} → ${lvLabel(m.level_after)}`, p: `p ${f2(m.p_before)} → ${f2(m.p_after)}`
    })) : [];
    const statusChanges = wi ? (wi.status_changes || []).map(c => `${c.strategy_id}: ${c.from} → ${c.to}${(c.gates_failed_after || []).length ? ' (fails ' + c.gates_failed_after.join(', ') + ')' : ''}`) : [];
    const propagationText = wi
      ? `Ranking before ${(wi.ranking_before || []).join(' > ') || '—'}; conditioned on the assumption failing ${(wi.ranking_after_conditioned || []).join(' > ') || '—'}; with its evidence withdrawn ${(wi.ranking_after_withdrawn || []).join(' > ') || '—'}. ${(wi.harmful_events_moved || []).length} harmful event rows and ${(wi.problem_sets_moved || []).length} problem-set rows move.`
      : '';

    // ─────────────────────────────────────── stage 3 · the risk graph (/api/risks)
    const nearest = rows => (rows || []).find(x => x.jsps_horizon === 'near') || (rows || [])[0] || null;
    const driverText = d => (d && (d.driver_id || d.id || d.name || d.statement)) || String(d);
    const riskProblemSets = (risksEnv.problem_sets || []).map(ps => {
      const h = nearest(ps.horizons);
      return { label: ps.name, level: h ? lvLabel(h.max_risk_level) : NA, horizon: h ? `${h.jsps_horizon}-term` : NA,
        bg: h ? lvColor(h.max_risk_level)[0] : 'rgb(30,41,59)', fg: h ? lvColor(h.max_risk_level)[1] : 'var(--color-neutral-700)',
        owner: ps.risk_owner_role || NA, tolerance: ps.tolerance_statement || NA,
        value: (ps.thing_of_value_names || []).join(', ') || NA };
    });
    const riskEvents = (risksEnv.harmful_events || []).map(he => {
      const h = nearest(he.horizons);
      const drivers = (h && h.active_drivers) || [];
      return { statement: he.statement, set: he.problem_set_name, type: he.risk_type,
        level: h ? lvLabel(h.risk_level) : NA, bg: h ? lvColor(h.risk_level)[0] : 'rgb(30,41,59)', fg: h ? lvColor(h.risk_level)[1] : 'var(--color-neutral-700)',
        p: h ? `${h.p_level} · p ${f2(h.p_raw)}` : NA, consequence: h ? h.c_level : NA, trend: h ? h.trend : NA,
        drivers: drivers.length ? drivers.map(driverText).join(', ') : 'no driver active at this horizon' };
    });
    const cascade = (risksEnv.escalation_edges || []).map(e => ({ from: e.from_statement, to: e.to_statement, lift: `lift ${f2(e.lift)}`, mechanism: e.mechanism || NA }));

    // ────────────────────────────── stage 2 · collection (/api/collection + drafts)
    const REQ_STATUS = {
      research: ['Research', 'rgb(130,78,0)', 'rgb(254,243,221)'],
      validation: ['Validation', 'rgb(63,34,0)', 'rgb(255,203,71)'],
      submission: ['Submission', 'rgb(16,42,76)', 'rgb(147,197,253)'],
      satisfaction: ['Satisfied', 'rgb(35,110,74)', 'rgb(229,251,235)'],
      closed: ['Closed', 'rgb(35,110,74)', 'rgb(229,251,235)']
    };
    const reqStat = st => REQ_STATUS[st] || [String(st || 'unknown'), 'rgb(30,41,59)', 'var(--color-neutral-700)'];
    const basisText = b => {
      if (!b) return 'priority basis not supplied';
      if (b.basis === 'evpi') return `priority basis: EVPI ${f3(b.evpi)} on ${b.assumption_id}`;
      return `priority basis: ${b.basis} — claim ${b.claim_id || '—'}, confidence ${f2(b.confidence)}, degree ${b.degree}`;
    };
    const apiPirs = requirements.map(r => {
      const st = reqStat(r.status);
      const linked = r.assumption ? byId.get(r.assumption.assumption_id) : null;
      return {
        n: r.jipcl_rank, q: r.pir_statement || r.sir || r.req_id,
        ind: r.indicators || [], assets: (r.candidate_assets || []).map(a => (a && (a.name || a.asset_id)) || String(a)),
        status: st[0], bg: st[1], fg: st[2],
        meta: `${r.req_id} · gap ${r.gap_type} · LTIOV ${r.ltiov || 'not set'} · routed to ${r.routing || 'unrouted'} · ${basisText(r.priority_basis)}`,
        tied: linked ? ` · validates A${linked.n}` : '',
        isLocal: false, cycleLabel: '', cycle: () => {}, remove: () => {}
      };
    });
    const draftPirs = s.pirs.map((p, i) => ({
      n: `D${i + 1}`, q: p.q, ind: p.ind || [], assets: p.assets || [],
      status: ['Gap', 'Collecting', 'Answered'][p.status] || 'Gap',
      bg: [['rgb(174,25,85)'], ['rgb(130,78,0)'], ['rgb(35,110,74)']][p.status || 0][0],
      fg: ['rgb(254,236,244)', 'rgb(254,243,221)', 'rgb(229,251,235)'][p.status || 0],
      meta: `Local draft — not submitted to the backend · LTIOV ${p.ltiov || 'TBD'}`,
      tied: p.assumption ? ` · drafted against ${p.assumption}` : '',
      isLocal: true, cycleLabel: p.status === 2 ? 'Reset' : p.status === 1 ? 'Collection returned' : 'Task assets',
      cycle: () => this.setState({ pirs: s.pirs.map((x, j) => j === i ? { ...x, status: ((x.status || 0) + 1) % 3 } : x) }),
      remove: () => this.setState({ pirs: s.pirs.filter((_, j) => j !== i) })
    }));
    const pirs = apiPirs.concat(draftPirs);
    const openReqs = requirements.filter(r => !['satisfaction', 'closed'].includes(r.status)).length;
    const pirSummary = requirements.length
      ? `${requirements.length} requirements from /api/collection · ${openReqs} open · ${draftPirs.length} local draft${draftPirs.length === 1 ? '' : 's'}`
      : (s.apiError ? 'Requirements unavailable — the API did not answer' : 'Loading requirements…');

    const requirementFor = a => requirements.find(r => r.assumption && r.assumption.assumption_id === a.assumption_id) || null;
    const draftFor = a => s.pirs.findIndex(p => p.assumption === a.assumption_id);
    const draftOne = a => this.setState({ pirs: [...this.state.pirs, { q: 'Validate: ' + textOf(a), ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], ltiov: 'TBD', status: 0, assumption: a.assumption_id }] });
    const weakList = weakEval.map(a => {
      const st = aStat(a.status);
      const req = requirementFor(a); const di = draftFor(a);
      return {
        n: a.n, text: textOf(a),
        link: `${a.subject_name || a.subject_id || 'unlinked'} · ${a.predicate || '—'}`,
        valid: `sensitivity ${f3(a.sensitivity)} · EVPI ${f3(a.evpi)}`,
        conf: pctOf(a.p_holds), status: st[0], bg: st[1], fg: st[2],
        bearing: a.options.map(n => 'Strategy ' + n).join(', ') || 'no option',
        hasCr: !!req || di >= 0, noCr: !req && di < 0,
        crLabel: req ? `${req.req_id} · ${reqStat(req.status)[0]}` : (di >= 0 ? `Local draft D${di + 1}` : ''),
        draft: () => draftOne(a)
      };
    });

    // ─────────────────────────────────── step 1 · the assumption tracker
    const trackerApi = evaluated.map(a => {
      const st = aStat(a.status); const doc = wordingFor(a.statement);
      return { n: a.n, text: doc || a.statement, conf: pctOf(a.p_holds), status: st[0], bg: st[1], fg: st[2],
        link: doc ? `Wording from ${docSel.name}; evaluated as ${a.assumption_id}` : `${a.assumption_id} · ${a.subject_name || a.subject_id || 'unlinked'} · ${a.predicate || '—'}`,
        stats: `p(holds) ${f3(a.p_holds)} · sensitivity ${f3(a.sensitivity)} · EVPI ${f3(a.evpi)} · load-bearing for ${a.options.map(n => 'Strategy ' + n).join(', ')}`,
        isLocal: false, remove: () => {} };
    });
    const trackerLocal = s.assumptions.map((a, i) => ({
      n: evaluated.length + i + 1, text: a.text, conf: null, status: 'Local draft', bg: 'rgb(30,41,59)', fg: 'var(--color-neutral-700)',
      link: a.link ? 'Local draft · ' + a.link : 'Local draft',
      stats: 'Local draft — typed into this session and not evaluated by the model.',
      isLocal: true, remove: () => this.setState({ assumptions: s.assumptions.filter((_, j) => j !== i) })
    }));
    const trackerRows = trackerApi.concat(trackerLocal);
    const assumptionSummary = evaluated.length
      ? `${evaluated.filter(a => a.status === 'holds').length} hold · ${evaluated.filter(a => a.status !== 'holds').length} not holding · ${weakEval.length} below p(holds) 0.70 or not holding · ${trackerLocal.length} local draft${trackerLocal.length === 1 ? '' : 's'}`
      : (s.apiError ? 'Assumptions unavailable — the API did not answer' : 'Loading assumptions…');

    // ───────────────────────────────── step 4 · where the analysis stands
    const evidence = optionList.map(o => {
      const r = rankOf(o.strategy_id), x = excludedOf(o.strategy_id);
      const deps = (o.assumptions || []).map(a => {
        const st = aStat(a.status); const u = byId.get(a.assumption_id) || {};
        return { n: u.n, short: textOf(a).slice(0, 78), conf: pctStr(a.p_holds), status: st[0], bg: st[1], fg: st[2] };
      });
      const weak = (o.assumptions || []).filter(isWeakA);
      return {
        n: o.number, title: o.title, deps,
        rank: r ? `Rank #${r.rank}` : 'Not ranked',
        border: r && r.rank === 1 ? 'var(--color-accent)' : 'var(--color-divider)',
        verdict: x
          ? `Invalid — failed the JP 5-0 ${x.gate_failed} test. ${x.reason}`
          : (weak.length ? `Stands on thin evidence: ${weak.map(a => 'A' + (byId.get(a.assumption_id) || {}).n).join(', ')} ${weak.length === 1 ? 'is' : 'are'} stale, violated or below p(holds) 0.70.` : 'Every load-bearing assumption holds at p ≥ 0.70.'),
        verdictColor: x ? 'rgb(255,120,120)' : (weak.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)')
      };
    });

    const bestOption = bestRow ? optionList.find(o => o.strategy_id === bestRow.strategy_id) : null;
    const worstCrit = bestRow ? (bestRow.criteria || []).slice().sort((a, b) => a.score - b.score)[0] : null;
    const best = bestRow ? {
      n: bestRow.number, title: bestRow.title,
      reason: `Highest weighted total among the valid options: ${bestRow.weighted_total} of ${rankEnv.weighted_max} (${bestRow.weighted_pct}%) under weights ${critKeys.map(k => k + ' ' + s.weights[k]).join(', ')}. Expected value ${f3(bestRow.expected_value)} against an aspiration of ${f3(bestOption && bestOption.aspiration)}. ${excluded.length} option${excluded.length === 1 ? '' : 's'} could not be ranked because ${excluded.length === 1 ? 'it' : 'they'} failed a JP 5-0 validity test.`,
      riskAccepted: worstCrit ? `${worstCrit.level_label} on "${worstCrit.label}" is the governing criterion: E[u] ${f3(worstCrit.expected_value)}, shortfall ${f3(worstCrit.shortfall)}. ${env.level_basis || ''}` : ''
    } : { n: '', title: '', reason: '', riskAccepted: '' };

    const tradeoffs = hasOptions ? (() => {
      const byValue = optionList.slice().sort((a, b) => b.expected_value - a.expected_value)[0];
      const widest = optionList.slice().sort((a, b) => ((b.adversary_range || {}).max - (b.adversary_range || {}).min) - ((a.adversary_range || {}).max - (a.adversary_range || {}).min))[0];
      const robust = optionList.slice().sort((a, b) => b.robustness - a.robustness)[0];
      return [
        `Highest expected value: Strategy ${byValue.number} at ${f3(byValue.expected_value)} against an aspiration of ${f3(byValue.aspiration)}.`,
        `Widest adversary-scenario range: Strategy ${widest.number} at ${f3((widest.adversary_range || {}).min)} – ${f3((widest.adversary_range || {}).max)}. That is the spread of expected value across the adversary COAs in the opponent model.`,
        `Most robust to the adversary's choice: Strategy ${robust.number} at ${f3(robust.robustness)}.`,
        excluded.length ? `${excluded.map(x => 'Strategy ' + x.number).join(', ')} cannot be recommended: ${excluded.map(x => x.gate_failed).join(', ')} test failed.` : 'Every option passed all five JP 5-0 validity tests.'
      ];
    })() : [];

    // ───────────────────────────────────────────────── step 5 · recommendation
    const evalGrade = stab
      ? { label: `${stabPct}% of ${stab.weightings_evaluated} weightings`, bg: stabPct >= 75 ? 'rgb(19,57,41)' : 'rgb(63,34,0)', fg: stabPct >= 75 ? 'rgb(76,195,138)' : 'rgb(255,203,71)' }
      : { label: NA, bg: 'rgb(30,41,59)', fg: 'var(--color-neutral-700)' };
    const evalSummary = bestRow
      ? `Strategy ${bestRow.number} ranks first at ${bestRow.weighted_pct}% of the weighted maximum (${bestRow.weighted_total} / ${rankEnv.weighted_max})${runnerRow ? `, ahead of Strategy ${runnerRow.number} (${runnerRow.weighted_pct}%)` : ''}. It holds the top rank in ${stabPct}% of the ${stab ? stab.weightings_evaluated : '—'} weightings the backend enumerated. It rests on ${(bestOption && bestOption.assumptions || []).length} evaluated assumptions, ${(bestOption && bestOption.assumptions || []).filter(isWeakA).length} of which are stale, violated or below p(holds) 0.70. ${openReqs} collection requirement${openReqs === 1 ? '' : 's'} are open. ${env.caution || ''}`
      : '';
    const evalStats = bestRow ? [
      { label: 'Weighted score', value: `${bestRow.weighted_pct}%`, note: `Rank #1 of ${rankedRows.length} valid options`, color: 'var(--color-text)' },
      { label: 'Rank stability', value: stabPct == null ? NA : `${stabPct}%`, note: stab ? `of ${stab.weightings_evaluated} weightings enumerated` : '', color: stabPct >= 75 ? 'rgb(76,195,138)' : 'rgb(255,203,71)' },
      { label: 'Thin evidence', value: `${(bestOption && bestOption.assumptions || []).filter(isWeakA).length} / ${(bestOption && bestOption.assumptions || []).length}`, note: 'load-bearing assumptions not holding at p ≥ 0.70', color: 'rgb(255,203,71)' },
      { label: 'Open collection', value: String(openReqs), note: `of ${requirements.length} requirements in the JIPCL`, color: openReqs ? 'rgb(255,203,71)' : 'rgb(76,195,138)' },
      { label: 'Highest sensitivity', value: f3(topSens && topSens.sensitivity), note: topSens ? `A${topSens.n} · EVPI ${f3(topSens.evpi)}` : NA, color: 'rgb(255,203,71)' }
    ] : [];
    const evalGaps = bestOption
      ? ((bestOption.assumptions || []).filter(isWeakA).map(a => {
          const u = byId.get(a.assumption_id) || {}; const req = requirementFor(a);
          return `A${u.n} · ${aStat(a.status)[0].toLowerCase()}, p(holds) ${f3(a.p_holds)}, EVPI ${f3(a.evpi)}: ${textOf(a).slice(0, 140)}. Collection: ${req ? `${req.req_id} (${req.status})` : 'no requirement raised'}.`;
        }).concat((bestOption.assumptions || []).filter(isWeakA).length ? [] : ['Every load-bearing assumption on this option holds at p ≥ 0.70.']))
      : [];
    const evalRisks = bestRow ? (bestRow.criteria || []).map(c =>
      `${c.label} (${c.level_label}): E[u] ${f3(c.expected_value)}, shortfall ${f3(c.shortfall)}, scoring ${c.score} at weight ${c.weight}.`
    ).concat(excluded.map(x => `Strategy ${x.number} is invalid and outside the ranking: ${x.reason}`)) : [];
    const evalConditions = bestRow ? [
      topSens ? `Validate A${topSens.n} first: it carries the largest sensitivity (${f3(topSens.sensitivity)}) and an EVPI of ${f3(topSens.evpi)}.` : 'No assumption carries a material sensitivity.',
      openReqs ? `Close ${openReqs} open collection requirement${openReqs === 1 ? '' : 's'}; /api/collection ranks them by the JIPCL rule.` : 'No collection requirement is open.',
      env.caution || '',
      env.level_basis ? `Risk levels: ${env.level_basis}` : ''
    ].filter(Boolean) : [];

    const failToggles = evaluated.map(a => ({
      label: `A${a.n} fails`, pick: () => this.pickAssumption(a.assumption_id),
      border: s.whatIfId === a.assumption_id ? 'rgb(255,120,120)' : 'var(--color-divider)',
      bg: s.whatIfId === a.assumption_id ? 'rgb(60,20,35)' : 'transparent'
    }));

    const selOption = optionList[s.sel] || optionList[0] || null;

    const defaultWorld = env.scenario_name
      ? `Scenario ${env.scenario_name} (${env.scenario}), batch ${env.batch}, evaluated as of ${env.as_of}. ${this.SCENARIOS[s.scenario].desc}`
      : `Scenario: ${this.SCENARIOS[s.scenario].label}. ${s.ccmd} is supporting a plan against ${T.label}. ${T.desc}`;

    return {
      brandMark: B.mark || '【Pytho】', brandTitle: B.title || 'Strategy Adjudicator', brandProduct: B.product || '',
      crumb: s.view === 'collection' ? 'Collection Management Agent' : s.view === 'doctrine' ? 'Doctrine' : s.step === 3 ? 'Predictive Interconnected Risk Engine' : s.step === 5 ? 'Option Recommendation' : s.step === 1 ? 'Inputs / ' + { strategy: 'Strategy', intel: 'Intelligence', docs: 'Plans & Guidance', posture: 'Force Posture' }[s.inputTab] : 'Strategy Option Evaluation',
      showWorkflow: s.view !== 'doctrine',
      isCoa: s.view === 'coa', isIntel: s.step === 1 && s.inputTab === 'intel', isCollection: s.view === 'collection', isRfi: s.view === 'collection', isPosture: s.step === 1 && s.inputTab === 'posture', isDoctrine: s.view === 'doctrine',
      inputStrategy: s.inputTab === 'strategy',

      // ── API state. An error stops every numeric screen and prints the backend's
      //    own code and message; nothing degrades to a locally computed number.
      apiFailed: !!s.apiError, apiOk: !s.apiError, apiLoading: s.loading && !s.apiError,
      apiError: s.apiError || {},
      apiErrorCode: (s.apiError || {}).code || '', apiErrorMessage: (s.apiError || {}).message || '',
      apiErrorPath: (s.apiError || {}).path || '', apiErrorLine: (s.apiError || {}).line || '',
      retry: () => this.loadAll(),
      caution: env.caution || '',
      asOf: env.as_of || '', scenarioName: env.scenario_name || '', scenarioId: env.scenario || '', batchNo: env.batch != null ? String(env.batch) : '',
      levelBasis: env.level_basis || '',
      aspirationNote: (s.dist && s.dist.aspiration_basis) || 'probability across enumerated assumption worlds, not a real-world forecast',
      binNote: (s.dist && s.dist.bin_note) || '',
      modelShape: hasOptions ? `${optionList.length} options · ${rankedRows.length} ranked · ${excluded.length} invalid · ${evaluated.length} evaluated assumptions · evaluated as of ${env.as_of}` : '',

      inputTabs: [['Strategy', 'strategy'], ['Intelligence', 'intel'], ['Plans & Guidance', 'docs'], ['Force Posture', 'posture']].map(([label, t]) => ({ label, go: () => this.setState({ inputTab: t }), line: s.inputTab === t ? 'var(--color-accent)' : 'transparent', opacity: s.inputTab === t ? 1 : 0.65 })),
      strategyName: (s.planDocs[s.planSel] || {}).name || 'No strategy document loaded',
      strategyMeta: s.planDocs[s.planSel] ? `${s.planDocs[s.planSel].words.toLocaleString()} words · ${s.planDocs[s.planSel].pages} pages · ${s.planDocs[s.planSel].status}${s.docBusy ? ' · ' + s.docBusy : ''}` : (s.docBusy || 'Parsed in your browser; mission, intent, end state and assumptions are pulled into the fields below'),
      strategyRisks: s.planDocs[s.planSel] ? this.planRisk(s.planDocs[s.planSel]).risks : [],
      planTypeDesc: (p => `${p.label} — ${p.desc}`)(this.PLAN_TYPES.find(x => x.id === s.planType)),
      scenarioLabel: this.SCENARIOS[s.scenario].label, showScenario: s.details.scenario, toggleScenario: tog('scenario'), scenarioToggle: s.details.scenario ? 'Hide details' : 'Edit scenario',
      showArc: s.details.arc, toggleArc: tog('arc'), arcToggle: s.details.arc ? 'Hide risk graph' : 'Show risk graph',
      showSens: s.details.sens, toggleSens: () => { if (!s.details.sens) this.loadTornado(); tog('sens')(); }, sensToggle: s.details.sens ? 'Hide details' : 'Show details',
      showPirDetail: s.details.pir, togglePir: tog('pir'), pirToggle: s.details.pir ? 'Hide indicators and assets' : 'Show indicators and assets',
      pirSummary,
      onPirKey: e => { if (e.key === 'Enter' && s.newPir.trim()) this.setState({ pirs: [...s.pirs, { q: s.newPir.trim(), ind: ['Indicators to be defined'], assets: ['Unassigned'], ltiov: 'TBD', status: 0 }], newPir: '' }); },
      goCollection: () => this.go('collection'), goDoctrine: () => this.go('doctrine'), goHome: () => this.toStep({ view: 'coa', step: 1, inputTab: 'strategy' }),
      feedUrl: s.feedUrl, onFeedUrl: set('feedUrl'), toggleFeed: () => this.toggleFeed(), feedBtn: s.feedOn ? 'Disconnect' : 'Connect', feedLabel: s.feedOn ? `Connected · ${s.feedCount} received` : 'Not connected', feedColor: s.feedOn ? 'rgb(76,195,138)' : 'var(--color-neutral-600)',
      stages: [['Strategy Option Evaluation', 'Scores strategies against their assumptions and shows exactly where the analysis stands on thin evidence.', 1], ['Collection Management Agent', 'Turns weak assumptions into draft collection requirements: tagged, routed, tracked. Scores re-run as collection returns.', 2], ['Predictive Interconnected Risk Engine', 'Reads the graph\'s edges and propagates: which option degrades if this assumption fails, and how far it travels.', 3], ['Option Recommendation', 'Strategy evaluation taking in every gap and risk; offers the Commander a recommended option and the risk accepted.', 4]].map(([label, sub, n]) => { const active = stage === n; const done = n === 1 ? hasOptions : n === 2 ? requirements.length > 0 : n === 3 ? !!s.dist : !!s.decision; return { n, label, sub, lineShow: n < 4 ? 'block' : 'none', go: () => n === 1 ? this.toStep({ view: 'coa', step: [1, 2, 4].includes(s.step) ? s.step : 1, inputTab: 'strategy' }) : n === 2 ? this.go('collection') : n === 3 ? this.toStep({ view: 'coa', step: 3 }) : this.toStep({ view: 'coa', step: 5 }), ring: active || done ? 'var(--color-accent)' : 'var(--color-divider)', bg: active ? 'rgb(16,42,76)' : done ? 'rgb(9,84,165)' : 'var(--color-surface)', fg: active || done ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: active ? 1 : 0.65 }; }),
      foundation: { go: () => this.go('intel'), ring: stage === 5 ? 'var(--color-accent)' : 'var(--color-divider)', bg: stage === 5 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: stage === 5 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', stat: `${evaluated.length} evaluated assumptions · ${s.intel.length} local reports · ${s.planDocs.length + s.guideDocs.length} documents` },
      hasSubtabs: s.view === 'coa' && [1, 2, 4].includes(s.step),
      subtabs: [['Inputs', 1], ['Options', 2], ['Score', 4]].map(([label, st]) => ({ label, go: () => this.goStep(st), line: s.step === st ? 'var(--color-accent)' : 'transparent', opacity: s.step === st ? 1 : 0.65 })),
      step1: s.step === 1, step2: s.step === 2, step3: s.step === 3, step4: s.step === 4, step5: s.step === 5,
      globalNav: [],
      sections: [
        { hasLabel: true, label: 'Workflow', items: [{ ...navItem('coa', 'Strategy Option Evaluation', 'coa'), border: stage === 1 ? 'rgb(30,41,59)' : 'transparent', dot: stage === 1 ? 'var(--color-accent-700)' : 'transparent', go: () => this.toStep({ view: 'coa', step: [1, 2, 4].includes(s.step) ? s.step : 1 }) }, navItem('collection', 'Collection Management Agent', 'collection'), { ...navItem('coa', 'Predictive Risk Engine', 'coa'), border: stage === 3 ? 'rgb(30,41,59)' : 'transparent', dot: stage === 3 ? 'var(--color-accent-700)' : 'transparent', go: () => this.toStep({ view: 'coa', step: 3 }) }, { ...navItem('coa', 'Option Recommendation', 'coa'), border: stage === 4 ? 'rgb(30,41,59)' : 'transparent', dot: stage === 4 ? 'var(--color-accent-700)' : 'transparent', go: () => this.toStep({ view: 'coa', step: 5 }) }] },
        { hasLabel: true, label: 'Foundational Data Ingestion', items: [navItem('intel', 'Intelligence', 'intel'), navItem('docs', 'Plans & Strategic Guidance', 'docs'), navItem('posture', 'Force Posture & GFM', 'posture'), navItem('rfi', 'RFI Management', 'rfi')] },
        { hasLabel: true, label: 'Reference', items: [navItem('doctrine', 'Doctrine', 'doctrine')] }
      ],
      planLabel, ccmd: s.ccmd, threatName: T.name, runId: s.runId,
      resetRun: () => { this.setState({ dist: null, decision: null, chosen: null, whatIf: null, whatIfId: null, tornado: null, runId: 'R-' + String(400 + Math.floor(Math.random() * 500)).padStart(4, '0') }); this.toStep({ step: 1 }); },
      steps: [['Strategy Preparation', 'Mission Analysis & Guidance'], ['Development', 'Concepts & Screening'], ['Option Adjudication', 'Risk engine · what-if'], ['Option\nComparison', 'Decision Matrix'], ['Strategy Decision', "Commander's decision"]].map(([label, sub], i) => ({ n: i + 1, label, sub, go: () => this.goStep(i + 1),
        lineShow: i < 4 ? 'block' : 'none', ring: s.step >= i + 1 ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.step > i + 1 ? 'rgb(9,84,165)' : s.step === i + 1 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: s.step >= i + 1 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: s.step === i + 1 ? 1 : 0.6 })),
      planTypes: this.PLAN_TYPES, planType: s.planType, onPlanType: e => this.setState({ planType: e.target.value }), onCcmd: e => this.setState({ ccmd: e.target.value }), threat: s.threat, onThreat: e => this.setState({ threat: e.target.value }),
      isContingency: s.planType === 'CON', levels: this.LEVELS.map((l, i) => ({ label: `L${i + 1}`, on: s.level === i + 1, pick: () => this.setState({ level: i + 1 }) })), levelDesc: this.LEVELS[s.level - 1],
      ccmds: Object.keys(this.CCMDS).map(c => { const a = s.ccmd === c ? on : off; return { label: c, pick: () => this.setState({ ccmd: c }), border: a[0], bg: a[1], fg: a[2] }; }), ccmdDesc: this.CCMDS[s.ccmd],
      threats: Object.keys(this.THREATS).map(k => { const a = s.threat === k ? on : off; return { id: k, label: this.THREATS[k].label, pick: () => this.setState({ threat: k }), border: a[0], bg: a[1], fg: a[2] }; }), threatDesc: T.desc,
      intelCount: s.intel.length, worldState: s.worldState || defaultWorld, onWorldState: set('worldState'),
      intent: s.intent || (s.planDocs[0] ? s.planDocs[0].intent : ''), onIntent: set('intent'),
      endState: s.endState || (s.planDocs[0] ? s.planDocs[0].endState : ''), onEndState: set('endState'),
      assumptions: trackerRows, assumptionSummary,
      scenarios: this.SCENARIOS.map((sc, i) => ({ ...sc, pick: () => this.setState({ scenario: i, worldState: '' }), border: s.scenario === i ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.scenario === i ? 'rgb(16,36,62)' : 'transparent' })),
      newAssumption: s.newAssumption, onNewAssumption: set('newAssumption'),
      addAssumption: () => s.newAssumption.trim() && this.setState({ assumptions: [...s.assumptions, { text: s.newAssumption.trim(), link: '' }], newAssumption: '' }),
      onAssumptionKey: e => { if (e.key === 'Enter' && s.newAssumption.trim()) this.setState({ assumptions: [...s.assumptions, { text: s.newAssumption.trim(), link: '' }], newAssumption: '' }); },
      constraints: s.constraints.map((c, i) => ({ code: `${c.kind}${s.constraints.slice(0, i + 1).filter(x => x.kind === c.kind).length}`, text: c.text, remove: () => this.setState({ constraints: s.constraints.filter((_, j) => j !== i) }) })),
      constraintKinds: [['C', 'Constraint'], ['R', 'Restraint']].map(([k, label]) => ({ label, on: s.constraintKind === k, pick: () => this.setState({ constraintKind: k }) })),
      constraintPlaceholder: s.constraintKind === 'C' ? 'Add constraint (something the commander must do)' : 'Add restraint (something the commander must not do)',
      newConstraint: s.newConstraint, onNewConstraint: set('newConstraint'),
      addConstraint: () => s.newConstraint.trim() && this.setState({ constraints: [...s.constraints, { kind: s.constraintKind, text: s.newConstraint.trim() }], newConstraint: '' }),
      onConstraintKey: e => { if (e.key === 'Enter' && s.newConstraint.trim()) this.setState({ constraints: [...s.constraints, { kind: s.constraintKind, text: s.newConstraint.trim() }], newConstraint: '' }); },
      startDevelopment: () => this.toStep({ step: 2 }),
      coas, coaCount: optionList.length,
      startWargame: () => this.toStep({ step: 3 }, s.dist ? null : () => this.runWargame()),
      runSim: () => this.runWargame(), runLabel: s.dist ? 'Re-run Wargame' : 'Run Wargame',
      distBusy: s.distBusy, rankBusy: s.rankBusy,
      hasResults: !!s.dist && hasOptions && !s.distBusy, noResults: !s.dist && !s.distBusy,
      hasOptions, noOptions: !hasOptions && !s.apiError,
      results, selN: selOption ? selOption.number : '', selTitle: selOption ? selOption.title : '',
      riskProblemSets, riskEvents, cascade,
      goCompare: () => this.toStep({ step: 4 }), goApprove: () => this.toStep({ step: 5 }),
      evalGrade, evalSummary, evalStats, evalGaps, evalRisks, evalConditions,
      matrix, scoreRow, ranked, best,
      explain, explainText, runnerUp: runnerRow ? { n: runnerRow.number, title: runnerRow.title } : {},
      stability, stabilityText, stabilityLabel, tornado, tornadoBusy: s.tornadoBusy,
      sweep, sweepText, assumptionRisk, assumptionText,
      weakCount: weakEval.length,
      evidence,
      sendWeakToCollection: () => {
        const add = weakEval.filter(a => !requirementFor(a) && draftFor(a) < 0)
          .map(a => ({ q: 'Validate: ' + textOf(a), ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], ltiov: 'TBD', status: 0, assumption: a.assumption_id }));
        this.setState({ pirs: [...s.pirs, ...add], view: 'collection' });
      },
      weakList, noWeak: hasOptions && weakEval.length === 0,
      failToggles,
      hasFail: !!wi, whatIfBusy: s.whatIfBusy,
      failN: wiAssumption ? ((byId.get(wiAssumption.assumption_id) || {}).n || '') : '',
      failText: wiAssumption ? (wordingFor(wiAssumption.statement) || wiAssumption.statement) : '',
      failStats: wiAssumption ? `status ${wiAssumption.status} · p(holds) ${f3(wiAssumption.p_holds)} → ${f3(wiAssumption.p_holds_after_withdrawn)} · sensitivity ${f3(wiAssumption.sensitivity)} · EVPI ${f3(wiAssumption.evpi)}` : '',
      propagation, problemSets, harmfulMoved, statusChanges, propagationText,
      claimCount: evaluated.length + s.intel.length,
      claims: [
        ...evaluated.map(a => { const st = aStat(a.status); return { text: textOf(a), type: 'Assumption', source: `${a.subject_name || a.subject_id || 'unlinked'} · ${a.predicate || '—'}`, valid: `evaluated as of ${env.as_of || '—'}`, conf: pctStr(a.p_holds), bg: st[1], fg: st[2], edges: a.options.map(n => 'Strategy ' + n).join(', ') || '—' }; }),
        ...s.intel.map(r => ({ text: r.title, type: r.type, source: r.rel + ' · local demo item', valid: r.when === 'just now' ? 'received this session' : r.when, conf: NA, bg: 'rgb(30,41,59)', fg: 'var(--color-neutral-700)', edges: 'not in the evaluated claim set' }))
      ],
      tradeoffs,
      chosen: chosenR, decisionNote: s.decisionNote, onDecisionNote: set('decisionNote'),
      approve: () => this.decide('Approved'), approveMod: () => this.decide('Approved with modifications'), returnRework: () => this.decide('Returned for rework'),
      hasDecision: !!s.decision, noDecision: !s.decision, decision: s.decision || {},
      isDocs: s.step === 1 && s.inputTab === 'docs', prevent: e => e.preventDefault(),
      dropPlan: e => this.loadDocs(this.filesFrom(e), 'plan'), pickPlan: e => this.loadDocs(this.filesFrom(e), 'plan'),
      dropGuide: e => this.loadDocs(this.filesFrom(e), 'guide'), pickGuide: e => this.loadDocs(this.filesFrom(e), 'guide'),
      dropIntel: e => this.loadDocs(this.filesFrom(e), 'intel'), pickIntel: e => this.loadDocs(this.filesFrom(e), 'intel'),
      planDocCount: s.planDocs.length, goDocs: () => this.go('docs'),
      planDocs: s.planDocs.map((d, i) => { const r = this.planRisk(d); return { name: d.name, kind: d.kind, meta: `${d.words.toLocaleString()} words · ${d.pages} pages · ${d.status}${s.docBusy && i === s.planDocs.length - 1 ? ' · ' + s.docBusy : ''}`, risks: r.risks, select: () => this.setState({ planSel: i }), border: s.planSel === i ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.planSel === i ? 'rgb(16,36,62)' : 'transparent' }; }),
      guideDocs: s.guideDocs.map((g, i) => ({ ...g, remove: () => this.setState({ guideDocs: s.guideDocs.filter((_, j) => j !== i) }) })),
      hasPlanSel: !!s.planDocs[s.planSel],
      planSel: s.planDocs[s.planSel] ? { ...s.planDocs[s.planSel], ...this.planRisk(s.planDocs[s.planSel]), words: s.planDocs[s.planSel].words.toLocaleString() } : {},
      sendToCoa: () => this.applyPlan(s.planDocs[s.planSel]), guidanceSource: s.planDocs[s.planSel] ? 'Parsed from ' + s.planDocs[s.planSel].name.replace(/\.(docx|pdf|txt|md)$/i, '').replace(/\s+[—–-]\s+.*$/, '') : 'No strategy loaded',
      intel: s.intel, newIntelTitle: s.newIntelTitle, onNewIntelTitle: set('newIntelTitle'), newIntelBody: s.newIntelBody, onNewIntelBody: set('newIntelBody'),
      intelTypes: ['SIGINT', 'IMINT', 'GEOINT', 'HUMINT', 'OSINT'].map(t => ({ label: t, on: s.newIntelType === t, pick: () => this.setState({ newIntelType: t }) })),
      ingest: () => s.newIntelTitle.trim() && this.setState({ intel: [{ title: s.newIntelTitle.trim(), type: s.newIntelType, rel: 'F – Not yet evaluated', pir: 1 + (s.intel.length % 3), when: 'just now' }, ...s.intel], newIntelTitle: '', newIntelBody: '' }),
      mapSrc: './assets/jipoe-map/index.html?threat=' + encodeURIComponent(T.name),
      pirs, newPir: s.newPir, onNewPir: set('newPir'),
      addPir: () => s.newPir.trim() && this.setState({ pirs: [...s.pirs, { q: s.newPir.trim(), ind: ['Indicators to be defined'], assets: ['Unassigned'], ltiov: 'TBD', status: 0 }], newPir: '' }),
      rfis: s.rfis.map(r => ({ ...r, bg: ({ Open: 'rgb(174,25,85)', Pending: 'rgb(130,78,0)', Answered: 'rgb(35,110,74)' })[r.status], fg: ({ Open: 'rgb(254,236,244)', Pending: 'rgb(254,243,221)', Answered: 'rgb(229,251,235)' })[r.status] })), newRfi: s.newRfi, onNewRfi: set('newRfi'),
      addRfi: () => s.newRfi.trim() && this.setState({ rfis: [...s.rfis, { id: `RFI-0${35 + s.rfis.length - 4}`, q: s.newRfi.trim() + (s.newRfiLtiov ? ` (LTIOV ${s.newRfiLtiov})` : ''), to: s.newRfiRoute || 'J2', ties: s.newRfiTies || 'Unlinked', status: 'Open' }], newRfi: '', newRfiTies: '', newRfiLtiov: '', rfiOpen: false }),
      rfiOpen: !!s.rfiOpen, openRfi: () => this.setState({ rfiOpen: true }), closeRfi: () => this.setState({ rfiOpen: false }), stop: e => e.stopPropagation(),
      rfiRoutes: ['J2 / DIA', 'J4', 'J5', 'Interagency'].map(r => ({ label: r, on: (s.newRfiRoute || 'J2 / DIA') === r, pick: () => this.setState({ newRfiRoute: r }) })),
      newRfiTies: s.newRfiTies || '', onNewRfiTies: set('newRfiTies'), newRfiLtiov: s.newRfiLtiov || '', onNewRfiLtiov: set('newRfiLtiov'),
      postureStats: [{ label: 'Component commands', value: '5' }, { label: 'Designated for AMBER SHIELD', value: '11 packages' }, { label: 'C-1 / C-2 ready', value: '78%' }, { label: 'Peak strategy demand', value: NA }],
      forces: [
        { unit: 'V Corps (Forward) · ARFOR / corps HQ', domain: 'Land', source: 'Assigned', loc: 'Poznań', c: 'C-1', avail: 'C+1' },
        { unit: '2nd Cavalry Regiment (SBCT)', domain: 'Land', source: 'Assigned', loc: 'Vilseck', c: 'C-1', avail: 'C+4 (Lithuania)' },
        { unit: '1st Armored Division · 2 ABCT via APS-2, 1 ABCT via sealift', domain: 'Land', source: 'Allocated (CONUS)', loc: 'Fort Bliss → Powidz / Orzysz', c: 'C-2', avail: 'C+21 / C+45' },
        { unit: '41st FA Bde and 56th Artillery Command (HIMARS / MLRS / MDTF)', domain: 'Fires', source: 'Assigned', loc: 'Grafenwöhr / Wiesbaden', c: 'C-1', avail: 'C-Day' },
        { unit: '10th AAMDC · Patriot / IFPC', domain: 'IAMD', source: 'Assigned', loc: 'Kaiserslautern → Powidz, Rzeszów, Riga', c: 'C-2', avail: 'C+3' },
        { unit: '12th CAB · attack, lift, MEDEVAC', domain: 'Aviation', source: 'Assigned', loc: 'Ansbach', c: 'C-1', avail: 'C+7' },
        { unit: '173rd Airborne Brigade · theater response force', domain: 'Land', source: 'Assigned', loc: 'Vicenza', c: 'C-1', avail: '24-h alert from C-Day' },
        { unit: '48th, 52nd, 31st Fighter Wings (F-35A / F-15E / F-16)', domain: 'Air', source: 'Assigned', loc: 'Lakenheath / Spangdahlem / Aviano → Šiauliai, Ämari, Łask', c: 'C-1', avail: 'C-Day' },
        { unit: 'Rota FDNF destroyers · P-8A · expeditionary MCM', domain: 'Maritime', source: 'Assigned', loc: 'Rota / Sigonella / Keflavik', c: 'C-2', avail: 'C-Day' },
        { unit: 'Carrier Strike Group', domain: 'Maritime', source: 'Allocated', loc: 'North Atlantic / Norwegian Sea', c: 'C-2', avail: 'Retained vs Northern Fleet' },
        { unit: 'SOCEUR SOF · special reconnaissance, resistance support', domain: 'SOF', source: 'Assigned', loc: 'Stuttgart / Baltics', c: 'C-1', avail: 'C-Day' },
        { unit: 'Marine rotational force / MEU element', domain: 'Maritime / Land', source: 'Allocated', loc: 'Rota → Estonian islands / Gotland', c: 'C-2', avail: 'C+10' },
        { unit: '21st TSC · RSOI, APS-2 issue, theater sustainment', domain: 'Logistics', source: 'Assigned', loc: 'Kaiserslautern / Powidz / Bremerhaven', c: 'C-1', avail: 'Now' },
        { unit: 'APODs / SPODs (Ramstein, Rzeszów, Powidz, Bremerhaven, Gdańsk/Gdynia)', domain: 'Mobility', source: 'HNS', loc: 'DEU / POL', c: 'C-1', avail: 'Now' }
      ],
      ipoe: s.threat === 'RUS' ? { likely: 'Russia consolidates its gains in Narva/Ida-Viru and eastern Latgale, transitions to maneuver defense behind a dense mine, obstacle and EW belt, and seeks a negotiated freeze that leaves Russian forces in place. Kaliningrad and Belarus-based forces remain postured but uncommitted to fix Allied forces in Lithuania and Poland. Hybrid pressure continues (cyber, sabotage of undersea cables and rail LOCs, disinformation targeting Baltic Russophones) and nuclear signaling escalates as NATO builds combat power.', dangerous: 'Russia expands the incursion before NATO reinforcement is complete: 1st Guards Tank Army elements reinforce through the Pskov axis toward Tartu and the Daugava; 11th Army Corps and Belarus-based forces conduct a converging attack to close the Suwałki corridor and isolate the Baltic States; the Baltic Fleet mines and strikes to close Klaipėda, Riga and Tallinn and interdict the Danish Straits; and Russia conducts a demonstrative low-yield nuclear detonation over the Baltic Sea to coerce Alliance disunity.', terrain: 'Suwałki corridor (only land LOC to the Baltics); Narva River crossings; Daugava River line through Latgale; Tallinn, Riga and Klaipėda ports; Šiauliai and Ämari airfields; Danish Straits; Gulf of Finland and Gulf of Riga (mine-favorable).' }
        : { likely: `${T.name} escalates gray-zone coercion into a limited seizure of a peripheral objective under cover of an exercise, seeking a fait accompli within 72 hours.`, dangerous: `${T.name} opens with pre-emptive long-range fires on regional bases and cyber attacks on logistics, then commits amphibious and airborne forces simultaneously.`, terrain: 'Maritime chokepoints, forward airfields within 500 nm of the objective, undersea cable landing sites.' },
      doctrine: [
        { ref: 'CJCSI 3100.01F · 29 Jan 2024', title: 'Joint Strategic Planning System', note: 'Directs three types of campaign plans (GCP, FCP, CCP), integrated contingency plan sets and Strategic Planning Frameworks; frames advice around risk to strategy, risk to force and readiness.', used: 'Plan type selector, CCMD selection, GFM inputs' },
        { ref: 'JP 5-0 · Joint Planning', title: 'Joint Planning Process', note: 'Mission analysis, COA development, COA analysis and wargaming, COA comparison and approval; screening for feasibility, acceptability, suitability, distinguishability and completeness.', used: 'Five-step lifecycle, COA screening tags' },
        { ref: 'CJCSM 3105.01 · JRAM', title: 'Joint Risk Analysis Methodology', note: 'Risk appraised on a four-level scale (Low, Moderate, Significant, High) against probability and consequence; risk-to-mission and risk-to-force as governing lenses.', used: 'Risk scale, decision matrix' },
        { ref: 'JP 2-01.3 · JIPOE', title: 'Intelligence Preparation of the Operational Environment', note: 'Defines the environment, evaluates the adversary, and determines adversary most likely and most dangerous courses of action.', used: 'JIPOE panel, red-cell reactions in the ARC table' },
        { ref: 'USEUCOM OPORD 26-004 · 09 SEP 2026', title: 'Operation AMBER SHIELD', note: 'US force employment in support of NATO collective defense of the Baltic States under SACEUR OPLAN 2026-BAL; three lines of effort (Reinforce and Defend; Shape and Restore; Deter, Protect and Communicate) across four phases; ten PIRs linked to decision points.', used: 'Strategy under adjudication; assumptions, PIRs and constraints' },
        { ref: 'JP 2-0 · Joint Intelligence', title: 'Collection management', note: 'PIRs decomposed into indicators and specific information requirements, tasked to collection assets with latest time information is of value.', used: 'Collection Management, RFI routing' }
      ]
    };
  }
}
