class Component extends DCLogic {
  state = {
    view: 'coa', step: 1, runId: 'R-0417',
    planType: 'OPORD', level: 3, ccmd: 'EUCOM', threat: 'RUS',
    worldState: '', intent: '', endState: '',
    assumptions: [
      { text: 'Article 5 remains invoked and the North Atlantic Council sustains political consensus for the restoration of Estonian and Latvian territorial integrity by force if necessary.', status: 0, conf: 85, link: 'OPORD 1.g.1 · NAC 06 SEP', valid: 'Duration of operation' , pir: 4 },
      { text: 'Germany, Poland, Denmark, the Netherlands, Belgium, Finland and Sweden grant unrestricted transit, overflight, basing and host-nation support for US force flow; EU military-mobility procedures are expedited.', status: 1, conf: 75, link: 'OPORD 1.g.2', valid: 'Through Phase II' , pir: 9 },
      { text: 'Russia does not conduct conventional strikes against CONUS; strikes against NATO territory outside the Baltic States remain possible and are covered under NATO air and missile defense planning.', status: 1, conf: 65, link: 'OPORD 1.g.3', valid: 'Operational period' , pir: 2 },
      { text: 'Strategic sealift and APS-2 stocks are sufficient to deliver 1AD with two ABCTs combat-ready in Poland NLT C+21 and the full division NLT C+45; airlift delivers advance parties, 173rd ABN and time-critical enablers NLT C+7.', status: 1, conf: 55, link: 'OPORD 1.g.4', valid: 'Expires C+21 / C+45' , pir: 1 },
      { text: 'The Baltic Sea will be contested but not closed; Danish Straits transit remains possible under Allied escort. Klaipėda and Gdańsk/Gdynia remain usable as SPODs with MCM support.', status: 1, conf: 50, link: 'OPORD 1.g.5', valid: 'Through D-Day' , pir: 7 },
      { text: 'Russia will employ non-strategic nuclear signaling and may conduct a demonstrative detonation; deliberate nuclear employment against Allied forces is less likely but planned for in Annex C App 4.', status: 1, conf: 60, link: 'OPORD 1.g.6 · ATP 7-100.1', valid: 'Operational period' , pir: 4 },
      { text: 'Belarusian forces remain uncommitted absent a Russian decision to expand the war; Belarusian territory will be used by Russia for basing and fires.', status: 1, conf: 55, link: 'OPORD 1.g.7', valid: 'Through Phase II' , pir: 2 },
      { text: 'Mission Partner Environment (MPE) and NATO Federated Mission Networking (FMN) provide adequate C2 interoperability for US forces under NATO command.', status: 0, conf: 80, link: 'OPORD 1.g.8 · Annex H', valid: 'From TOA' , pir: 9 }
    ],
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
    numCoas: 3, numSims: 2000, aggression: 0.5,
    coas: [], results: null, simRunning: false, simProgress: 0, simStatus: '', sel: 0,
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
    pirs: [
      { no: 1, q: 'Reinforcement. Will Russia expand the incursion beyond Ida-Viru and Latgale?', ind: ['1st Guards Tank Army or 20th Guards CAA movement toward the Pskov axis or into Belarus', 'Rail loading in the Moscow MD', 'Forward logistics build at Pskov, Ostrov or Luga'], assets: ['RQ-4 / RC-135 (USAFE)', 'NATO AGS', 'National technical means'], reports: 1, ltiov: 'C+10', status: 1, dp: 'Commit 1AD as counterattack force vice reserve; request follow-on forces' },
      { no: 2, q: 'Suwałki. Will 11th Army Corps or Belarus-based forces attack to close the Suwałki corridor?', ind: ['18th Guards MRD, 7th MRR or 336th Naval Infantry departure from garrison', 'Belarusian mobilization or RGF staging in the Grodno area', 'Engineer and bridging activity on the Lithuanian and Polish borders'], assets: ['2CR guard reporting', 'MQ-9 orbit', 'Polish 16th/18th Mech Div'], reports: 1, ltiov: 'C+4', status: 1, dp: 'Reinforce 2CR with 1AD ABCT; alert 173rd ABN; shift MND-NE main effort' },
      { no: 3, q: 'Enemy transition. Will Russian forces in Estonia and Latgale shift to maneuver defense, or seize Tartu, Daugavpils or the Daugava crossings before NATO closure?', ind: ['Forward-detachment and mobile-obstacle-detachment activity', 'Minefield emplacement', 'Repositioning of antitank and anti-airborne reserves', 'River-crossing preparation on the Daugava'], assets: ['SOCEUR special reconnaissance', 'Latvian National Guard', 'Armed ISR'], reports: 1, ltiov: 'C+21', status: 1, dp: 'Advance or delay D-Day; adjust MND-N scheme of maneuver' },
      { no: 4, q: 'Nuclear. Is Russia preparing to employ or demonstrate a non-strategic nuclear weapon?', ind: ['Iskander-M dispersal or warhead mating in Kaliningrad or Leningrad MD', 'Oreshnik activity in Belarus', 'Movement from 12th GUMO storage sites', 'Northern Fleet SSBN surge', 'Announced test or exclusion zones over the Baltic'], assets: ['National technical means', 'STRATCOM space ISR', 'SOCEUR SR'], reports: 1, ltiov: 'Continuous', status: 0, dp: 'Activate Annex C App 4; adjust strike authorities and dispersal' },
      { no: 6, q: 'Snow Dome. Where are the S-400/S-300 batteries, EW complexes, UAS ground stations and Iskander launch units, and has the reconnaissance-strike complex been degraded enough for the D-Day air-superiority condition?', ind: ['Emitter geolocation of S-400/S-300 and EW complexes', 'UAS GCS activity', 'Iskander launch unit locations'], assets: ['RC-135 / U-2', 'EC-37B Compass Call', 'SOCEUR SR', 'USCYBERCOM'], reports: 0, ltiov: 'D-3', status: 0, dp: 'D-Day go/no-go; SEAD/DEAD sequencing; Tomahawk release' },
      { no: 7, q: 'Baltic Fleet. Will the Baltic Fleet sortie, mine or strike?', ind: ['Kilo-class and corvette departures from Baltiysk', 'Minelaying in the Gulf of Finland and Gulf of Riga', 'Coastal-missile battery activation', 'Kalibr shooters positioned against Klaipėda, Riga, Gdańsk'], assets: ['P-8A (Sigonella / Keflavik)', 'CTF Baltic COP', 'SNMG1 / SNMCMG1'], reports: 1, ltiov: 'D-7', status: 1, dp: 'Escort and MCM prioritization; SPOD selection; Kaliningrad naval strike release' },
      { no: 9, q: 'Rear-area threat. Are Spetsnaz, GRU or proxy networks positioning against LOCs, APODs, SPODs, undersea cables, Rail Baltica or the Klaipėda LNG terminal?', ind: ['Host-nation security service reporting', 'Anomalous vessel activity near cable routes', 'UAS overflight of Allied airfields and rail nodes'], assets: ['Host-nation services', 'NATO CUI Centre', 'SOCEUR counter-sabotage'], reports: 1, ltiov: 'Continuous', status: 0, dp: 'LOC security allocation; C-UAS repositioning; SOCEUR tasking' }
    ],
    newPir: '',
    rfis: [
      { id: 'RFI-041', q: 'APS-2 draw rate at Powidz and the Dülmen/Zutendaal/Eygelshoven sites; can two ABCTs close combat-ready NLT C+21?', to: '21st TSC / 405th AFSB', ties: 'Assumption A4', status: 'Open' },
      { id: 'RFI-042', q: 'MCM Q-route clearance timeline to Klaipėda and Riga; SNMCMG1 and Allied MCM force availability.', to: 'NAVEUR / CTF Baltic', ties: 'Assumption A5', status: 'Pending' },
      { id: 'RFI-043', q: 'Confirm EU military-mobility corridor clearances and HNS agreements for Germany, Poland, Denmark and Benelux for C-Day flow.', to: 'J4 / US Mission to NATO', ties: 'Assumption A2', status: 'Open' },
      { id: 'RFI-044', q: 'Belarusian mobilization indicators and Regional Grouping of Forces order of battle in the Grodno and Vitebsk regions.', to: 'J2 / NATO Intelligence Fusion Centre', ties: 'Assumption A7', status: 'Pending' },
      { id: 'RFI-045', q: 'FMN Spiral / US BICES-X terminal availability at MNC-NE, MND-N and MND-NE for V Corps liaison.', to: 'J6', ties: 'Assumption A8', status: 'Answered' }
    ],
    newRfi: '',
    planDocs: [
      { name: 'USEUCOM OPORD 26-004 — OPERATION AMBER SHIELD.docx', kind: 'DOCX', words: 8600, pages: 18, status: 'Parsed', text: '',
        mission: 'US European Command, as the supported combatant command, on order and NLT C-Day (10 SEP 2026), deploys, receives and employs designated US ground, air, maritime and special operations forces in the Baltic Region under NATO command; defends Allied territory, airspace and sea lines of communication; and, on order (D-Day), conducts and enables Alliance counteroffensive operations to expel Russian forces from Estonia and Latvia, while maintaining strategic deterrence across the remainder of the EUCOM AOR and managing escalation, in order to restore the territorial integrity of Estonia and Latvia, preserve the credibility of NATO Article 5 and deter further Russian aggression against the Alliance.',
        intent: 'This operation exists to prove that Article 5 is a fact and not a slogan. The United States will fight forward with Allies to restore Estonia and Latvia to their governments, deny Russia a frozen conflict on NATO soil, and do so without allowing Moscow to convert a limited incursion into a general war or a nuclear crisis. Speed of reinforcement, Allied cohesion and escalation discipline are the decisive factors.',
        endState: 'Russian forces are expelled from Estonia and Latvia and Allied forces control the international border; the Suwałki corridor, Baltic SPODs and Danish Straits are open; Allied air and maritime superiority over the Baltic Region is established; a sustainable Allied forward defense is in place at brigade-plus strength in each Baltic State; escalation has been contained below the nuclear threshold; and Russia has been denied both a territorial gain and a narrative of Alliance disunity.',
        assumptions: ['Article 5 remains invoked and the NAC sustains consensus for restoration by force.', 'Transit, overflight, basing and HNS granted by Germany, Poland, Denmark, Benelux, Finland and Sweden.', 'Russia does not strike CONUS; strikes on NATO territory outside the Baltics remain possible.', 'Sealift and APS-2 deliver 1AD with two ABCTs NLT C+21, full division NLT C+45.', 'Baltic Sea contested but not closed; Danish Straits transit possible under escort.', 'Russia employs nuclear signaling and may conduct a demonstrative detonation.', 'Belarusian forces remain uncommitted absent a Russian decision to expand the war.', 'MPE and NATO FMN provide adequate C2 interoperability.'],
        phases: ['Phase I Deter and Reinforce (Now to C+21)', 'Phase II Defend and Shape (C+21 to D-Day, notionally C+30)', 'Phase III Restore (D-Day to D+30)', 'Phase IV Stabilize and Transition (D+30 onward)'],
        sig: { offensive: 8, defensive: 14, escalation: 9, restraint: 9, force: 7, partners: 18, sustain: 13, intel: 11 } }
    ],
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
    const mod = await import('./assets/docreader.js');
    for (const f of files) {
      this.setState({ docBusy: `Reading ${f.name}…` });
      let doc;
      try { doc = await mod.readDocument(f); } catch (e) { doc = { name: f.name, kind: f.name.split('.').pop().toUpperCase(), text: '', words: 0, pages: 0 }; }
      const sig = mod.signalIndex(doc.text || '');
      if (kind === 'plan') {
        const ex = mod.extractPlan(doc.text || '');
        const entry = { ...doc, status: doc.text ? 'Parsed' : 'Could not read text — metadata only', mission: ex.mission || 'Not found in document', intent: ex.intent || 'Not found in document', endState: ex.endState || 'Not found in document', assumptions: ex.assumptions.length ? ex.assumptions : ['No explicit assumptions found'], pirs: ex.pirs || [], phases: ex.phases, sig };
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
    { label: 'Consolidation and freeze (MLCOA)', desc: 'Maneuver defense behind mine, obstacle and EW belt in Narva and Latgale; hybrid pressure; nuclear signaling as NATO builds', ag: 0.35 },
    { label: 'Expanded incursion (MDCOA)', desc: '1st GTA reinforces via Pskov; converging attack closes Suwałki; Baltic Fleet mines and strikes SPODs; demonstrative nuclear detonation', ag: 0.8 },
    { label: 'Horizontal escalation', desc: 'Kalibr and Kh-101 strikes on Polish and German APODs/SPODs; sabotage of undersea cables and rail LOCs', ag: 0.6 }
  ];
  PROBLEM_SETS = { 0: ['Alliance consensus', 'Article 5 credibility', 'Strategic communication'], 1: ['Force flow through Poland and Germany', 'Military mobility', 'Reception infrastructure'], 2: ['IAMD over reception corridor', 'Horizontal escalation'], 3: ['1AD closure timeline', 'D-Day conditions', 'APS-2 draw'], 4: ['Baltic SPODs', 'MCM and escort', 'Sustainment line to Klaipėda / Riga'], 5: ['Escalation management', 'Nuclear consequence management', 'Strike authorities'], 6: ['Suwałki corridor', 'Belarus front', '2CR guard'], 7: ['Coalition C2', 'Liaison and reporting'] };
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
    RUS: { name: 'Russia', label: 'Russian Federation', desc: 'Armed Forces of the Russian Federation: limited incursion into Narva/Ida-Viru and eastern Latgale by 6th CAA and 76th GAAD (05 SEP 2026); 11th Army Corps and Belarus-based forces threaten Suwałki; Baltic Fleet mining and Kalibr threat; Iskander-M and Oreshnik nuclear signaling. Fights per ATP 7-100.1: reconnaissance-strike complex, Snow Dome, maneuver defense.' },
    PRC: { name: 'PRC', label: 'China (PRC)', desc: 'Pacing challenge; multi-domain A2/AD, maritime militia, gray-zone coercion.' },
    IRN: { name: 'Iran', label: 'Iran', desc: 'Proxy networks, missiles and UAS, maritime harassment.' },
    DPRK: { name: 'DPRK', label: 'North Korea', desc: 'Nuclear-armed artillery and missile threat to allies.' },
    VEO: { name: 'VEO', label: 'Violent extremist orgs', desc: 'Dispersed, partner-enabled counter-network problem.' }
  };
  COA_LIB = [
    { title: 'Rapid Reinforcement, Hold and Restore', approach: 'Base plan · LOE 1-3', deps: [1, 2, 4, 5], s: 0.72, cas: 2.1, esc: 0.34, days: 60, res: 88, dps: 5,
      concept: '2CR forward to Lithuania and the Daugava by C+4; 1AD draws APS-2 and closes two ABCTs at Orzysz by C+21; joint SEAD/DEAD campaign degrades the Snow Dome in Estonia, Latgale and the Pskov support zone; D-Day counteroffensive along the Daugava–Rēzekne axis at C+30 with 1AD as the armored main effort.',
      tasks: ['2CR guard on Suwałki and the Lithuanian–Belarusian border NLT C+4', 'Two 1AD ABCTs combat-ready NLT C+21; third by sealift C+45', 'Joint suppression of IADS, EW and fires networks in Phase II', 'MND-N main attack to restore Latgale and Ida-Viru at D-Day'] },
    { title: 'Defend Forward, Delay D-Day', approach: 'Conditions-first', deps: [1, 4, 6, 8], s: 0.64, cas: 1.4, esc: 0.2, days: 95, res: 80, dps: 4,
      concept: 'Complete full 1AD closure (three ABCTs, C+45) and finish MCM clearance to Riga before attacking; Phase II extended to D-Day at roughly C+60. Accepts a longer Russian consolidation window and a frozen-conflict narrative risk in exchange for overmatch and lower casualties.',
      tasks: ['Extend Phase II shaping; hold D-Day until three ABCTs and cleared Q-routes', 'Persistent ISR against PIRs 1, 3 and 6', 'Sustain Alliance consensus through the delay via StratCom', 'Counterattack only if Suwałki is threatened'] },
    { title: 'Suwałki-First Economy of Force', approach: 'Secure the LOC', deps: [2, 4, 7], s: 0.58, cas: 1.6, esc: 0.26, days: 80, res: 75, dps: 4,
      concept: '1AD is committed as the counterattack force against 11th Army Corps and Belarus-based threats to the Suwałki corridor rather than held as reserve; the Estonian and Latvian restoration is led by MND-N Allied forces with US fires, air and 2CR in support, and US armor joins Phase III late.',
      tasks: ['1AD positioned at Orzysz–Bemowo Piskie oriented on Kaliningrad and Grodno', '2CR and 173rd ABN reinforce MND-NE', 'US deep fires and air support Allied attack in Latgale', 'Convoys through Suwałki under dedicated C-UAS escort'] },
    { title: 'Deep Strike and Maritime Pressure', approach: 'Fires-led shaping', deps: [1, 3, 6], s: 0.66, cas: 1.5, esc: 0.52, days: 55, res: 70, dps: 5,
      concept: 'Seek early NAC and national approval to strike Kaliningrad IADS, Kalibr shooters and coastal batteries with Tomahawk and long-range fires; carrier strike group holds the Northern Fleet at risk; ground counteroffensive follows a compressed Phase II. Fastest route to air and sea superiority; highest escalation exposure.',
      tasks: ['Request NAC approval for Kaliningrad strikes in Phase II', 'Tomahawk and 56th Artillery Command deep fires against Snow Dome nodes', 'CSG and P-8A ASW pressure on Baltic and Northern Fleets', 'Compressed D-Day at C+25'] },
    { title: 'Restrained Defense and Negotiated Withdrawal', approach: 'Deter, defend, negotiate', deps: [1, 3, 7, 8], s: 0.41, cas: 0.6, esc: 0.1, days: 120, res: 60, dps: 3,
      concept: 'Establish an unbreakable defense on the Daugava, Tapa and Suwałki lines with US forces, deny further gains, and use the Alliance build-up as leverage for a Russian withdrawal without a counteroffensive. Lowest casualties and escalation risk; does not restore territory by force and risks the frozen conflict the intent forbids.',
      tasks: ['Defensive positions at brigade-plus in each Baltic State', 'IAMD and MCM to keep SPODs open', 'Joint Staff-led de-escalation channel', 'StratCom on Alliance unity and Russian pretext'] }
  ];

  componentDidMount() { const v = this.props.startView, st = +this.props.startStep; if (v || st) { if (['intel', 'docs', 'posture'].includes(v)) this.setState({ view: 'coa', step: 1, inputTab: v }); else this.setState({ view: v || 'coa', step: st || 1 }); } }
  go(view) { if (['intel', 'docs', 'posture'].includes(view)) return this.setState({ view: 'coa', step: 1, inputTab: view }); this.setState({ view }); }
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
    this.setState({ coas, simRunning: true, simProgress: 0, results: null, simStatus: 'Setting up the red cell from JIPOE…' });
    const msgs = ['Setting up the red cell from JIPOE…', 'Playing adversary reactions…', 'Resolving engagements…', 'Scoring risk to mission, personnel, escalation…'];
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
      1: [['2CR screens Suwałki by C+4; 1AD draws APS-2 at Powidz; USAFE establishes DCA over the Baltics.', `${t} REB and GPS jamming against reception corridor; Spetsnaz sabotage of Polish rail; Iskander readiness announced.`, 'C-UAS and LOC security to FPCON CHARLIE; SDDC reroutes armor by road; STRATCOM deterrence messaging.', 'DP1 · Force flow'], ['Joint SEAD/DEAD against S-400 and EW complexes in Latgale and Pskov support zone.', `${t} transitions to maneuver defense; minefields on the Daugava; threatens strikes on Powidz if Pskov is hit.`, 'SACEUR approves strikes on engaged forces only; Patriot repositioned to Powidz and Rzeszów.', 'DP2 · Strike authorities'], ['D-Day: 1AD attacks along Daugava–Rēzekne; Estonian and UK forces fix Narva.', `${t} announces exclusion zone over the Baltic; SSBN surge; Oreshnik activity in Belarus.`, 'Activate Annex C App 4; disperse forces; NAC consultation; continue the attack.', 'DP3 · Nuclear signaling']],
      2: [['Extend Phase II; complete three-ABCT closure and MCM clearance to Riga.', `${t} hardens the Narva and Latgale belts; pushes a negotiated freeze through third parties; IO on Baltic Russophones.`, 'StratCom sustains Alliance consensus; persistent ISR builds the target set.', 'DP1 · Consensus'], ['Shaping fires degrade the reconnaissance-strike complex over 30 days.', `${t} 1st GTA closes to Pskov; reinforces Latgale before the delayed D-Day.`, 'Re-evaluate correlation of forces; commit 1AD earlier or accept a longer campaign.', 'DP2 · Reinforcement'], ['D-Day at C+60 with overmatch.', `${t} Kalibr strikes on Klaipėda LNG and Riga port.`, 'Escort and MCM surge; Tomahawk release against Kaliningrad shooters requested.', 'DP3 · SPODs']],
      3: [['1AD oriented on Suwałki; 2CR and 173rd ABN reinforce MND-NE.', `${t} 11th Army Corps demonstrates toward the Lithuanian border but does not cross; Belarus stages in Grodno.`, 'Hold 1AD; Allied MND-N forces begin shaping in Latgale with US fires.', 'DP1 · Fix vs commit'], ['Allied-led attack toward Rēzekne with US air and deep fires.', `${t} maneuver defense trades space; anti-airborne reserves counterattack the Daugava crossings.`, 'Release one 1AD ABCT to MND-N; accept thinner Suwałki guard.', 'DP2 · Release reserve'], ['1AD joins Phase III late.', `${t} claims Allied disunity as US armor stays in Poland.`, 'StratCom emphasizes Allied lead; visible US armor movement north.', 'DP3 · Narrative']],
      4: [['Request NAC approval for Kaliningrad strikes; CSG pressures the Northern Fleet.', `${t} frames strikes as attack on the homeland; Iskander warhead mating observed in Kaliningrad.`, 'Joint Staff de-escalation channel; limit strikes to Kalibr shooters and IADS.', 'DP1 · NAC approval'], ['Tomahawk and deep fires collapse the Snow Dome over Latgale in 10 days.', `${t} demonstrative low-yield detonation over the Baltic Sea.`, 'Nuclear consequence management; NAC consultation; national escalation measures.', 'DP2 · Detonation'], ['Compressed D-Day at C+25 with two ABCTs.', `${t} 1st GTA commits through Pskov toward Tartu.`, '173rd ABN and Estonian forces block; air interdiction of the Pskov axis.', 'DP3 · Pskov axis']],
      5: [['Brigade-plus defense on the Daugava, Tapa and Suwałki lines; IAMD and MCM keep SPODs open.', `${t} consolidates Narva and Latgale; offers a freeze with forces in place.`, 'Reject freeze; sustain build-up as leverage.', 'DP1 · Freeze offer'], ['Allied build-up to corps strength over 90 days.', `${t} sabotage against Estlink and Rail Baltica; IO on Baltic domestic resolve.`, 'Undersea infrastructure defense; counter-sabotage; StratCom.', 'DP2 · Hybrid pressure'], ['Negotiations stall; Russian forces remain on NATO soil.', `${t} normalizes the occupation; Allies question the mission.`, 'Decide: transition to a counteroffensive or accept a frozen conflict.', 'DP3 · Commit']]
    };
    return (lib[r] || lib[1]).map((a, i) => ({ turn: (i + 1) * 3, action: a[0], reaction: a[1], counter: a[2], dp: a[3] }));
  }
  sensitivity(ranked, best, crit) {
    const s = this.state, res = s.results; if (!res || !best) return { explain: [], explainText: '', runnerUp: {}, stability: [], stabilityText: '', tornado: [], sweep: [], sweepText: '', assumptionRisk: [], assumptionText: '' };
    const w = s.weights, keys = ['mission', 'personnel', 'escalation', 'time', 'resources'], lv = { mission: 'rm', personnel: 'rp', escalation: 're', time: 'rt', resources: 'rr' };
    const runner = ranked[1] || ranked[0];
    const explain = crit.map(([k, label]) => { const b = w[k] * this.score(best[lv[k]]), o = w[k] * this.score(runner[lv[k]]), mx = w[k] * 4 || 1; const d = b - o; return { label, bestW: Math.round(b / mx * 50), otherW: Math.round(o / mx * 50), delta: (d > 0 ? '+' : '') + d, color: d > 0 ? 'rgb(76,195,138)' : d < 0 ? 'rgb(255,120,120)' : 'var(--color-neutral-600)' }; });
    const gains = explain.filter(x => x.delta.startsWith('+')).map(x => x.label.toLowerCase()), losses = explain.filter(x => x.delta.startsWith('-')).map(x => x.label.toLowerCase());
    const explainText = `Strategy ${best.n} leads Strategy ${runner.n} by ${best.raw - runner.raw} weighted points. The margin comes from ${gains.length ? gains.join(', ') : 'no single criterion'}${losses.length ? '; it gives ground on ' + losses.join(', ') : ''}. Each bar is weight × JRAM score (Low 4 … High 1).`;
    const r = this.rng(4242); const wins = {}; res.forEach(x => wins[x.n] = 0);
    for (let i = 0; i < 500; i++) { const pw = {}; keys.forEach(k => pw[k] = Math.max(0, Math.min(5, w[k] + Math.round((r() - 0.5) * 4)))); wins[this.rankWith(pw, res)[0].n]++; }
    const stability = res.map(x => ({ n: x.n, pct: Math.round(wins[x.n] / 5), bg: x.n === best.n ? 'var(--color-accent)' : 'rgb(100,116,139)' })).sort((a, b) => b.pct - a.pct);
    const stabilityText = stability[0].pct >= 75 ? `Robust: Strategy ${stability[0].n} ranks first in ${stability[0].pct}% of perturbed weightings.` : `Fragile: the top rank shifts between Strategy ${stability[0].n} and Strategy ${stability[1] ? stability[1].n : '-'} depending on weights — the commander's priorities decide.`;
    const flip = n => n === best.n ? ['rgb(19,57,41)', 'rgb(76,195,138)'] : ['rgb(174,25,85)', 'rgb(254,236,244)'];
    const tornado = crit.map(([k, label]) => { const lo = this.rankWith({ ...w, [k]: Math.max(0, w[k] - 2) }, res)[0].n, hi = this.rankWith({ ...w, [k]: Math.min(5, w[k] + 2) }, res)[0].n; return { label, lo, hi, loBg: flip(lo)[0], loFg: flip(lo)[1], hiBg: flip(hi)[0], hiFg: flip(hi)[1] }; });
    const coas = s.coas.length ? s.coas : this.buildCoas();
    const sw = [0.2, 0.5, 0.85].map(ag => this.compute(coas, ag, 400));
    const sweep = coas.map((c, i) => ({ n: c.n, lo: Math.round(sw[0][i].pSuccess * 100), mid: Math.round(sw[1][i].pSuccess * 100), hi: Math.round(sw[2][i].pSuccess * 100) }));
    const bestSw = sweep.find(x => x.n === best.n) || sweep[0]; const mostRobust = [...sweep].sort((a, b) => (a.lo - a.hi) - (b.lo - b.hi))[0];
    const sweepText = `Strategy ${best.n} loses ${bestSw.lo - bestSw.hi} points of success probability from restrained to aggressive adversary behavior${mostRobust.n === best.n ? ', and it is also the most robust option across the sweep.' : `; Strategy ${mostRobust.n} degrades least (${mostRobust.lo - mostRobust.hi}).`}`;
    const assumptionRisk = s.assumptions.map((a, i) => ({ n: i + 1, text: a.text, conf: a.conf, status: this.A_STATUS[a.status][0], bg: this.A_STATUS[a.status][1], fg: this.A_STATUS[a.status][2] })).sort((a, b) => a.conf - b.conf);
    const weak = assumptionRisk.filter(a => a.conf < 70 || a.status !== 'Valid');
    const sigma = Math.round(s.assumptions.reduce((a, x) => a + (x.status === 2 ? 0.04 : (100 - x.conf) / 1000), 0) * 100);
    const assumptionText = weak.length ? `${weak.length} assumption(s) below 70% confidence or unvalidated add roughly ${sigma} points of uncertainty to every result. Validate A${weak[0].n} first — it has the lowest confidence.` : 'All assumptions validated at high confidence; uncertainty is driven by collection gaps only.';
    return { explain, explainText, runnerUp: { n: runner.n, title: runner.title }, stability, stabilityText, tornado, sweep, sweepText, assumptionRisk, assumptionText };
  }
  // Assumption index (1-based) -> PIR: explicit link, else keyword overlap, else round-robin so every assumption has a PIR
  pirFor(i) {
    const s = this.state, a = s.assumptions[i - 1]; if (!a || !s.pirs.length) return null;
    if (a.pir) return s.pirs.find(p => (p.no || s.pirs.indexOf(p) + 1) === a.pir) || null;
    const words = (a.text.toLowerCase().match(/[a-zåäöéū]{5,}/g) || []);
    let best = null, score = 1;
    s.pirs.forEach(p => { const t = (p.q + ' ' + (p.ind || []).join(' ')).toLowerCase(); const n = words.filter(w => t.includes(w)).length; if (n > score) { score = n; best = p; } });
    return best || s.pirs[(i - 1) % s.pirs.length];
  }
  assumptionsForPir(p) { return this.state.assumptions.map((_, k) => k + 1).filter(i => this.pirFor(i) === p); }
  mitigations(r, c) {
    const s = this.state, col = l => this.riskColor(l)[1]; const out = [];
    const deps = (c.deps || []).map(i => s.assumptions[i - 1] && { i, a: s.assumptions[i - 1] }).filter(Boolean);
    const weakest = deps.slice().sort((x, y) => x.a.conf - y.a.conf)[0];
    out.push({ tag: `Mission · ${r.rm}`, fg: col(r.rm), risk: `Fails to reach the end state in about ${Math.round((1 - r.pSuccess) * 100)} of 100 runs${weakest ? `, most often when A${weakest.i} (${weakest.a.conf}%) does not hold` : ''}.`, fix: weakest ? `Task collection against A${weakest.i} now (${(() => { const p = this.pirFor(weakest.i); return p ? 'PIR ' + (p.no || s.pirs.indexOf(p) + 1) : 'assign a PIR'; })()}) and write a branch plan for the case where it fails.` : 'Hold a ready alternative strategy and define the trigger to switch.' });
    out.push({ tag: `Personnel · ${r.rp}`, fg: col(r.rp), risk: `Worst-case losses near ${r.cas.toFixed(1)} percent of the committed force over ${r.days} days.`, fix: r.rp === 'Low' ? 'Maintain force protection posture; no additional measures.' : 'Phase the commitment so lead elements are not exposed before enablers and medical support are in place; confirm Role 3 and evacuation capacity.' });
    out.push({ tag: `Escalation · ${r.re}`, fg: col(r.re), risk: `Adversary widens the fight in ${Math.round(r.pEsc * 100)} of 100 runs; spreads beyond the theater in ${Math.round(r.pMajor * 100)}.`, fix: r.re === 'Low' ? 'Keep current strike approval rules and messaging.' : 'Keep strikes limited to forces engaged against Allied territory, pre-clear the approval chain for time-sensitive targets, and keep the Joint Staff de-escalation channel open.' });
    const gaps = s.pirs.filter(p => p.status === 0 && deps.some(d => this.pirFor(d.i) === p));
    gaps.slice(0, 2).forEach(p => out.push({ tag: 'Collection gap', fg: 'rgb(255,203,71)', risk: `PIR ${p.no || s.pirs.indexOf(p) + 1} is untasked: "${p.q.replace(/\?.*$/, '')}".`, fix: `Assign ${(p.assets || []).filter(a => a !== 'Unassigned')[0] || 'a collector'} with a latest-time-of-value before the first decision point.` }));
    return out;
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
      evalSummary: `Strategy ${best.n} ranks first at ${best.pct}% of the weighted maximum succeeding in ${Math.round(best.pSuccess * 100)} of 100 runs across ${s.numSims} wargame runs${runner ? `, ahead of Strategy ${runner.n} (${runner.pct}%)` : ''}. It holds the top rank in ${stab}% of perturbed weightings and rests on ${deps.length} load-bearing assumption${deps.length === 1 ? '' : 's'}, ${weakDeps.length} of which ${weakDeps.length === 1 ? 'is' : 'are'} below threshold. ${openPirs.length} collection requirement${openPirs.length === 1 ? '' : 's'} remain open. Confidence in the recommendation is ${grade[0].toLowerCase()}.`,
      evalStats: [
        { label: 'Weighted score', value: `${best.pct}%`, note: `Rank #1 of ${ranked.length}`, color: 'var(--color-text)' },
        { label: 'Rank stability', value: `${stab}%`, note: 'of perturbed weightings', color: stab >= 75 ? 'rgb(76,195,138)' : 'rgb(255,203,71)' },
        { label: 'Thin evidence', value: `${weakDeps.length} / ${deps.length}`, note: 'load-bearing claims weak', color: weakDeps.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)' },
        { label: 'Open collection', value: String(openPirs.length), note: `${gapsPirs.length} untasked gap${gapsPirs.length === 1 ? '' : 's'}`, color: gapsPirs.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)' },
        { label: 'Worst propagation', value: `−${worstProp.drop} pts`, note: worstProp.i ? `if A${worstProp.i} fails` : 'no dependencies', color: worstProp.drop >= 10 ? 'rgb(255,120,120)' : 'rgb(255,203,71)' }
      ],
      evalGaps: deps.map(d => { const p = this.pirFor(d.i); const pl = p ? `PIR ${p.no || s.pirs.indexOf(p) + 1} (${['untasked', 'collecting', 'answered'][p.status]})` : 'no PIR assigned'; return `A${d.i} · ${d.a.conf}% ${this.A_STATUS[d.a.status][0].toLowerCase()}: ${d.a.text.split(/[,;—]/)[0].replace(/\.$/, '')}. Collection: ${pl}.`; }).concat(deps.length === 0 ? ['This strategy carries no load-bearing assumptions.'] : []),
      evalRisks: [
        `Mission (${best.rm}): about ${Math.round((1 - best.pSuccess) * 100)} in 100 runs the strategy does not reach the end state on time. ${best.rm === 'Low' || best.rm === 'Moderate' ? 'Acceptable for planning.' : 'The commander should expect to adjust the plan mid-execution.'}`,
        `Personnel (${best.rp}): in the worst 10 percent of runs the force loses about ${best.cas.toFixed(1)} percent of committed personnel. ${best.rp === 'Low' || best.rp === 'Moderate' ? 'Within expected combat losses.' : 'Medical, replacement and casualty-notification capacity must be checked before execution.'}`,
        `Escalation (${best.re}): ${Math.round(best.pEsc * 100)} in 100 runs the adversary widens the fight, and ${Math.round(best.pMajor * 100)} in 100 it spreads beyond the theater. ${best.re === 'Low' || best.re === 'Moderate' ? 'Manageable with existing strike approval rules.' : 'Strike authorities and de-escalation channels need SecDef and NAC attention before D-Day.'}`,
        `Adversary behavior: if the adversary is aggressive rather than restrained, the chance of success drops from ${sw.lo} to ${sw.hi} in 100. The plan should not depend on the adversary holding back.`,
        ...gapsPirs.map(p => `Untasked PIR ${p.no || s.pirs.indexOf(p) + 1}: nobody is collecting against "${p.q.replace(/\?.*$/, '')}". Until it is tasked the staff is guessing at this question, and any assumption that leans on it (${this.assumptionsForPir(p).map(i => 'A' + i).join(', ') || 'none linked'}) stays unverified.`)
      ],
      evalConditions: [worstProp.i ? `Validate A${worstProp.i} before C-Day; its failure costs Strategy ${best.n} ${worstProp.drop} points of success probability.` : 'No single assumption failure degrades the option materially.', openPirs.length ? `Close ${openPirs.length} open collection requirement${openPirs.length === 1 ? '' : 's'} to narrow outcome distributions before execution.` : 'Collection complete; outcome distributions at minimum width.', `Decision points DP1–DP3 in the wargame ARC table define branch triggers${runner ? `; Strategy ${runner.n} is the ready alternative` : ''}.`, best.re === 'Significant' || best.re === 'High' ? 'Escalation risk requires SecDef-level review of targets and STRATCOM deterrence messaging.' : 'Escalation risk within theater tolerance; maintain STRATCOM signaling.']
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
    const docSel = s.planDocs[s.planSel]; const docTitle = docSel ? docSel.name.replace(/\.(docx|pdf|txt|md)$/i, '').replace(/\s+[—–-]\s+.*$/, '').trim() : ''; const planLabel = docTitle || `${s.ccmd} ${{ OPORD: 'OPORD', CCP: 'CCP', CON: 'CONPLAN', GCP: 'GCP', FCP: 'FCP', SPF: 'SPF' }[s.planType]}`;
    const stage = s.view === 'coa' ? (s.step === 3 ? 3 : s.step === 5 ? 4 : (s.step === 1 && s.inputTab !== 'strategy') ? 5 : 1) : s.view === 'collection' ? 2 : 0; const tog = k => () => this.setState({ details: { ...s.details, [k]: !s.details[k] } });
    const isWeak = a => a.conf < 70 || a.status !== 0 || /expire/i.test(a.valid || '');
    const coasNow = s.coas.length ? s.coas : this.buildCoas();
    const ranked = this.ranked();
    const results = s.results ? s.results.map(r => ({ ...r, sims: s.numSims, select: () => this.setState({ sel: r.n - 1 }),
      outline: s.sel === r.n - 1 ? '2px solid var(--color-accent)' : 'none',
      pSuccess: Math.round(r.pSuccess * 100), pEsc: Math.round(r.pEsc * 100), pMajor: Math.round(r.pMajor * 100), cas: r.cas.toFixed(1),
      risks: [['Risk to mission', r.rm], ['Risk to personnel', r.rp], ['Risk of escalation', r.re]].map(([label, level]) => ({ label, level, bg: this.riskColor(level)[0], fg: this.riskColor(level)[1] })), mitigations: this.mitigations(r, coasNow.find(c => c.n === r.n) || {}) })) : [];
    const cell = (level, detail) => ({ level, detail, bg: this.riskColor(level)[0], fg: this.riskColor(level)[1] });
    const crit = [['mission', 'Risk to mission', r => cell(r.rm, `fails ${Math.round((1 - r.pSuccess) * 100)} in 100`)], ['personnel', 'Risk to personnel', r => cell(r.rp, `worst case ${r.cas.toFixed(1)}% casualties`)], ['escalation', 'Risk of escalation', r => cell(r.re, `escalates ${Math.round(r.pEsc * 100)} in 100`)], ['time', 'Time to end state', r => cell(r.rt, `${r.days} days`)], ['resources', 'Force demand vs GFM', r => cell(r.rr, `${r.res}% of allocated`)]];
    const best = ranked[0]; const worstRisk = best ? [['mission', best.rm], ['personnel', best.rp], ['escalation', best.re]].sort((a, b) => this.score(a[1]) - this.score(b[1]))[0] : null;
    const sel = s.results ? s.results[s.sel] || s.results[0] : null;
    const chosenR = ranked.find(r => r.n === s.chosen) || best || {};
    const statusMap = { 0: ['Gap', 'rgb(174,25,85)', 'rgb(254,236,244)'], 1: ['Collecting', 'rgb(130,78,0)', 'rgb(254,243,221)'], 2: ['Answered', 'rgb(35,110,74)', 'rgb(229,251,235)'] };
    const rfiColor = { Open: ['rgb(174,25,85)', 'rgb(254,236,244)'], Pending: ['rgb(130,78,0)', 'rgb(254,243,221)'], Answered: ['rgb(35,110,74)', 'rgb(229,251,235)'] };
    const set = k => e => this.setState({ [k]: e.target.value });
    const defaultWorld = s.threat === 'RUS'
      ? `Scenario: ${this.SCENARIOS[s.scenario].label}. USEUCOM is the supported combatant command for Operation AMBER SHIELD; the NAC invoked Article 5 on 06 SEP 2026. On 05 SEP Russian 6th CAA elements seized the Narva crossings and Ida-Viru County; 76th GAAD and Spetsnaz hold blocking positions in eastern Latgale. 11th Army Corps (Kaliningrad) and Belarus-based forces threaten the Suwałki corridor but have not crossed. Iskander-M readiness announced; Northern Fleet SSBN surge. C-Day 10 SEP 2026; D-Day on order, notionally C+30. Autumn weather degrades aviation and ISR; bogs canalize armor onto roads.`
      : `Scenario: ${this.SCENARIOS[s.scenario].label}. ${s.ccmd} is supporting a ${planLabel.toLowerCase()} against ${T.label}. ${T.desc} Indications from the last 72 hours show force concentration and readiness increases consistent with the JIPOE most-likely COA. Allied posture is defensive; civilian shipping remains in the area. Weather window favorable for the next 10 days.`;
    return {
      crumb: s.view === 'collection' ? 'Collection Management Agent' : s.view === 'doctrine' ? 'Doctrine' : s.step === 3 ? 'Predictive Interconnected Risk Engine' : s.step === 5 ? 'Option Recommendation' : s.step === 1 ? 'Inputs / ' + { strategy: 'Strategy', intel: 'Intelligence', docs: 'Plans & Guidance', posture: 'Force Posture' }[s.inputTab] : 'Strategy Option Evaluation',
      showWorkflow: s.view !== 'doctrine',
      isCoa: s.view === 'coa', isIntel: s.step === 1 && s.inputTab === 'intel', isCollection: s.view === 'collection', isRfi: s.view === 'collection', isPosture: s.step === 1 && s.inputTab === 'posture', isDoctrine: s.view === 'doctrine',
      inputStrategy: s.inputTab === 'strategy',
      inputTabs: [['Strategy', 'strategy'], ['Intelligence', 'intel'], ['Plans & Guidance', 'docs'], ['Force Posture', 'posture']].map(([label, t]) => ({ label, go: () => this.setState({ inputTab: t }), line: s.inputTab === t ? 'var(--color-accent)' : 'transparent', opacity: s.inputTab === t ? 1 : 0.65 })),
      strategyName: (s.planDocs[s.planSel] || {}).name || 'No strategy loaded',
      strategyMeta: s.planDocs[s.planSel] ? `${s.planDocs[s.planSel].words.toLocaleString()} words · ${s.planDocs[s.planSel].pages} pages · ${s.planDocs[s.planSel].status}${s.docBusy ? ' · ' + s.docBusy : ''}` : (s.docBusy || 'Parsed in your browser; mission, intent, end state and assumptions are pulled into the fields below'),
      strategyRisks: s.planDocs[s.planSel] ? this.planRisk(s.planDocs[s.planSel]).risks : [],
      planTypeDesc: (p => `${p.label} — ${p.desc}`)(this.PLAN_TYPES.find(x => x.id === s.planType)),
      scenarioLabel: this.SCENARIOS[s.scenario].label, showScenario: s.details.scenario, toggleScenario: tog('scenario'), scenarioToggle: s.details.scenario ? 'Hide details' : 'Edit scenario',
      showArc: s.details.arc, toggleArc: tog('arc'), arcToggle: s.details.arc ? 'Hide log' : 'Show log',
      showSens: s.details.sens, toggleSens: tog('sens'), sensToggle: s.details.sens ? 'Hide details' : 'Show details',
      showPirDetail: s.details.pir, togglePir: tog('pir'), pirToggle: s.details.pir ? 'Hide indicators and assets' : 'Show indicators and assets',
      pirSummary: `${s.pirs.filter(p => p.status === 0).length} gaps · ${s.pirs.filter(p => p.status === 1).length} collecting · ${s.pirs.filter(p => p.status === 2).length} answered`,
      onPirKey: e => { if (e.key === 'Enter' && s.newPir.trim()) this.setState({ pirs: [...s.pirs, { q: s.newPir.trim(), ind: ['Indicators to be defined'], assets: ['Unassigned'], reports: 0, ltiov: 'TBD', status: 0 }], newPir: '' }); },
      goCollection: () => this.go('collection'), goDoctrine: () => this.go('doctrine'), goHome: () => this.setState({ view: 'coa', step: 1, inputTab: 'strategy' }),
      feedUrl: s.feedUrl, onFeedUrl: set('feedUrl'), toggleFeed: () => this.toggleFeed(), feedBtn: s.feedOn ? 'Disconnect' : 'Connect', feedLabel: s.feedOn ? `Connected · ${s.feedCount} received` : 'Not connected', feedColor: s.feedOn ? 'rgb(76,195,138)' : 'var(--color-neutral-600)',
      stages: [['Strategy Option Evaluation', 'Scores strategies against their assumptions and shows exactly where the analysis stands on thin evidence.', 1], ['Collection Management Agent', 'Turns weak assumptions into draft collection requirements: tagged, routed, tracked. Scores re-run as collection returns.', 2], ['Predictive Interconnected Risk Engine', 'Reads the graph\'s edges and propagates: which option degrades if this assumption fails, and how far it travels.', 3], ['Option Recommendation', 'Strategy evaluation taking in every gap and risk; offers the Commander a recommended option and the risk accepted.', 4]].map(([label, sub, n]) => { const active = stage === n; const done = n === 1 ? !!s.results : n === 2 ? s.pirs.every(p => p.status === 2) : n === 3 ? !!s.results : !!s.decision; return { n, label, sub, lineShow: n < 4 ? 'block' : 'none', go: () => n === 1 ? this.setState({ view: 'coa', step: [1, 2, 4].includes(s.step) ? s.step : 1, inputTab: 'strategy' }) : n === 2 ? this.go('collection') : n === 3 ? this.setState({ view: 'coa', step: 3 }) : this.setState({ view: 'coa', step: 5 }), ring: active || done ? 'var(--color-accent)' : 'var(--color-divider)', bg: active ? 'rgb(16,42,76)' : done ? 'rgb(9,84,165)' : 'var(--color-surface)', fg: active || done ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', opacity: active ? 1 : 0.65 }; }),
      foundation: { go: () => this.go('intel'), ring: stage === 5 ? 'var(--color-accent)' : 'var(--color-divider)', bg: stage === 5 ? 'rgb(16,42,76)' : 'var(--color-surface)', fg: stage === 5 ? 'rgb(147,197,253)' : 'var(--color-neutral-600)', stat: `${s.assumptions.length + s.intel.length} claims · ${s.intel.length} reports · ${s.planDocs.length + s.guideDocs.length} documents` },
      hasSubtabs: s.view === 'coa' && [1, 2, 4].includes(s.step),
      subtabs: [['Inputs', 1], ['Options', 2], ['Score', 4]].map(([label, st]) => ({ label, go: () => this.goStep(st), line: s.step === st ? 'var(--color-accent)' : 'transparent', opacity: s.step === st ? 1 : 0.65 })),
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
      planTypes: this.PLAN_TYPES, planType: s.planType, onPlanType: e => this.setState({ planType: e.target.value }), onCcmd: e => this.setState({ ccmd: e.target.value }), threat: s.threat, onThreat: e => this.setState({ threat: e.target.value, coas: [], results: null }),
      isContingency: s.planType === 'CON', levels: this.LEVELS.map((l, i) => ({ label: `L${i + 1}`, on: s.level === i + 1, pick: () => this.setState({ level: i + 1 }) })), levelDesc: this.LEVELS[s.level - 1],
      ccmds: Object.keys(this.CCMDS).map(c => { const a = s.ccmd === c ? on : off; return { label: c, pick: () => this.setState({ ccmd: c }), border: a[0], bg: a[1], fg: a[2] }; }), ccmdDesc: this.CCMDS[s.ccmd],
      threats: Object.keys(this.THREATS).map(k => { const a = s.threat === k ? on : off; return { id: k, label: this.THREATS[k].label, pick: () => this.setState({ threat: k, coas: [], results: null }), border: a[0], bg: a[1], fg: a[2] }; }), threatDesc: T.desc,
      intelCount: s.intel.length, worldState: s.worldState || defaultWorld, onWorldState: set('worldState'),
      intent: s.intent || (s.threat === 'RUS' ? s.planDocs[0].intent : `Deter ${T.name} aggression against allies and partners; if deterrence fails, deny ${T.name} its objectives while limiting escalation beyond the theater and preserving the force for a prolonged campaign.`), onIntent: set('intent'),
      endState: s.endState || (s.threat === 'RUS' ? s.planDocs[0].endState : `${T.name} force projection halted; allied territory and sea lines of communication secure; conditions set for a negotiated settlement.`), onEndState: set('endState'),
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
      best: best ? { n: best.n, title: best.title, reason: `Highest weighted score (${best.pct}%) across ${s.numSims} wargame runs: succeeds ${Math.round(best.pSuccess * 100)} in 100 with ${best.re.toLowerCase()} escalation risk and p90 casualties of ${best.cas.toFixed(1)}%. Weights reflect commander's emphasis on mission and escalation.`, riskAccepted: worstRisk ? `${worstRisk[1]} risk to ${worstRisk[0]} is the governing risk; mitigated through the decision points in the ARC table and the branch plans identified in wargaming.` : '' } : { n: '', title: '', reason: '', riskAccepted: '' },
      ...this.sensitivity(ranked, best, crit),
      weakCount: s.assumptions.filter(isWeak).length,
      evidence: ranked.map(r => { const c = coasNow.find(x => x.n === r.n) || {}; const deps = (c.deps || []).filter(i => s.assumptions[i - 1]).map(i => { const a = s.assumptions[i - 1]; const w = isWeak(a); return { n: i, short: a.text.split(/[,;—]/)[0].slice(0, 70), conf: a.conf, status: this.A_STATUS[a.status][0], bg: w ? this.A_STATUS[a.status === 0 ? 1 : a.status][1] : this.A_STATUS[0][1], fg: w ? this.A_STATUS[a.status === 0 ? 1 : a.status][2] : this.A_STATUS[0][2] }; }); const weak = deps.filter(d => isWeak(s.assumptions[d.n - 1])); return { n: r.n, title: r.title, rank: r.rank, deps, border: r.rank === 1 ? 'var(--color-accent)' : 'var(--color-divider)', verdict: weak.length ? `Stands on thin evidence: ${weak.map(d => 'A' + d.n).join(', ')} ${weak.length === 1 ? 'is' : 'are'} below threshold.` : 'All load-bearing claims validated.', verdictColor: weak.length ? 'rgb(255,203,71)' : 'rgb(76,195,138)' }; }),
      sendWeakToCollection: () => { const existing = new Set(s.pirs.map(p => p.assumption).filter(x => x != null)); const add = s.assumptions.map((a, i) => [a, i]).filter(([a, i]) => isWeak(a) && !existing.has(i)).map(([a, i]) => ({ q: 'Validate: ' + a.text, ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], reports: 0, ltiov: (a.valid || '').replace('Expires ', '') || 'TBD', status: 0, assumption: i })); this.setState({ pirs: [...s.pirs, ...add], view: 'collection' }); },
      weakList: s.assumptions.map((a, i) => ({ a, i })).filter(({ a }) => isWeak(a)).map(({ a, i }) => { const cr = s.pirs.findIndex(p => p.assumption === i); return { n: i + 1, text: a.text, link: a.link || 'unsourced', valid: a.valid || 'unspecified', conf: a.conf, status: this.A_STATUS[a.status][0], bg: this.A_STATUS[a.status][1], fg: this.A_STATUS[a.status][2], bearing: coasNow.filter(c => (c.deps || []).includes(i + 1)).map(c => 'Strategy ' + c.n).join(', ') || 'no option', hasCr: cr >= 0, noCr: cr < 0, crLabel: cr >= 0 ? `PIR ${cr + 1} · ${['Gap', 'Collecting', 'Answered'][s.pirs[cr].status]}` : '', draft: () => this.setState({ pirs: [...s.pirs, { q: 'Validate: ' + a.text, ind: ['Indicators to be defined by J2'], assets: ['Unassigned'], reports: 0, ltiov: (a.valid || '').replace('Expires ', '') || 'TBD', status: 0, assumption: i }] }) }; }),
      noWeak: !s.assumptions.some(isWeak),
      failToggles: s.assumptions.map((a, i) => ({ label: `A${i + 1} fails`, pick: () => this.setState({ failIdx: s.failIdx === i ? null : i }), border: s.failIdx === i ? 'rgb(255,120,120)' : 'var(--color-divider)', bg: s.failIdx === i ? 'rgb(60,20,35)' : 'transparent' })),
      hasFail: s.failIdx != null && !!s.results, failN: (s.failIdx ?? 0) + 1, failText: s.failIdx != null ? s.assumptions[s.failIdx].text : '',
      ...(s.failIdx != null && s.results ? (() => { const alt = this.compute(coasNow, undefined, 600, s.failIdx); const propagation = s.results.map((r, i) => { const d = Math.round((alt[i].pSuccess - r.pSuccess) * 100); const shifts = [['Mission', r.rm, alt[i].rm], ['Personnel', r.rp, alt[i].rp], ['Escalation', r.re, alt[i].re]].filter(x => x[1] !== x[2]).map(x => `${x[0]} ${x[1]} → ${x[2]}`); return { n: r.n, title: r.title, delta: (d > 0 ? '+' : '') + d + ' pts', color: d < -5 ? 'rgb(255,120,120)' : d < 0 ? 'rgb(255,203,71)' : 'var(--color-neutral-600)', riskShift: shifts.join(' · ') || 'Risk levels unchanged' }; }); const sets = (this.PROBLEM_SETS[s.failIdx] || ['Force flow']); const problemSets = sets.map((label, k) => ({ label, hop: k === 0 ? 'Direct' : `${k} hop${k > 1 ? 's' : ''}`, w: Math.max(14, 60 - k * 18), bg: k === 0 ? 'rgb(255,120,120)' : k === 1 ? 'rgb(255,203,71)' : 'rgb(100,116,139)' })); const hit = propagation.filter(p => p.delta.startsWith('-') && parseInt(p.delta) <= -5); return { propagation, problemSets, propagationText: `${hit.length} of ${propagation.length} options degrade materially; the effect reaches ${sets.length} problem set${sets.length > 1 ? 's' : ''} through the graph's edges.` }; })() : { propagation: [], problemSets: [], propagationText: '' }),
      claimCount: s.assumptions.length + s.intel.length,
      claims: [...s.assumptions.map((a, i) => ({ text: a.text, type: 'Assumption', source: a.link || 'unsourced', valid: a.valid || 'unspecified', conf: a.conf, bg: this.A_STATUS[isWeak(a) ? (a.status === 0 ? 1 : a.status) : 0][1], fg: this.A_STATUS[isWeak(a) ? (a.status === 0 ? 1 : a.status) : 0][2], edges: (coasNow.filter(c => (c.deps || []).includes(i + 1)).map(c => 'Strategy ' + c.n).concat(s.pirs.map((p, k) => p.assumption === i ? 'PIR ' + (k + 1) : null).filter(Boolean)).join(', ')) || '—' })), ...s.intel.map(r => { const conf = { A: 90, B: 75, C: 55, D: 40, E: 25, F: 30 }[r.rel[0]] || 50; return { text: r.title, type: r.type, source: r.rel, valid: r.when === 'just now' ? '72 h from receipt' : '72 h from ' + r.when, conf, bg: conf >= 70 ? this.A_STATUS[0][1] : this.A_STATUS[1][1], fg: conf >= 70 ? this.A_STATUS[0][2] : this.A_STATUS[1][2], edges: 'PIR ' + r.pir }; })],
      tradeoffs: ranked.length ? [
        `Fastest to end state: Strategy ${[...ranked].sort((a, b) => a.days - b.days)[0].n} (${[...ranked].sort((a, b) => a.days - b.days)[0].days} days) — ${['Significant', 'High'].includes([...ranked].sort((a, b) => a.days - b.days)[0].re) ? 'but carries' : 'and carries'} ${[...ranked].sort((a, b) => a.days - b.days)[0].re.toLowerCase()} escalation risk.`,
        `Lowest risk to personnel: Strategy ${[...ranked].sort((a, b) => a.cas - b.cas)[0].n} (worst case ${[...ranked].sort((a, b) => a.cas - b.cas)[0].cas.toFixed(1)}% casualties) at the cost of a ${Math.round([...ranked].sort((a, b) => a.cas - b.cas)[0].pSuccess * 100)}% success probability.`,
        `${s.pirs.filter(p => p.status === 0).length} unanswered PIR(s) add uncertainty to every result; answering them tightens the estimates before approval.`
      ] : [],
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
      ipoe: s.threat === 'RUS' ? { likely: 'Russia consolidates its gains in Narva/Ida-Viru and eastern Latgale, transitions to maneuver defense behind a dense mine, obstacle and EW belt, and seeks a negotiated freeze that leaves Russian forces in place. Kaliningrad and Belarus-based forces remain postured but uncommitted to fix Allied forces in Lithuania and Poland. Hybrid pressure continues (cyber, sabotage of undersea cables and rail LOCs, disinformation targeting Baltic Russophones) and nuclear signaling escalates as NATO builds combat power.', dangerous: 'Russia expands the incursion before NATO reinforcement is complete: 1st Guards Tank Army elements reinforce through the Pskov axis toward Tartu and the Daugava; 11th Army Corps and Belarus-based forces conduct a converging attack to close the Suwałki corridor and isolate the Baltic States; the Baltic Fleet mines and strikes to close Klaipėda, Riga and Tallinn and interdict the Danish Straits; and Russia conducts a demonstrative low-yield nuclear detonation over the Baltic Sea to coerce Alliance disunity.', terrain: 'Suwałki corridor (only land LOC to the Baltics); Narva River crossings; Daugava River line through Latgale; Tallinn, Riga and Klaipėda ports; Šiauliai and Ämari airfields; Danish Straits; Gulf of Finland and Gulf of Riga (mine-favorable).' }
        : { likely: `${T.name} escalates gray-zone coercion into a limited seizure of a peripheral objective under cover of an exercise, seeking a fait accompli within 72 hours.`, dangerous: `${T.name} opens with pre-emptive long-range fires on regional bases and cyber attacks on logistics, then commits amphibious and airborne forces simultaneously.`, terrain: 'Maritime chokepoints, forward airfields within 500 nm of the objective, undersea cable landing sites.' },
      pirs: s.pirs.map((p, i) => ({ ...p, n: p.no || i + 1, remove: () => this.setState({ pirs: s.pirs.filter((_, j) => j !== i), results: null }), status: statusMap[p.status][0], bg: statusMap[p.status][1], fg: statusMap[p.status][2], tied: p.assumption != null ? ` · validates A${p.assumption + 1}` : '', cycleLabel: p.status === 2 ? 'Reset' : p.status === 1 ? 'Collection returned' : 'Task assets',
        cycle: () => { const ns = (p.status + 1) % 3; this.setState({ pirs: s.pirs.map((x, j) => j === i ? { ...x, status: ns, reports: ns === 2 ? x.reports + 1 : x.reports } : x), results: null, assumptions: (ns === 2 && p.assumption != null) ? s.assumptions.map((a, k) => k === p.assumption ? { ...a, status: 0, conf: Math.max(a.conf, 85) } : a) : s.assumptions }); } })),
      newPir: s.newPir, onNewPir: set('newPir'), addPir: () => s.newPir.trim() && this.setState({ pirs: [...s.pirs, { q: s.newPir.trim(), ind: ['Indicators to be defined'], assets: ['Unassigned'], reports: 0, ltiov: 'TBD', status: 0 }], newPir: '' }),
      rfis: s.rfis.map(r => ({ ...r, bg: rfiColor[r.status][0], fg: rfiColor[r.status][1] })), newRfi: s.newRfi, onNewRfi: set('newRfi'),
      addRfi: () => s.newRfi.trim() && this.setState({ rfis: [...s.rfis, { id: `RFI-0${35 + s.rfis.length - 4}`, q: s.newRfi.trim() + (s.newRfiLtiov ? ` (LTIOV ${s.newRfiLtiov})` : ''), to: s.newRfiRoute || 'J2', ties: s.newRfiTies || 'Unlinked', status: 'Open' }], newRfi: '', newRfiTies: '', newRfiLtiov: '', rfiOpen: false }),
      rfiOpen: !!s.rfiOpen, openRfi: () => this.setState({ rfiOpen: true }), closeRfi: () => this.setState({ rfiOpen: false }), stop: e => e.stopPropagation(),
      rfiRoutes: ['J2 / DIA', 'J4', 'J5', 'Interagency'].map(r => ({ label: r, on: (s.newRfiRoute || 'J2 / DIA') === r, pick: () => this.setState({ newRfiRoute: r }) })),
      newRfiTies: s.newRfiTies || '', onNewRfiTies: set('newRfiTies'), newRfiLtiov: s.newRfiLtiov || '', onNewRfiLtiov: set('newRfiLtiov'),
      postureStats: [{ label: 'Component commands', value: '5' }, { label: 'Designated for AMBER SHIELD', value: '11 packages' }, { label: 'C-1 / C-2 ready', value: '78%' }, { label: 'Peak strategy demand', value: `${Math.max(...this.buildCoas().map(c => c.res))}%` }],
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
