class Component extends DCLogic {
  state = {
    view: 'coa', step: 1, runId: 'R-0417',
    planType: 'OPORD', level: 3, ccmd: 'EUCOM', threat: 'OLV',
    worldState: '', intent: '', endState: '',
    assumptions: [
      { text: 'UNSCR 2781 (S/2026/041) remains in force for the duration of MNFA operations, providing legal authority for multinational military action.', status: 0, conf: 90, link: 'Ref a · UNSCR 2781', valid: 'Duration of MNFA ops' },
      { text: 'NATO allies will not formally invoke Article 5 but will provide political endorsement and overflight/transit rights through the European theater in support of EUCOM force deployment.', status: 1, conf: 70, link: 'OPORD 1.g.2', valid: 'Through Phase IV' },
      { text: 'EUCOM will maintain sufficient combat power in the European theater to deter opportunistic Russian or North Torbian aggression during the period of force reallocation to MNFA.', status: 1, conf: 50, link: 'OPORD 1.g.3', valid: 'C-Day to D+150' },
      { text: 'Strategic air and sealift, coordinated through USTRANSCOM, will be sufficient to deploy designated EUCOM force contributions to the INDOPACOM AOR NLT C-Day, 10 April 2026.', status: 1, conf: 60, link: 'OPORD 1.g.4', valid: 'Expires C-Day 10 APR' },
      { text: 'Olvana will not conduct offensive operations against the continental United States or European theater during the operational period; nuclear threat is confined to the Indo-Pacific JOA.', status: 1, conf: 60, link: 'OPORD 1.g.5', valid: 'Operational period' },
      { text: 'Participating countries will provide individual funding for their deployed forces unless otherwise agreed through bilateral or multilateral arrangements.', status: 0, conf: 80, link: 'WARNORD 26-001 4.B', valid: 'Operational period' },
      { text: 'CENTRIXS–MNFA provides adequate coalition C2 interoperability for EUCOM-assigned forces operating within the MNFA C2 structure.', status: 1, conf: 70, link: 'OPORD 1.g.7', valid: 'From C-Day' }
    ],
    scenario: 0,
    newAssumption: '',
    constraints: [
      { kind: 'C', text: 'Transfer designated forces to USINDOPACOM OPCON NLT C-Day, 10 April 2026, per TPFDD' },
      { kind: 'C', text: 'Maintain minimum essential deterrence posture in the European theater per SACEUR guidance' },
      { kind: 'C', text: 'Establish liaison at MNFA HQ Bangkok and USINDOPACOM HQ NLT C-Day' },
      { kind: 'C', text: 'Deploying units complete MOPP training and CBRN familiarization before entering the JOA' },
      { kind: 'R', text: 'No degradation of NATO Enhanced Air Policing missions by force reallocation' },
      { kind: 'R', text: 'No public release on EUCOM force contributions without USEUCOM PA and USINDOPACOM coordination' },
      { kind: 'R', text: 'Forces transferred to MNFA operate only under MNFA ROE; European forces under existing EUCOM/NATO ROE' }
    ],
    newConstraint: '', constraintKind: 'C',
    numCoas: 3, numSims: 2000, aggression: 0.5,
    coas: [], results: null, simRunning: false, simProgress: 0, simStatus: '', sel: 0,
    weights: { mission: 4, personnel: 3, escalation: 4, time: 2, resources: 1 },
    chosen: null, decisionNote: '', decision: null,
    intel: [
      { title: 'OPA 18th Army reserve brigades (18-1 to 18-4) staging in Bagansait', type: 'IMINT', rel: 'B – Usually reliable', pir: 1, when: '2 h ago' },
      { title: 'Southern Fleet Yuan-class submarines sortie toward Malacca approaches', type: 'SIGINT', rel: 'A – Reliable', pir: 1, when: '5 h ago' },
      { title: 'Olvanan IO themes targeting European transit-state publics', type: 'OSINT', rel: 'C – Fairly reliable', pir: 3, when: '9 h ago' },
      { title: 'Russian Western MD snap-exercise notification, Baltic region', type: 'SIGINT', rel: 'B – Usually reliable', pir: 3, when: '14 h ago' },
      { title: 'Radiation survey, Udon Thani contamination zone', type: 'GEOINT', rel: 'A – Reliable', pir: 2, when: '1 d ago' },
      { title: 'RRLA reporting: 788th SSM Command dispersal in northern Sungzon', type: 'HUMINT', rel: 'C – Fairly reliable', pir: 2, when: '1 d ago' }
    ],
    newIntelTitle: '', newIntelBody: '', newIntelType: 'SIGINT',
    pirs: [
      { q: 'Will the OPA launch a renewed offensive into southern Khorathidin before D-Day (MDCOA)?', ind: ['18th Army reserve moves out of Bagansait', 'Amphibious lift loading at Southern Fleet ports', '788th / 789th SSM Command dispersal'], assets: ['EO/IR satellite', 'MPA orbit', 'RRLA reporting'], reports: 2, ltiov: 'D-10', status: 1 },
      { q: 'Will Olvana employ additional nuclear or WMD strikes against coalition forces or staging ports?', ind: ['Nuclear C2 alert changes', 'Warhead movement to delivery units', 'IO pre-justification themes'], assets: ['National technical means', 'STRATCOM space ISR', 'OSINT cell'], reports: 2, ltiov: 'Continuous', status: 1 },
      { q: 'Will Russia or North Torbia exploit the EUCOM force drawdown during the reallocation window?', ind: ['Western MD snap exercises', 'Baltic Fleet sorties', 'Hybrid activity against Baltic states'], assets: ['NATO AWACS', 'SIGINT', 'eFP battlegroup reporting'], reports: 2, ltiov: 'C-Day', status: 0 }
    ],
    newPir: '',
    rfis: [
      { id: 'RFI-031', q: 'Confirm HNS port and airfield access windows (Germany, Spain, Italy, Portugal) for C-Day force flow.', to: 'J4 / Embassies', ties: 'Assumption A2', status: 'Open' },
      { id: 'RFI-032', q: 'USTRANSCOM lift allocation sufficient to close BCT, fighter wing and CSG/ARG by C-Day, 10 APR 2026?', to: 'USTRANSCOM', ties: 'Assumption A4', status: 'Pending' },
      { id: 'RFI-033', q: 'SACEUR minimum essential deterrence force list for the European theater during reallocation.', to: 'J5 / NATO', ties: 'Assumption A3', status: 'Open' },
      { id: 'RFI-034', q: 'CENTRIXS–MNFA terminal availability for EUCOM FLE at INDOPACOM HQ and MNFA HQ Bangkok.', to: 'J6', ties: 'Assumption A7', status: 'Answered' }
    ],
    newRfi: '',
    planDocs: [
      { name: 'USEUCOM OPORD 26-002 — OPERATION ENDURING PHOENIX.docx', kind: 'DOCX', words: 4900, pages: 11, status: 'Parsed', text: '',
        mission: 'USEUCOM, as supporting combatant command to USINDOPACOM, on order NLT C-Day (10 April 2026), deploys designated ground, air, naval and special operations forces from the European theater under USINDOPACOM/MNFA OPCON, provides sustained logistical and enabling support through European strategic staging areas, and maintains sufficient deterrence posture in the European theater, in order to support MNFA in executing Operation ENDURING PHOENIX to expel Olvanan forces from Khorathidin, then Sungzon, restore their territorial sovereignty, and re-establish regional stability IAW UNSCR 2781.',
        intent: 'Deploy forward combat power and enabling capabilities to reinforce MNFA decisive operations while sustaining the credibility of US deterrence in the European theater — demonstrating that the United States can simultaneously sustain Alliance commitments in Europe and execute major combat operations in the Indo-Pacific, and thereby deter opportunistic aggression.',
        endState: 'Designated EUCOM forces integrated into MNFA C2 and operationally effective in the JOA; European theater deterrence posture sufficient to preclude opportunistic aggression; EUCOM staging infrastructure sustaining uninterrupted flow of forces and materiel; EUCOM information operations reinforcing the legitimacy and resolve of MNFA.',
        assumptions: ['Assumption: UNSCR 2781 remains in force for the duration of MNFA operations.', 'Assumption: NATO allies will not invoke Article 5 but will provide overflight/transit rights.', 'Assumption: EUCOM will maintain sufficient combat power to deter opportunistic Russian or North Torbian aggression.', 'Assumption: Strategic lift is sufficient to deploy EUCOM contributions NLT C-Day.', 'Assumption: Olvana will not conduct offensive operations against CONUS or the European theater.', 'Assumption: CENTRIXS–MNFA provides adequate coalition C2 interoperability.'],
        phases: ['Phase I Isolate', 'Phase II Secure (C-Day to D+60)', 'Phase III Dominate (D+60 to D+150)', 'Phase IV Transition (D+150+)'],
        sig: { offensive: 5, defensive: 13, escalation: 6, restraint: 6, force: 6, partners: 15, sustain: 14, intel: 6 } }
    ],
    guideDocs: [
      { name: '2022 National Defense Strategy', tier: 'SecDef', directs: 'Integrated deterrence; PRC as pacing challenge; campaigning.', sig: { offensive: 2, defensive: 9, escalation: 2, restraint: 7, force: 2, partners: 14, sustain: 4, intel: 3 } },
      { name: '2022 National Military Strategy', tier: 'CJCS', directs: 'Risk to force and risk to strategy framing; joint force development.', sig: { offensive: 3, defensive: 8, escalation: 3, restraint: 5, force: 4, partners: 9, sustain: 5, intel: 4 } },
      { name: 'JSCP (CJCSI 3110.01)', tier: 'CJCS', directs: 'Campaign and contingency planning tasks; plan levels; integrated plan sets.', sig: { offensive: 3, defensive: 6, escalation: 2, restraint: 4, force: 3, partners: 7, sustain: 9, intel: 6 } },
      { name: 'Contingency Planning Guidance', tier: 'President / SecDef', directs: 'Priority contingencies, planning assumptions, escalation constraints.', sig: { offensive: 2, defensive: 7, escalation: 4, restraint: 9, force: 3, partners: 8, sustain: 4, intel: 4 } },
      { name: 'UNSCR 2781 (2026)', tier: 'UN Security Council', directs: 'Authorizes MNFA to restore the territorial sovereignty of Khorathidin and Sungzon.', sig: { offensive: 3, defensive: 6, escalation: 1, restraint: 8, force: 1, partners: 12, sustain: 2, intel: 1 } },
      { name: 'CJCS WARNORD 26-001', tier: 'CJCS', directs: 'USINDOPACOM lead for MNFA; USEUCOM supporting CCMD (para 3.B.5); funding and reporting.', sig: { offensive: 4, defensive: 7, escalation: 3, restraint: 5, force: 3, partners: 10, sustain: 9, intel: 5 } }
    ],
    planSel: 0, docBusy: ''
  };

  async loadDocs(files, kind) {
    const mod = await import('./assets/docreader.js');
    for (const f of files) {
      this.setState({ docBusy: `Reading ${f.name}…` });
      let doc;
      try { doc = await mod.readDocument(f); } catch (e) { doc = { name: f.name, kind: f.name.split('.').pop().toUpperCase(), text: '', words: 0, pages: 0 }; }
      const sig = mod.signalIndex(doc.text || '');
      if (kind === 'plan') {
        const ex = mod.extractPlan(doc.text || '');
        const entry = { ...doc, status: doc.text ? 'Parsed' : 'Could not read text — metadata only', mission: ex.mission || 'Not found in document', intent: ex.intent || 'Not found in document', endState: ex.endState || 'Not found in document', assumptions: ex.assumptions.length ? ex.assumptions : ['No explicit assumptions found'], phases: ex.phases, sig };
        this.setState(s => ({ planDocs: [...s.planDocs, entry], planSel: s.planDocs.length }));
      } else if (kind === 'guide') {
        this.setState(s => ({ guideDocs: [...s.guideDocs, { name: doc.name, tier: 'Uploaded', directs: (doc.text || '').slice(0, 90).replace(/\s+/g, ' ') || 'Text not readable', sig }] }));
      } else {
        this.setState(s => ({ intel: [{ title: doc.name, type: s.newIntelType, rel: 'F – Not yet evaluated', pir: 1 + (s.intel.length % 3), when: 'just now' }, ...s.intel], newIntelBody: (doc.text || '').slice(0, 600) }));
      }
    }
    this.setState({ docBusy: '' });
  }
  filesFrom(e) { e.preventDefault(); return Array.from((e.dataTransfer && e.dataTransfer.files) || (e.target && e.target.files) || []); }
  planRisk(d) {
    const g = this.state.guideDocs; const avg = k => g.length ? g.reduce((a, x) => a + (x.sig[k] || 0), 0) / g.length : 0;
    const s = d.sig || {};
    const escV = (s.escalation || 0) * 0.6 + Math.max(0, (s.offensive || 0) - (s.restraint || 0)) * 0.3 - (s.restraint || 0) * 0.2 + Math.max(0, (s.escalation || 0) - avg('escalation'));
    const misV = Math.max(0, avg('partners') - (s.partners || 0)) * 0.5 + Math.max(0, avg('sustain') - (s.sustain || 0)) * 0.6 + Math.max(0, 6 - (s.intel || 0)) * 0.4 + (d.mission && d.mission.startsWith('Not found') ? 4 : 0);
    const perV = (s.force || 0) * 0.6 + (s.offensive || 0) * 0.3 - (s.defensive || 0) * 0.1;
    const lv = (v, th) => this.level(v, th); const col = l => this.riskColor(l);
    const rm = lv(misV, [2.5, 5, 8]), rp = lv(perV, [4, 7, 10]), re = lv(escV, [2.5, 5, 8]);
    const mk = (label, level, why) => ({ label, short: label.replace('Risk to ', '').replace('Risk of ', ''), level, why, bg: col(level)[0], fg: col(level)[1] });
    const alignLevel = x => { const gap = Math.abs((s.restraint || 0) - x.sig.restraint) + Math.abs((s.partners || 0) - x.sig.partners) * 0.5 + Math.max(0, (s.escalation || 0) - x.sig.escalation) * 1.5; return gap < 5 ? 'Aligned' : gap < 10 ? 'Tension' : 'Conflict'; };
    const alignColor = { Aligned: col('Low'), Tension: col('Moderate'), Conflict: col('High') };
    const findings = [];
    if (re !== 'Low') findings.push(`Escalation language (${(s.escalation || 0).toFixed(1)} per 1k words) exceeds the guidance-set average (${avg('escalation').toFixed(1)}); restraint / off-ramp language is ${(s.restraint || 0) < avg('restraint') ? 'below' : 'at or above'} guidance.`);
    if ((s.partners || 0) < avg('partners')) findings.push('Allied and partner integration is thinner than the strategy directs; integrated deterrence depends on it.');
    if ((s.sustain || 0) < avg('sustain')) findings.push('Sustainment and deployment (TPFDD, munitions, resupply) are under-specified relative to JSCP planning tasks.');
    if ((s.intel || 0) < 6) findings.push('Few PIRs / indicators referenced; wargame uncertainty will be wide until collection is defined.');
    if (!findings.length) findings.push('No material divergence from the guidance set detected; residual risk is inherent to the operational problem.');
    return { rm, rp, re, risks: [mk('Risk to mission', rm, 'Nesting with guidance, partner and sustainment coverage'), mk('Risk to personnel', rp, 'Force exposure and offensive tempo in the text'), mk('Risk of escalation', re, 'Escalatory vs restraint language against guidance')],
      alignment: g.map(x => { const l = alignLevel(x); return { doc: x.name.replace(/^\d{4}\s/, ''), level: l, note: x.directs, bg: alignColor[l][0], fg: alignColor[l][1] }; }), findings };
  }

  SCENARIOS = [
    { label: 'OPA consolidation (MLCOA)', desc: 'Defense-in-depth in Sungzon/Khorathidin; hybrid attrition; nuclear posturing', ag: 0.35 },
    { label: 'Renewed offensive (MDCOA)', desc: 'Drive to the Gulf of Khorathidin coast; amphibious ops on ports; further WMD use', ag: 0.8 },
    { label: 'Opportunistic Russia / North Torbia', desc: 'Adversaries exploit the European drawdown during force flow', ag: 0.55 }
  ];
  PROBLEM_SETS = { 0: ['Legal authority / coalition cohesion', 'Information operations'], 1: ['European transit and staging', 'Force flow timeline', 'Alliance cohesion'], 2: ['European deterrence', 'Russia / North Torbia opportunism', 'MNFA combat power'], 3: ['Force flow timeline', 'MNFA Phase II Secure', 'Sustainment pipeline'], 4: ['Homeland / European force protection', 'CBRN posture in Europe'], 5: ['Coalition funding', 'Sustainment'], 6: ['Coalition C2', 'Liaison and reporting'] };
  A_STATUS = { 0: ['Valid', 'rgb(19,57,41)', 'rgb(76,195,138)'], 1: ['Under review', 'rgb(63,34,0)', 'rgb(255,203,71)'], 2: ['Invalidated', 'rgb(174,25,85)', 'rgb(254,236,244)'] };
  PLAN_TYPES = [
    { id: 'OPORD', label: 'Operation Order', abbr: 'OPORD', desc: 'Execution order directing force contribution and support to a lead command.' },
    { id: 'CCP', label: 'Combatant Command Campaign Plan', abbr: 'CCP', desc: 'Day-to-day campaigning that operationalizes strategic guidance.' },
    { id: 'CON', label: 'Contingency Plan', abbr: 'CONPLAN / OPLAN', desc: 'Branch of the campaign for a specific threat scenario; Level 1–4 detail.' },
    { id: 'GCP', label: 'Global Campaign Plan', abbr: 'GCP', desc: 'Trans-regional, all-domain challenge integrated across CCMDs.' },
    { id: 'FCP', label: 'Functional Campaign Plan', abbr: 'FCP', desc: 'Cross-cutting functional challenge, global in scope.' },
    { id: 'SPF', label: 'Strategic Planning Framework', abbr: 'SPF', desc: 'Integrated contingency planning for a priority problem set.' }
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
    OLV: { name: 'Olvana', label: 'Olvana (OPA)', desc: 'Olvana People\'s Army: full-scale multi-domain invasion of Sungzon and Khorathidin; battlefield nuclear use at Udon Thani 14 MAR 2026; Southern Fleet submarine and SSM threat. DIA-model adversary.' },
    PRC: { name: 'PRC', label: 'China (PRC)', desc: 'Pacing challenge; multi-domain A2/AD, maritime militia, gray-zone coercion.' },
    RUS: { name: 'Russia', label: 'Russia', desc: 'Acute threat; long-range fires, hybrid and nuclear signaling.' },
    IRN: { name: 'Iran', label: 'Iran', desc: 'Proxy networks, missiles and UAS, maritime harassment.' },
    DPRK: { name: 'DPRK', label: 'North Korea', desc: 'Nuclear-armed artillery and missile threat to allies.' },
    VEO: { name: 'VEO', label: 'Violent extremist orgs', desc: 'Dispersed, partner-enabled counter-network problem.' }
  };
  COA_LIB = [
    { title: 'Full Package by C-Day', approach: 'Comply in full', deps: [2, 3, 4], s: 0.74, cas: 1.6, esc: 0.38, days: 45, res: 85, dps: 4,
      concept: 'Transfer the BCT with division enablers, one fighter wing, a CSG/ARG element and SOCEUR forces to USINDOPACOM OPCON NLT C-Day; run Ramstein, Rota, Sigonella and Lajes at maximum throughput; accept a thinned European posture with SACEUR endorsement.',
      tasks: ['OPCON transfer of all designated forces at C-Day', 'JRSOI complete at INDOPACOM reception nodes NLT C+10', 'Activate four strategic staging hubs', 'Minimum essential deterrence with residual forces'] },
    { title: 'Phased Contribution', approach: 'Sequence by phase', deps: [1, 3, 6], s: 0.66, cas: 1.2, esc: 0.22, days: 75, res: 65, dps: 5,
      concept: 'Enablers, SOF and the fighter wing transfer by C-Day; the BCT and CSG follow at D+30 once NATO backfill of eFP and Enhanced Air Policing is confirmed, keeping European deterrence whole through the most exposed window.',
      tasks: ['Transfer air, SOF, ISR and logistics enablers at C-Day', 'Confirm allied backfill of eFP / EAP', 'Movement order for BCT and CSG at D+30', 'Liaison at JFLCC/JFACC/JFMCC from C-Day'] },
    { title: 'Enablers and Staging Only', approach: 'Enable, do not commit', deps: [1, 5], s: 0.48, cas: 0.4, esc: 0.12, days: 30, res: 35, dps: 2,
      concept: 'EUCOM provides the pipeline — staging hubs, strategic lift coordination, ISR, cyber, IO and CBRN consequence management — without transferring combat formations; European posture stays intact.',
      tasks: ['Operate staging hubs and WRM draw-down', 'Deploy CBRN CM units for Udon Thani vicinity', 'J39 information operations in European media', 'Retain all combat forces in the European AOR'] },
    { title: 'Maritime and SOF Lead', approach: 'Sea-centric contribution', deps: [3, 6], s: 0.62, cas: 1.0, esc: 0.28, days: 50, res: 55, dps: 3,
      concept: 'Transfer the CSG/ARG, MEU and SOCEUR to JFMCC/JFSOCC for ASW, maritime interdiction and support to the RRLA resistance in Sungzon; retain the BCT and fighter wing in Europe.',
      tasks: ['CSG/ARG and MEU through Rota and Sigonella', 'ASW coordination against OPA Southern Fleet', 'SOF preparation of the environment with RRLA', 'Land and air forces hold European deterrence'] },
    { title: 'Full Package with NATO Backfill', approach: 'Surge and backfill', deps: [1, 2, 3], s: 0.76, cas: 1.7, esc: 0.2, days: 60, res: 90, dps: 4,
      concept: 'Full force package transfers by C-Day while allies backfill EAP, eFP and Mediterranean presence under a negotiated SACEUR arrangement; depends on assumptions A2 and A3 holding.',
      tasks: ['Negotiate allied backfill through SACEUR', 'Full OPCON transfer at C-Day', 'Allied QRA covers Enhanced Air Policing', 'Joint EUCOM–NATO StratCom on alliance cohesion'] }
  ];

  componentDidMount() { const v = this.props.startView, st = +this.props.startStep; if (v || st) this.setState({ view: v || 'coa', step: st || 1 }); }
  go(view) { this.setState({ view }); }
  goStep(step) { this.setState({ view: 'coa', step }); }
  rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  gauss(r) { const u = 1 - r(), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  level(v, th) { return v < th[0] ? 'Low' : v < th[1] ? 'Moderate' : v < th[2] ? 'Significant' : 'High'; }
  riskColor(l) { return { Low: ['rgb(19,57,41)', 'rgb(76,195,138)'], Moderate: ['rgb(63,34,0)', 'rgb(255,203,71)'], Significant: ['rgb(130,78,0)', 'rgb(254,243,221)'], High: ['rgb(174,25,85)', 'rgb(254,236,244)'] }[l]; }
  score(l) { return { Low: 4, Moderate: 3, Significant: 2, High: 1 }[l]; }

  buildCoas() {
    const t = this.THREATS[this.state.threat].name;
    return this.COA_LIB.slice(0, this.state.numCoas).map((c, i) => ({ ...c, n: i + 1, concept: c.concept.replace('adversary', t) }));
  }
  runSim() {
    const coas = this.state.coas.length ? this.state.coas : this.buildCoas();
    this.setState({ coas, simRunning: true, simProgress: 0, results: null, simStatus: 'Initializing red cell from JIPOE…' });
    const msgs = ['Initializing red cell from JIPOE…', 'Sampling adversary reactions…', 'Resolving engagements…', 'Scoring risk to mission, personnel, escalation…'];
    let p = 0;
    const tick = setInterval(() => {
      p += 6 + Math.random() * 8;
      if (p >= 100) { clearInterval(tick); this.setState({ simRunning: false, simProgress: 100, results: this.compute(coas) }); return; }
      this.setState({ simProgress: Math.round(p), simStatus: msgs[Math.min(3, Math.floor(p / 25))] });
    }, 120);
  }
  compute(coas, agOverride, nOverride, failIdx) {
    const { pirs, assumptions } = this.state; const N = nOverride || this.state.numSims, ag = agOverride ?? this.state.aggression;
    if (failIdx != null) coas = coas.map(c => (c.deps || []).includes(failIdx + 1) ? { ...c, s: c.s - 0.14, esc: c.esc + 0.08, cas: c.cas * 1.25 } : { ...c, s: c.s - 0.03 });
    const gaps = pirs.filter(p => p.status === 0).length;
    const aWeak = assumptions.reduce((a, x) => a + (x.status === 2 ? 0.04 : (100 - x.conf) / 1000), 0);
    const sd = 0.11 + gaps * 0.02 + aWeak;
    return coas.map((c, i) => {
      const r = this.rng(1000 + i * 77 + N);
      const bins = new Array(10).fill(0); const sc = [], cas = []; let esc = 0, major = 0;
      for (let k = 0; k < N; k++) {
        const s = Math.min(1, Math.max(0, c.s - 0.18 * (ag - 0.5) + this.gauss(r) * sd));
        sc.push(s); bins[Math.min(9, Math.floor(s * 10))]++;
        cas.push(Math.max(0, c.cas * (0.7 + 0.6 * ag) + this.gauss(r) * c.cas * 0.45));
        if (r() < c.esc + 0.35 * (ag - 0.5)) { esc++; if (r() < 0.35 + 0.4 * ag) major++; }
      }
      sc.sort((a, b) => a - b); cas.sort((a, b) => a - b);
      const pS = sc.filter(s => s >= 0.5).length / N, pE = esc / N, c90 = cas[Math.floor(N * 0.9)];
      const mx = Math.max(...bins);
      return { n: c.n, title: c.title, days: c.days, res: c.res,
        pSuccess: pS, pEsc: pE, pMajor: major / N, cas: c90,
        ci: `${Math.round(sc[Math.floor(N * 0.1)] * 100)}–${Math.round(sc[Math.floor(N * 0.9)] * 100)}`,
        bins: bins.map((b, j) => ({ h: Math.max(3, Math.round(b / mx * 100)), bg: j < 5 ? 'var(--color-accent-300)' : 'var(--color-accent-700)' })),
        rm: this.level(1 - pS, [0.15, 0.30, 0.50]), rp: this.level(c90, [1, 2, 4]), re: this.level(pE, [0.15, 0.30, 0.45]),
        rt: this.level(c.days, [30, 60, 100]), rr: this.level(c.res, [45, 65, 85]) };
    });
  }
  rankWith(w, results) {
    return results.map(r => ({ n: r.n, raw: w.mission * this.score(r.rm) + w.personnel * this.score(r.rp) + w.escalation * this.score(r.re) + w.time * this.score(r.rt) + w.resources * this.score(r.rr) })).sort((a, b) => b.raw - a.raw);
  }
  ranked() {
    const { results, weights: w } = this.state; if (!results) return [];
    const max = (w.mission + w.personnel + w.escalation + w.time + w.resources) * 4 || 1;
    return results.map(r => {
      const s = w.mission * this.score(r.rm) + w.personnel * this.score(r.rp) + w.escalation * this.score(r.re) + w.time * this.score(r.rt) + w.resources * this.score(r.rr);
      return { ...r, raw: s, pct: Math.round(s / max * 100), score: `${s} / ${max}` };
    }).sort((a, b) => b.raw - a.raw).map((r, i) => ({ ...r, rank: i + 1 }));
  }
  arcFor(r) {
    const t = this.THREATS[this.state.threat].name;
    const lib = {
      1: [['Transfer BCT, fighter wing and CSG to INDOPACOM OPCON at C-Day; open Ramstein, Rota, Sigonella, Lajes.', `${t} cyber attacks on European staging infrastructure; Russia announces snap exercises on the eastern flank.`, 'CYBERCOM hardens hubs; SACEUR raises eFP readiness.', 'DP1 · Transfer'], ['Forces complete JRSOI in the JOA by C+10.', `${t} shifts to defense-in-depth; nuclear signaling against MNFA staging ports.`, 'Disperse staging; CBRN posture; STRATCOM deterrence messaging.', 'DP2 · Posture'], ['EUCOM-contributed forces join Phase III Dominate.', 'Russia probes Baltic airspace; North Torbia mobilizes reserves.', 'Decide: accelerate redeployment or accept the deterrence gap.', 'DP3 · Deterrence gap']],
      2: [['Deploy enablers, SOF and fighter wing by C-Day; hold BCT and CSG pending backfill.', `${t} consolidates and attrits coalition will through hybrid attacks.`, 'Confirm NATO backfill; issue movement order for BCT at D+30.', 'DP1 · Backfill'], ['BCT and CSG transfer at D+30.', `${t} launches renewed offensive toward the Gulf of Khorathidin coast (MDCOA).`, 'MNFA requests acceleration; EUCOM compresses the timeline.', 'DP2 · Accelerate'], ['Full package in the JOA for Phase III.', 'Russia exercises near the Suwałki corridor.', 'Retain residual eFP; SACEUR reassurance measures.', 'DP3 · Reassure']],
      3: [['Activate hubs, ISR, logistics, IO and CBRN CM; no combat force transfer.', `${t} reads coalition hesitation; intensifies IO on coalition fractures.`, 'J39 counter-narrative; visible allied contributions.', 'DP1 · Narrative'], ['Sustain the pipeline for CONUS forces through Europe.', `${t} Southern Fleet interdicts Malacca approaches.`, 'NAVEUR ASW coordination support to JFMCC.', 'DP2 · Maritime'], ['MNFA short of combat power for Phase III.', `${t} holds gains; operational stalemate.`, 'Decide whether to transfer combat forces late.', 'DP3 · Commit']],
      4: [['Transfer CSG/ARG, MEU and SOCEUR by C-Day; retain land and air in Europe.', `${t} Yuan-class submarines contest the South Olvanan Sea.`, 'ASW campaign; mine countermeasures at Gulf approaches.', 'DP1 · ASW'], ['SOF enable RRLA resistance across 40 sites in Sungzon.', `${t} SPF brigades hunt the resistance; cyber attacks on CENTRIXS–MNFA.`, 'Harden coalition network; expand preparation of the environment.', 'DP2 · Resistance'], ['Amphibious operations in the Gulf of Khorathidin.', `${t} nuclear posturing against amphibious staging.`, 'Disperse ARG; STRATCOM signaling.', 'DP3 · WMD']],
      5: [['Full package transfer plus negotiated allied backfill of EAP and eFP.', 'Russia tests backfill credibility with Baltic air incursions.', 'Allied QRA responds; demonstrate alliance cohesion.', 'DP1 · Backfill test'], ['Forces integrate into JFLCC/JFACC/JFMCC.', `${t} hybrid campaign against European public opinion.`, 'J39 counter-narrative with NATO StratCom.', 'DP2 · Narrative'], ['Phase III Dominate with full EUCOM contribution.', `${t} renewed offensive; further WMD strike threat.`, 'CBRN CM units deploy to the Udon Thani vicinity.', 'DP3 · CBRN']]
    };
    return (lib[r] || lib[1]).map((a, i) => ({ turn: (i + 1) * 3, action: a[0], reaction: a[1], counter: a[2], dp: a[3] }));
  }
  sensitivity(ranked, best, crit) {
    const s = this.state, res = s.results; if (!res || !best) return { explain: [], explainText: '', runnerUp: {}, stability: [], stabilityText: '', tornado: [], sweep: [], sweepText: '', assumptionRisk: [], assumptionText: '' };
    const w = s.weights, keys = ['mission', 'personnel', 'escalation', 'time', 'resources'], lv = { mission: 'rm', personnel: 'rp', escalation: 're', time: 'rt', resources: 'rr' };
    const runner = ranked[1] || ranked[0];
    const explain = crit.map(([k, label]) => { const b = w[k] * this.score(best[lv[k]]), o = w[k] * this.score(runner[lv[k]]), mx = w[k] * 4 || 1; const d = b - o; return { label, bestW: Math.round(b / mx * 50), otherW: Math.round(o / mx * 50), delta: (d > 0 ? '+' : '') + d, color: d > 0 ? 'rgb(76,195,138)' : d < 0 ? 'rgb(255,120,120)' : 'var(--color-neutral-600)' }; });
    const gains = explain.filter(x => x.delta.startsWith('+')).map(x => x.label.toLowerCase()), losses = explain.filter(x => x.delta.startsWith('-')).map(x => x.label.toLowerCase());
    const explainText = `COA ${best.n} leads COA ${runner.n} by ${best.raw - runner.raw} weighted points. The margin comes from ${gains.length ? gains.join(', ') : 'no single criterion'}${losses.length ? '; it gives ground on ' + losses.join(', ') : ''}. Each bar is weight × JRAM score (Low 4 … High 1).`;
    const r = this.rng(4242); const wins = {}; res.forEach(x => wins[x.n] = 0);
    for (let i = 0; i < 500; i++) { const pw = {}; keys.forEach(k => pw[k] = Math.max(0, Math.min(5, w[k] + Math.round((r() - 0.5) * 4)))); wins[this.rankWith(pw, res)[0].n]++; }
    const stability = res.map(x => ({ n: x.n, pct: Math.round(wins[x.n] / 5), bg: x.n === best.n ? 'var(--color-accent)' : 'rgb(100,116,139)' })).sort((a, b) => b.pct - a.pct);
    const stabilityText = stability[0].pct >= 75 ? `Robust: COA ${stability[0].n} ranks first in ${stability[0].pct}% of perturbed weightings.` : `Fragile: the top rank shifts between COA ${stability[0].n} and COA ${stability[1] ? stability[1].n : '-'} depending on weights — the commander's priorities decide.`;
    const flip = n => n === best.n ? ['rgb(19,57,41)', 'rgb(76,195,138)'] : ['rgb(174,25,85)', 'rgb(254,236,244)'];
    const tornado = crit.map(([k, label]) => { const lo = this.rankWith({ ...w, [k]: Math.max(0, w[k] - 2) }, res)[0].n, hi = this.rankWith({ ...w, [k]: Math.min(5, w[k] + 2) }, res)[0].n; return { label, lo, hi, loBg: flip(lo)[0], loFg: flip(lo)[1], hiBg: flip(hi)[0], hiFg: flip(hi)[1] }; });
    const coas = s.coas.length ? s.coas : this.buildCoas();
    const sw = [0.2, 0.5, 0.85].map(ag => this.compute(coas, ag, 400));
    const sweep = coas.map((c, i) => ({ n: c.n, lo: Math.round(sw[0][i].pSuccess * 100), mid: Math.round(sw[1][i].pSuccess * 100), hi: Math.round(sw[2][i].pSuccess * 100) }));
    const bestSw = sweep.find(x => x.n === best.n) || sweep[0]; const mostRobust = [...sweep].sort((a, b) => (a.lo - a.hi) - (b.lo - b.hi))[0];
    const sweepText = `COA ${best.n} loses ${bestSw.lo - bestSw.hi} points of success probability from restrained to aggressive adversary behavior${mostRobust.n === best.n ? ', and it is also the most robust option across the sweep.' : `; COA ${mostRobust.n} degrades least (${mostRobust.lo - mostRobust.hi}).`}`;
    const assumptionRisk = s.assumptions.map((a, i) => ({ n: i + 1, text: a.text, conf: a.conf, status: this.A_STATUS[a.status][0], bg: this.A_STATUS[a.status][1], fg: this.A_STATUS[a.status][2] })).sort((a, b) => a.conf - b.conf);
    const weak = assumptionRisk.filter(a => a.conf < 70 || a.status !== 'Valid');
    const sigma = Math.round(s.assumptions.reduce((a, x) => a + (x.status === 2 ? 0.04 : (100 - x.conf) / 1000), 0) * 100);
    const assumptionText = weak.length ? `${weak.length} assumption(s) below 70% confidence or unvalidated widen every outcome distribution by ~${sigma} points of σ. Validate A${weak[0].n} first — it has the lowest confidence.` : 'All assumptions validated at high confidence; uncertainty is driven by collection gaps only.';
    return { explain, explainText, runnerUp: { n: runner.n, title: runner.title }, stability, stabilityText, tornado, sweep, sweepText, assumptionRisk, assumptionText };
  }
  evaluation(ranked, best, coas, isWeak) {
    const s = this.state; if (!best) return { evalGrade: {}, evalSummary: '', evalStats: [], evalGaps: [], evalRisks: [], evalConditions: [] };
    const c = coas.find(x => x.n === best.n) || {}; const deps = (c.deps || []).map(i => s.assumptions[i - 1] && { i, a: s.assumptions[i - 1] }).filter(Boolean);
    const weakDeps = deps.filter(d => isWeak(d.a)); const openPirs = s.pirs.filter(p => p.status !== 2); const gapsPirs = s.pirs.filter(p => p.status === 0);
    const sens = this.sensitivity(ranked, best, [['mission', 'Risk to mission'], ['personnel', 'Risk to personnel'], ['escalation', 'Risk of escalation'], ['time', 'Time to end state'], ['resources', 'Force demand vs GFM']]);
    const stab = (sens.stability.find(x => x.n === best.n) || {}).pct || 0; const sw = sens.sweep.find(x => x.n === best.n) || { lo: 0, hi: 0 };
    const worstProp = deps.map(d => { const alt = this.compute(coas, undefined, 300, d.i - 1); const base = s.results.find(r => r.n === best.n); const a = alt.find(r => r.n === best.n); return { i: d.i, drop: Math.round((base.pSuccess - a.pSuccess) * 100) }; }).sort((a, b) => b.drop - a.drop)[0] || { i: 0, drop: 0 };
    const score = (stab >= 75 ? 2 : stab >= 50 ? 1 : 0) + (weakDeps.length === 0 ? 2 : weakDeps.length === 1 ? 1 : 0) + (best.re === 'Low' || best.re === 'Moderate' ? 1 : 0) + (gapsPirs.length === 0 ? 1 : 0);
    const grade = score >= 5 ? ['High', 'rgb(19,57,41)', 'rgb(76,195,138)'] : score >= 3 ? ['Moderate', 'rgb(63,34,0)', 'rgb(255,203,71)'] : ['Low', 'rgb(174,25,85)', 'rgb(254,236,244)'];
    const runner = ranked[1];
    return {
      evalGrade: { label: grade[0], bg: grade[1], fg: grade[2] },
      evalSummary: `COA ${best.n} ranks first at ${best.pct}% of the weighted maximum with P(success) ${Math.round(best.pSuccess * 100)}% across ${s.numSims} wargame iterations${runner ? `, ahead of COA ${runner.n} (${runner.pct}%)` : ''}. It holds the top rank in ${stab}% of perturbed weightings and rests on ${deps.length} load-bearing assumption${deps.length === 1 ? '' : 's'}, ${weakDeps.length} of which ${weakDeps.length === 1 ? 'is' : 'are'} below threshold. ${openPirs.length} collection requirement${openPirs.length === 1 ? '' : 's'} remain open. Confidence in the recommendation is ${grade[0].toLowerCase()}.`,
      evalStats: [
        { label: 'Weighted score', value: `${best.pct}%`, note: `Rank #1 of ${ranked.length}`, color: 'var(--color-text)' },
        { label: 'Rank stability', value: `${stab}%`, note: 'of perturbed weightings', color: stab >= 75 ? 'rgb(76,195,138)' : 'rgb(255,203,71)' },
        { label: 'Thin evidence', value: `${weakDeps.length} / ${deps.length}`, note: 'load-bearing claims weak', color: weakDeps.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)' },
        { label: 'Open collection', value: String(openPirs.length), note: `${gapsPirs.length} untasked gap${gapsPirs.length === 1 ? '' : 's'}`, color: gapsPirs.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)' },
        { label: 'Worst propagation', value: `−${worstProp.drop} pts`, note: worstProp.i ? `if A${worstProp.i} fails` : 'no dependencies', color: worstProp.drop >= 10 ? 'rgb(255,120,120)' : 'rgb(255,203,71)' }
      ],
      evalGaps: [...weakDeps.map(d => `A${d.i} (${d.a.conf}% · ${this.A_STATUS[d.a.status][0]}${/expire/i.test(d.a.valid || '') ? ' · validity expiring' : ''}): ${d.a.text.split(/[,;—]/)[0]}.`), ...gapsPirs.map((p, k) => `PIR ${s.pirs.indexOf(p) + 1} untasked: ${p.q}`)].slice(0, 5).concat(weakDeps.length + gapsPirs.length === 0 ? ['No open gaps affect the recommended option.'] : []),
      evalRisks: [`Risk to mission ${best.rm} — P(failure) ${Math.round((1 - best.pSuccess) * 100)}%.`, `Risk to personnel ${best.rp} — p90 casualties ${best.cas.toFixed(1)}% of committed force.`, `Risk of escalation ${best.re} — P(escalation) ${Math.round(best.pEsc * 100)}%, ${Math.round(best.pMajor * 100)}% beyond theater.`, `Adversary behavior: P(success) falls from ${sw.lo}% (restrained) to ${sw.hi}% (aggressive).`],
      evalConditions: [worstProp.i ? `Validate A${worstProp.i} before C-Day; its failure costs COA ${best.n} ${worstProp.drop} points of success probability.` : 'No single assumption failure degrades the option materially.', openPirs.length ? `Close ${openPirs.length} open collection requirement${openPirs.length === 1 ? '' : 's'} to narrow outcome distributions before execution.` : 'Collection complete; outcome distributions at minimum width.', `Decision points DP1–DP3 in the wargame ARC table define branch triggers${runner ? `; COA ${runner.n} is the ready alternative` : ''}.`, best.re === 'Significant' || best.re === 'High' ? 'Escalation risk requires SecDef-level review of targets and STRATCOM deterrence messaging.' : 'Escalation risk within theater tolerance; maintain STRATCOM signaling.']
    };
  }
  decide(status) {
    const rk = this.ranked(); const ch = rk.find(r => r.n === (this.state.chosen ?? rk[0]?.n)) || rk[0]; if (!ch) return;
    this.setState({ decision: { status, n: ch.n, title: ch.title, risk: `Mission ${ch.rm} · Personnel ${ch.rp} · Escalation ${ch.re}`, time: new Date().toLocaleString(), note: this.state.decisionNote, hasNote: !!this.state.decisionNote } });
  }

  renderVals() {
    const s = this.state, T = this.THREATS[s.threat];
    const on = ['var(--color-accent)', 'var(--color-accent)', '#fff'], off = ['var(--color-divider)', 'transparent', 'var(--color-text)'];
    const navItem = (id, label, view) => ({ label, go: () => this.go(view), opacity: 1, border: s.view === view ? 'rgb(30,41,59)' : 'transparent', dot: s.view === view ? 'var(--color-accent-700)' : 'transparent' });
    const planLabel = `${s.ccmd} ${{ OPORD: 'OPORD 26-002', CCP: 'CCP', CON: 'CONPLAN', GCP: 'GCP', FCP: 'FCP', SPF: 'SPF' }[s.planType]}`;
    const stage = s.view === 'coa' ? (s.step === 3 ? 3 : s.step === 5 ? 4 : 1) : ['collection', 'rfi'].includes(s.view) ? 2 : ['intel', 'docs', 'posture'].includes(s.view) ? 5 : 0;
    const isWeak = a => a.conf < 70 || a.status !== 0 || /expire/i.test(a.valid || '');
    const coasNow = s.coas.length ? s.coas : this.buildCoas();
    const ranked = this.ranked();
    const results = s.results ? s.results.map(r => ({ ...r, sims: s.numSims, select: () => this.setState({ sel: r.n - 1 }),
      outline: s.sel === r.n - 1 ? '2px solid var(--color-accent)' : 'none',
      pSuccess: Math.round(r.pSuccess * 100), pEsc: Math.round(r.pEsc * 100), pMajor: Math.round(r.pMajor * 100), cas: r.cas.toFixed(1),
      risks: [['Risk to mission', r.rm], ['Risk to personnel', r.rp], ['Risk of escalation', r.re]].map(([label, level]) => ({ label, level, bg: this.riskColor(level)[0], fg: this.riskColor(level)[1] })) })) : [];
    const cell = (level, detail) => ({ level, detail, bg: this.riskColor(level)[0], fg: this.riskColor(level)[1] });
    const crit = [['mission', 'Risk to mission', r => cell(r.rm, `P(fail) ${Math.round((1 - r.pSuccess) * 100)}%`)], ['personnel', 'Risk to personnel', r => cell(r.rp, `p90 casualties ${r.cas.toFixed(1)}%`)], ['escalation', 'Risk of escalation', r => cell(r.re, `P(esc) ${Math.round(r.pEsc * 100)}%`)], ['time', 'Time to end state', r => cell(r.rt, `${r.days} days`)], ['resources', 'Force demand vs GFM', r => cell(r.rr, `${r.res}% of allocated`)]];
    const best = ranked[0]; const worstRisk = best ? [['mission', best.rm], ['personnel', best.rp], ['escalation', best.re]].sort((a, b) => this.score(a[1]) - this.score(b[1]))[0] : null;
    const sel = s.results ? s.results[s.sel] || s.results[0] : null;
    const chosenR = ranked.find(r => r.n === s.chosen) || best || {};
    const statusMap = { 0: ['Gap', 'rgb(174,25,85)', 'rgb(254,236,244)'], 1: ['Collecting', 'rgb(130,78,0)', 'rgb(254,243,221)'], 2: ['Answered', 'rgb(35,110,74)', 'rgb(229,251,235)'] };
    const rfiColor = { Open: ['rgb(174,25,85)', 'rgb(254,236,244)'], Pending: ['rgb(130,78,0)', 'rgb(254,243,221)'], Answered: ['rgb(35,110,74)', 'rgb(229,251,235)'] };
    const set = k => e => this.setState({ [k]: e.target.value });
    const defaultWorld = s.threat === 'OLV'
      ? `Scenario: ${this.SCENARIOS[s.scenario].label}. USEUCOM is the supporting combatant command to USINDOPACOM for Operation ENDURING PHOENIX (UNSCR 2781). Olvana has invaded Sungzon and Khorathidin and employed three low-yield nuclear weapons against Khorathidin's 5th Infantry Division at Udon Thani on 14 MAR 2026. The OPA fields three theater formations plus the Southern Fleet; nuclear contamination near Udon Thani and the southwest monsoon (APR–SEP) constrain movement. C-Day 10 APR 2026, D-Day 15 MAY 2026. Russia and North Torbia may exploit the drawdown of US forces from the European theater.`
      : `Scenario: ${this.SCENARIOS[s.scenario].label}. ${s.ccmd} is supporting a ${planLabel.toLowerCase()} against ${T.label}. ${T.desc} Indications from the last 72 hours show force concentration and readiness increases consistent with the JIPOE most-likely COA. Allied posture is defensive; civilian shipping remains in the area. Weather window favorable for the next 10 days.`;
    const B = window.BRANDING;
    return {
      brandMark: B.teamMark, brandTitle: B.title, brandProduct: B.productName,
      crumb: { coa: s.step === 3 ? 'Predictive Interconnected Risk Engine' : 'Strategy Option Evaluation', docs: 'Foundational Data Ingestion / Plans & Guidance', intel: 'Foundational Data Ingestion / Intelligence', collection: 'Collection Management Agent', rfi: 'Collection Management Agent / RFIs', posture: 'Foundational Data Ingestion / Force Posture', doctrine: 'Doctrine' }[s.view],
      showWorkflow: s.view !== 'doctrine',
      isCoa: s.view === 'coa', isIntel: s.view === 'intel', isCollection: s.view === 'collection', isRfi: s.view === 'rfi', isPosture: s.view === 'posture', isDoctrine: s.view === 'doctrine',
      stages: [['Strategy Option Evaluation', 'Scores courses of action against their assumptions and shows exactly where the analysis stands on thin evidence.', 1], ['Collection Management Agent', 'Turns weak assumptions into draft collection requirements: tagged, routed, tracked. Scores re-run as collection returns.', 2], ['Predictive Interconnected Risk Engine', 'Reads the graph\'s edges and propagates: which option degrades if this assumption fails, and how far it travels.', 3], ['Option Recommendation', 'Strategy evaluation taking in every gap and risk; offers the Commander a recommended option and the risk accepted.', 4]].map(([label, sub, n]) => { const active = stage === n; const done = n === 1 ? !!s.results : n === 2 ? s.pirs.every(p => p.status === 2) : n === 3 ? !!s.results : !!s.decision; return { n, label, sub, lineShow: n < 4 ? 'block' : 'none', go: () => n === 1 ? this.setState({ view: 'coa', step: [1, 2, 4].includes(s.step) ? s.step : 1 }) : n === 2 ? this.go('collection') : n === 3 ? this.setState({ view: 'coa', step: 3 }) : this.setState({ view: 'coa', step: 5 }), ring: active || done ? 'var(--color-accent)' : 'var(--color-divider)', bg: active ? 'rgb(16,42,76)' : done ? 'rgb(9,84,165)' : 'var(--color-surface)', fg: active || done ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: active ? 1 : 0.65 }; }),
      foundation: { go: () => this.go('intel'), ring: stage === 5 ? 'var(--color-accent)' : 'var(--color-divider)', bg: stage === 5 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: stage === 5 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', stat: `${s.assumptions.length + s.intel.length} claims · ${s.intel.length} reports · ${s.planDocs.length + s.guideDocs.length} documents` },
      hasSubtabs: stage === 1 || stage === 5,
      subtabs: stage === 1 ? [['Setup', 1], ['Options', 2], ['Score', 4]].map(([label, st]) => ({ label, go: () => this.goStep(st), line: s.step === st ? 'var(--color-accent)' : 'transparent', opacity: s.step === st ? 1 : 0.65 })) : [['Intelligence', 'intel'], ['Plans & Strategic Guidance', 'docs'], ['Force Posture & GFM', 'posture']].map(([label, v]) => ({ label, go: () => this.go(v), line: s.view === v ? 'var(--color-accent)' : 'transparent', opacity: s.view === v ? 1 : 0.65 })),
      step1: s.step === 1, step2: s.step === 2, step3: s.step === 3, step4: s.step === 4, step5: s.step === 5,
      globalNav: [],
      sections: [
        { hasLabel: true, label: 'Workflow', items: [{ ...navItem('coa', 'Strategy Option Evaluation', 'coa'), border: stage === 1 ? 'rgb(30,41,59)' : 'transparent', dot: stage === 1 ? 'var(--color-accent-700)' : 'transparent', go: () => this.setState({ view: 'coa', step: [1, 2, 4].includes(s.step) ? s.step : 1 }) }, navItem('collection', 'Collection Management Agent', 'collection'), { ...navItem('coa', 'Predictive Risk Engine', 'coa'), border: stage === 3 ? 'rgb(30,41,59)' : 'transparent', dot: stage === 3 ? 'var(--color-accent-700)' : 'transparent', go: () => this.setState({ view: 'coa', step: 3 }) }, { ...navItem('coa', 'Option Recommendation', 'coa'), border: stage === 4 ? 'rgb(30,41,59)' : 'transparent', dot: stage === 4 ? 'var(--color-accent-700)' : 'transparent', go: () => this.setState({ view: 'coa', step: 5 }) }] },
        { hasLabel: true, label: 'Foundational Data Ingestion', items: [navItem('intel', 'Intelligence', 'intel'), navItem('docs', 'Plans & Strategic Guidance', 'docs'), navItem('posture', 'Force Posture & GFM', 'posture'), navItem('rfi', 'RFI Management', 'rfi')] },
        { hasLabel: true, label: 'Reference', items: [navItem('doctrine', 'Doctrine', 'doctrine')] }
      ],
      planLabel, ccmd: s.ccmd, threatName: T.name, runId: s.runId,
      resetRun: () => this.setState({ step: 1, coas: [], results: null, decision: null, chosen: null, runId: 'R-' + String(400 + Math.floor(Math.random() * 500)).padStart(4, '0') }),
      steps: [['Strategy Preparation', 'Mission Analysis & Guidance'], ['Development', 'Concepts & Screening'], ['Option Adjudication', 'Wargames · ARC'], ['Option\nComparison', 'Decision Matrix'], ['Strategy Decision', "Commander's decision"]].map(([label, sub], i) => ({ n: i + 1, label, sub, go: () => this.goStep(i + 1),
        lineShow: i < 4 ? 'block' : 'none', ring: s.step >= i + 1 ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.step > i + 1 ? 'rgb(9,84,165)' : s.step === i + 1 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: s.step >= i + 1 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: s.step === i + 1 ? 1 : 0.6 })),
      planTypes: this.PLAN_TYPES.map(p => { const a = s.planType === p.id ? on : off; return { ...p, pick: () => this.setState({ planType: p.id }), border: a[0], bg: a[1], fg: a[2] }; }),
      isContingency: s.planType === 'CON', levels: this.LEVELS.map((l, i) => ({ label: `L${i + 1}`, on: s.level === i + 1, pick: () => this.setState({ level: i + 1 }) })), levelDesc: this.LEVELS[s.level - 1],
      ccmds: Object.keys(this.CCMDS).map(c => { const a = s.ccmd === c ? on : off; return { label: c, pick: () => this.setState({ ccmd: c }), border: a[0], bg: a[1], fg: a[2] }; }), ccmdDesc: this.CCMDS[s.ccmd],
      threats: Object.keys(this.THREATS).map(k => { const a = s.threat === k ? on : off; return { label: this.THREATS[k].label, pick: () => this.setState({ threat: k, coas: [], results: null }), border: a[0], bg: a[1], fg: a[2] }; }), threatDesc: T.desc,
      intelCount: s.intel.length, worldState: s.worldState || defaultWorld, onWorldState: set('worldState'),
      intent: s.intent || (s.threat === 'OLV' ? s.planDocs[0].intent : `Deter ${T.name} aggression against allies and partners; if deterrence fails, deny ${T.name} its objectives while limiting escalation beyond the theater and preserving the force for a prolonged campaign.`), onIntent: set('intent'),
      endState: s.endState || (s.threat === 'OLV' ? s.planDocs[0].endState : `${T.name} force projection halted; allied territory and sea lines of communication secure; conditions set for a negotiated settlement.`), onEndState: set('endState'),
      assumptions: s.assumptions.map((a, i) => ({ n: i + 1, text: a.text, conf: a.conf, link: a.link ? 'Tracked via ' + a.link : 'Unlinked', status: this.A_STATUS[a.status][0], bg: this.A_STATUS[a.status][1], fg: this.A_STATUS[a.status][2],
        remove: () => this.setState({ assumptions: s.assumptions.filter((_, j) => j !== i) }),
        cycle: () => this.setState({ assumptions: s.assumptions.map((x, j) => j === i ? { ...x, status: (x.status + 1) % 3 } : x), results: null }),
        setConf: e => this.setState({ assumptions: s.assumptions.map((x, j) => j === i ? { ...x, conf: +e.target.value } : x), results: null }) })),
      assumptionSummary: `${s.assumptions.filter(a => a.status === 0).length} valid · ${s.assumptions.filter(a => a.status === 1).length} under review · ${s.assumptions.filter(a => a.status === 2).length} invalidated`,
      scenarios: this.SCENARIOS.map((sc, i) => ({ ...sc, pick: () => this.setState({ scenario: i, aggression: sc.ag, results: null, worldState: '' }), border: s.scenario === i ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.scenario === i ? 'rgb(16,36,62)' : 'transparent' })),
      newAssumption: s.newAssumption, onNewAssumption: set('newAssumption'),
      addAssumption: () => s.newAssumption.trim() && this.setState({ assumptions: [...s.assumptions, { text: s.newAssumption.trim(), status: 1, conf: 50, link: '' }], newAssumption: '' }),
      onAssumptionKey: e => { if (e.key === 'Enter' && s.newAssumption.trim()) this.setState({ assumptions: [...s.assumptions, { text: s.newAssumption.trim(), status: 1, conf: 50, link: '' }], newAssumption: '' }); },
      constraints: s.constraints.map((c, i) => ({ code: `${c.kind}${s.constraints.slice(0, i + 1).filter(x => x.kind === c.kind).length}`, text: c.text, remove: () => this.setState({ constraints: s.constraints.filter((_, j) => j !== i) }) })),
      constraintKinds: [['C', 'Constraint'], ['R', 'Restraint']].map(([k, label]) => ({ label, on: s.constraintKind === k, pick: () => this.setState({ constraintKind: k }) })),
      constraintPlaceholder: s.constraintKind === 'C' ? 'Add constraint (something the commander must do)' : 'Add restraint (something the commander must not do)',
      newConstraint: s.newConstraint, onNewConstraint: set('newConstraint'),
      addConstraint: () => s.newConstraint.trim() && this.setState({ constraints: [...s.constraints, { kind: s.constraintKind, text: s.newConstraint.trim() }], newConstraint: '' }),
      onConstraintKey: e => { if (e.key === 'Enter' && s.newConstraint.trim()) this.setState({ constraints: [...s.constraints, { kind: s.constraintKind, text: s.newConstraint.trim() }], newConstraint: '' }); },
      coaCounts: [2, 3, 4, 5].map(k => ({ label: String(k), on: s.numCoas === k, pick: () => this.setState({ numCoas: k, coas: [], results: null }) })),
      numSims: s.numSims, onNumSims: e => this.setState({ numSims: +e.target.value, results: null }),
      aggressionPct: Math.round(s.aggression * 100), onAggression: e => this.setState({ aggression: +e.target.value / 100, results: null }),
      aggressionLabel: s.aggression < 0.34 ? 'restrained' : s.aggression < 0.67 ? 'moderate' : 'aggressive',
      startDevelopment: () => this.setState({ coas: this.buildCoas(), step: 2, results: null }),
      coas: (s.coas.length ? s.coas : this.buildCoas()).map(c => ({ ...c, screen: ['Feasible', 'Acceptable', 'Suitable', 'Distinguishable', 'Complete'].map((l, i) => { const warn = (c.res > 85 && i === 0) || (c.esc > 0.5 && i === 1) || (c.s < 0.5 && i === 2); return { label: l, bg: warn ? 'rgb(130,78,0)' : 'rgb(19,57,41)', fg: warn ? 'rgb(254,243,221)' : 'rgb(76,195,138)' }; }) })),
      coaCount: s.numCoas,
      startWargame: () => { this.setState({ step: 3 }); if (!s.results) setTimeout(() => this.runSim(), 200); },
      runSim: () => this.runSim(), runLabel: s.results ? 'Re-run Wargame' : 'Run Wargame',
      simRunning: s.simRunning, simProgress: s.simProgress, simStatus: s.simStatus,
      hasResults: !!s.results && !s.simRunning, noResults: !s.results,
      results, selN: sel ? sel.n : '', selTitle: sel ? sel.title : '', arc: sel ? this.arcFor(sel.n) : [],
      goCompare: () => this.setState({ step: 4 }), goApprove: () => this.setState({ step: 5 }),
      ...this.evaluation(ranked, best, coasNow, isWeak),
      matrix: crit.map(([k, label, fn]) => ({ label, weight: s.weights[k], setWeight: e => this.setState({ weights: { ...s.weights, [k]: +e.target.value } }), cells: (s.results || []).map(fn) })),
      ranked: (s.results || []).map(r => { const rk = ranked.find(x => x.n === r.n); const isCh = (s.chosen ?? best?.n) === r.n; return { ...rk, riskLine: `Mission ${rk.rm} · Personnel ${rk.rp} · Escalation ${rk.re}`, choose: () => this.setState({ chosen: r.n }), chooseBg: isCh ? 'color-mix(in srgb,var(--color-accent) 8%,transparent)' : 'transparent', chooseBorder: isCh ? 'var(--color-accent)' : 'var(--color-divider)' }; }),
      best: best ? { n: best.n, title: best.title, reason: `Highest weighted score (${best.pct}%) across ${s.numSims} iterations: P(success) ${Math.round(best.pSuccess * 100)}% with ${best.re.toLowerCase()} escalation risk and p90 casualties of ${best.cas.toFixed(1)}%. Weights reflect commander's emphasis on mission and escalation.`, riskAccepted: worstRisk ? `${worstRisk[1]} risk to ${worstRisk[0]} is the governing risk; mitigated through the decision points in the ARC table and the branch plans identified in wargaming.` : '' } : { n: '', title: '', reason: '', riskAccepted: '' },
      ...this.sensitivity(ranked, best, crit),
      weakCount: s.assumptions.filter(isWeak).length,
      evidence: ranked.map(r => { const c = coasNow.find(x => x.n === r.n) || {}; const deps = (c.deps || []).filter(i => s.assumptions[i - 1]).map(i => { const a = s.assumptions[i - 1]; const w = isWeak(a); return { n: i, short: a.text.split(/[,;—]/)[0].slice(0, 70), conf: a.conf, status: this.A_STATUS[a.status][0], bg: w ? this.A_STATUS[a.status === 0 ? 1 : a.status][1] : this.A_STATUS[0][1], fg: w ? this.A_STATUS[a.status === 0 ? 1 : a.status][2] : this.A_STATUS[0][2] }; }); const weak = deps.filter(d => isWeak(s.assumptions[d.n - 1])); return { n: r.n, title: r.title, rank: r.rank, deps, border: r.rank === 1 ? 'var(--color-accent)' : 'var(--color-divider)', verdict: weak.length ? `Stands on thin evidence: ${weak.map(d => 'A' + d.n).join(', ')} ${weak.length === 1 ? 'is' : 'are'} below threshold.` : 'All load-bearing claims validated.', verdictColor: weak.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)' }; }),
      sendWeakToCollection: () => { const existing = new Set(s.pirs.map(p => p.assumption).filter(x => x != null)); const add = s.assumptions.map((a, i) => [a, i]).filter(([a, i]) => isWeak(a) && !existing.has(i)).map(([a, i]) => ({ q: 'Validate: ' + a.text, ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], reports: 0, ltiov: (a.valid || '').replace('Expires ', '') || 'TBD', status: 0, assumption: i })); this.setState({ pirs: [...s.pirs, ...add], view: 'collection' }); },
      weakList: s.assumptions.map((a, i) => ({ a, i })).filter(({ a }) => isWeak(a)).map(({ a, i }) => { const cr = s.pirs.findIndex(p => p.assumption === i); return { n: i + 1, text: a.text, link: a.link || 'unsourced', valid: a.valid || 'unspecified', conf: a.conf, status: this.A_STATUS[a.status][0], bg: this.A_STATUS[a.status][1], fg: this.A_STATUS[a.status][2], bearing: coasNow.filter(c => (c.deps || []).includes(i + 1)).map(c => 'COA ' + c.n).join(', ') || 'no option', hasCr: cr >= 0, noCr: cr < 0, crLabel: cr >= 0 ? `PIR ${cr + 1} · ${['Gap', 'Collecting', 'Answered'][s.pirs[cr].status]}` : '', draft: () => this.setState({ pirs: [...s.pirs, { q: 'Validate: ' + a.text, ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], reports: 0, ltiov: (a.valid || '').replace('Expires ', '') || 'TBD', status: 0, assumption: i }] }) }; }),
      noWeak: !s.assumptions.some(isWeak),
      failToggles: s.assumptions.map((a, i) => ({ label: `A${i + 1} fails`, pick: () => this.setState({ failIdx: s.failIdx === i ? null : i }), border: s.failIdx === i ? 'rgb(255,120,120)' : 'var(--color-divider)', bg: s.failIdx === i ? 'rgb(60,20,35)' : 'transparent' })),
      hasFail: s.failIdx != null && !!s.results, failN: (s.failIdx ?? 0) + 1, failText: s.failIdx != null ? s.assumptions[s.failIdx].text : '',
      ...(s.failIdx != null && s.results ? (() => { const alt = this.compute(coasNow, undefined, 600, s.failIdx); const propagation = s.results.map((r, i) => { const d = Math.round((alt[i].pSuccess - r.pSuccess) * 100); const shifts = [['Mission', r.rm, alt[i].rm], ['Personnel', r.rp, alt[i].rp], ['Escalation', r.re, alt[i].re]].filter(x => x[1] !== x[2]).map(x => `${x[0]} ${x[1]} → ${x[2]}`); return { n: r.n, title: r.title, delta: (d > 0 ? '+' : '') + d + ' pts', color: d < -5 ? 'rgb(255,120,120)' : d < 0 ? 'rgb(255,203,71)' : 'var(--color-neutral-600)', riskShift: shifts.join(' · ') || 'Risk levels unchanged' }; }); const sets = (this.PROBLEM_SETS[s.failIdx] || ['Force flow']); const problemSets = sets.map((label, k) => ({ label, hop: k === 0 ? 'Direct' : `${k} hop${k > 1 ? 's' : ''}`, w: Math.max(14, 60 - k * 18), bg: k === 0 ? 'rgb(255,120,120)' : k === 1 ? 'rgb(255,203,71)' : 'rgb(100,116,139)' })); const hit = propagation.filter(p => p.delta.startsWith('-') && parseInt(p.delta) <= -5); return { propagation, problemSets, propagationText: `${hit.length} of ${propagation.length} options degrade materially; the effect reaches ${sets.length} problem set${sets.length > 1 ? 's' : ''} through the graph's edges.` }; })() : { propagation: [], problemSets: [], propagationText: '' }),
      claimCount: s.assumptions.length + s.intel.length,
      claims: [...s.assumptions.map((a, i) => ({ text: a.text, type: 'Assumption', source: a.link || 'unsourced', valid: a.valid || 'unspecified', conf: a.conf, bg: this.A_STATUS[isWeak(a) ? (a.status === 0 ? 1 : a.status) : 0][1], fg: this.A_STATUS[isWeak(a) ? (a.status === 0 ? 1 : a.status) : 0][2], edges: (coasNow.filter(c => (c.deps || []).includes(i + 1)).map(c => 'COA ' + c.n).concat(s.pirs.map((p, k) => p.assumption === i ? 'PIR ' + (k + 1) : null).filter(Boolean)).join(', ')) || '—' })), ...s.intel.map(r => { const conf = { A: 90, B: 75, C: 55, D: 40, E: 25, F: 30 }[r.rel[0]] || 50; return { text: r.title, type: r.type, source: r.rel, valid: r.when === 'just now' ? '72 h from receipt' : '72 h from ' + r.when, conf, bg: conf >= 70 ? this.A_STATUS[0][1] : this.A_STATUS[1][1], fg: conf >= 70 ? this.A_STATUS[0][2] : this.A_STATUS[1][2], edges: 'PIR ' + r.pir }; })],
      tradeoffs: ranked.length ? [
        `Fastest to end state: COA ${[...ranked].sort((a, b) => a.days - b.days)[0].n} (${[...ranked].sort((a, b) => a.days - b.days)[0].days} days) — ${['Significant', 'High'].includes([...ranked].sort((a, b) => a.days - b.days)[0].re) ? 'but carries' : 'and carries'} ${[...ranked].sort((a, b) => a.days - b.days)[0].re.toLowerCase()} escalation risk.`,
        `Lowest risk to personnel: COA ${[...ranked].sort((a, b) => a.cas - b.cas)[0].n} (p90 ${[...ranked].sort((a, b) => a.cas - b.cas)[0].cas.toFixed(1)}% casualties) at the cost of a ${Math.round([...ranked].sort((a, b) => a.cas - b.cas)[0].pSuccess * 100)}% success probability.`,
        `${s.pirs.filter(p => p.status === 0).length} unanswered PIR(s) widen every outcome distribution; closing them narrows the confidence intervals before approval.`
      ] : [],
      chosen: chosenR, decisionNote: s.decisionNote, onDecisionNote: set('decisionNote'),
      approve: () => this.decide('Approved'), approveMod: () => this.decide('Approved with modifications'), returnRework: () => this.decide('Returned for rework'),
      hasDecision: !!s.decision, noDecision: !s.decision, decision: s.decision || {},
      isDocs: s.view === 'docs', prevent: e => e.preventDefault(),
      dropPlan: e => this.loadDocs(this.filesFrom(e), 'plan'), pickPlan: e => this.loadDocs(this.filesFrom(e), 'plan'),
      dropGuide: e => this.loadDocs(this.filesFrom(e), 'guide'), pickGuide: e => this.loadDocs(this.filesFrom(e), 'guide'),
      dropIntel: e => this.loadDocs(this.filesFrom(e), 'intel'), pickIntel: e => this.loadDocs(this.filesFrom(e), 'intel'),
      planDocCount: s.planDocs.length, goDocs: () => this.go('docs'),
      planDocs: s.planDocs.map((d, i) => { const r = this.planRisk(d); return { name: d.name, kind: d.kind, meta: `${d.words.toLocaleString()} words · ${d.pages} pages · ${d.status}${s.docBusy && i === s.planDocs.length - 1 ? ' · ' + s.docBusy : ''}`, risks: r.risks, select: () => this.setState({ planSel: i }), border: s.planSel === i ? 'var(--color-accent)' : 'var(--color-divider)', bg: s.planSel === i ? 'rgb(16,36,62)' : 'transparent' }; }),
      guideDocs: s.guideDocs.map((g, i) => ({ ...g, remove: () => this.setState({ guideDocs: s.guideDocs.filter((_, j) => j !== i) }) })),
      hasPlanSel: !!s.planDocs[s.planSel],
      planSel: s.planDocs[s.planSel] ? { ...s.planDocs[s.planSel], ...this.planRisk(s.planDocs[s.planSel]), words: s.planDocs[s.planSel].words.toLocaleString() } : {},
      sendToCoa: () => { const d = s.planDocs[s.planSel]; if (!d) return; this.setState({ view: 'coa', step: 1, intent: d.intent.startsWith('Not found') ? s.intent : d.intent, endState: d.endState.startsWith('Not found') ? s.endState : d.endState, assumptions: d.assumptions.filter(a => !a.startsWith('No explicit')).map(a => ({ text: a.replace(/^(Assumption:|It is assumed)\s*/i, ''), status: 1, conf: 50, link: d.name.slice(0, 18) })).concat(s.assumptions).slice(0, 8), worldState: d.mission.startsWith('Not found') ? s.worldState : `${d.mission} ${s.worldState || ''}`.trim() }); },
      intel: s.intel, newIntelTitle: s.newIntelTitle, onNewIntelTitle: set('newIntelTitle'), newIntelBody: s.newIntelBody, onNewIntelBody: set('newIntelBody'),
      intelTypes: ['SIGINT', 'IMINT', 'GEOINT', 'HUMINT', 'OSINT'].map(t => ({ label: t, on: s.newIntelType === t, pick: () => this.setState({ newIntelType: t }) })),
      ingest: () => s.newIntelTitle.trim() && this.setState({ intel: [{ title: s.newIntelTitle.trim(), type: s.newIntelType, rel: 'F – Not yet evaluated', pir: 1 + (s.intel.length % 3), when: 'just now' }, ...s.intel], newIntelTitle: '', newIntelBody: '' }),
      mapSrc: './assets/jipoe-map/index.html?threat=' + encodeURIComponent(T.name),
      ipoe: s.threat === 'OLV' ? { likely: 'OPA consolidates territorial gains in Sungzon and Khorathidin, shifts to deliberate defense-in-depth, and employs hybrid warfare — cyber attacks, information operations and limited precision fires — to attrit coalition will. Nuclear posturing continues as a strategic deterrent against MNFA operations inside Olvanan territory.', dangerous: 'OPA launches renewed offensive operations into southern Khorathidin to seize the Gulf of Khorathidin coast; conducts amphibious operations against key coalition staging ports; employs additional nuclear or WMD strikes to fracture coalition will; and conducts prolonged maritime interdiction of the South Olvanan Sea and Straits of Malacca approaches.', terrain: 'Bangkok political-logistical hub; Udon Thani CBRN hazard zone; Da Nang and Ho Chi Minh City; Gulf of Khorathidin coast; South Olvanan Sea and Straits of Malacca approaches (mine and submarine threat).' }
        : { likely: `${T.name} escalates gray-zone coercion into a limited seizure of a peripheral objective under cover of an exercise, seeking a fait accompli within 72 hours.`, dangerous: `${T.name} opens with pre-emptive long-range fires on regional bases and cyber attacks on logistics, then commits amphibious and airborne forces simultaneously.`, terrain: 'Maritime chokepoints, forward airfields within 500 nm of the objective, undersea cable landing sites.' },
      pirs: s.pirs.map((p, i) => ({ ...p, n: i + 1, status: statusMap[p.status][0], bg: statusMap[p.status][1], fg: statusMap[p.status][2], tied: p.assumption != null ? ` · validates A${p.assumption + 1}` : '', cycleLabel: p.status === 2 ? 'Reset' : p.status === 1 ? 'Collection returned' : 'Task assets',
        cycle: () => { const ns = (p.status + 1) % 3; this.setState({ pirs: s.pirs.map((x, j) => j === i ? { ...x, status: ns, reports: ns === 2 ? x.reports + 1 : x.reports } : x), results: null, assumptions: (ns === 2 && p.assumption != null) ? s.assumptions.map((a, k) => k === p.assumption ? { ...a, status: 0, conf: Math.max(a.conf, 85) } : a) : s.assumptions }); } })),
      newPir: s.newPir, onNewPir: set('newPir'), addPir: () => s.newPir.trim() && this.setState({ pirs: [...s.pirs, { q: s.newPir.trim(), ind: ['Indicators to be defined'], assets: ['Unassigned'], reports: 0, ltiov: 'TBD', status: 0 }], newPir: '' }),
      rfis: s.rfis.map(r => ({ ...r, bg: rfiColor[r.status][0], fg: rfiColor[r.status][1] })), newRfi: s.newRfi, onNewRfi: set('newRfi'),
      addRfi: () => s.newRfi.trim() && this.setState({ rfis: [...s.rfis, { id: `RFI-0${35 + s.rfis.length - 4}`, q: s.newRfi.trim() + (s.newRfiLtiov ? ` (LTIOV ${s.newRfiLtiov})` : ''), to: s.newRfiRoute || 'J2', ties: s.newRfiTies || 'Unlinked', status: 'Open' }], newRfi: '', newRfiTies: '', newRfiLtiov: '', rfiOpen: false }),
      rfiOpen: !!s.rfiOpen, openRfi: () => this.setState({ rfiOpen: true }), closeRfi: () => this.setState({ rfiOpen: false }), stop: e => e.stopPropagation(),
      rfiRoutes: ['J2 / DIA', 'J4', 'J5', 'Interagency'].map(r => ({ label: r, on: (s.newRfiRoute || 'J2 / DIA') === r, pick: () => this.setState({ newRfiRoute: r }) })),
      newRfiTies: s.newRfiTies || '', onNewRfiTies: set('newRfiTies'), newRfiLtiov: s.newRfiLtiov || '', onNewRfiLtiov: set('newRfiLtiov'),
      postureStats: [{ label: 'Component commands', value: '5' }, { label: 'Designated for MNFA', value: '4 packages' }, { label: 'C-1 / C-2 ready', value: '82%' }, { label: 'Peak COA demand', value: `${Math.max(...this.buildCoas().map(c => c.res))}%` }],
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
