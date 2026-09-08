"""P5 collection requirements. Priority and rank are computed by eval.engine."""

REQUIREMENTS = [
    ('req_01', 'pir_02', 'Will Corvane grant access to Halden Airfield?',
     ['A signed access decision', 'Blue aircraft cleared to use Halden'],
     'Obtain Corvane government confirmation of basing access.', 'missing',
     'ent_corvane', 'basing_access', 'asm_blue_1_k2', 'JIOC', 55),
    ('req_02', 'pir_03', 'What is the effective range of the Dorne-3 system?',
     ['Instrumented launch telemetry', 'Deployment geometry consistent with extended range'],
     'Determine Dorne-3 effective range to within ten kilometres.', 'low_confidence',
     'sys_dorne_asm', 'range_km', 'asm_blue_1_k0', 'JCMB', 25),
    ('req_03', 'pir_01', 'How fast can Varenia mobilize two brigades?',
     ['Two brigades leave garrison', 'Sustainment trains assemble on Kessary Plain'],
     'Determine the elapsed days required to mobilize two brigades.', 'stale',
     'ent_varenia', 'mobilization_days', 'asm_blue_3_k1', 'JIOC', 20),
    ('req_04', 'pir_04', 'Can Varenia disrupt Blue sustainment networks?',
     ['Access attempts against logistics nodes', 'Command links to offensive network units'],
     'Assess Varenian cyber capacity against Blue logistics.', 'low_confidence',
     'ent_varenia', 'cyber_capacity', 'asm_blue_2_k4', 'JCMB', 65),
    ('req_05', 'pir_03', 'How many Serath launchers are operational?',
     ['Launcher signatures at Serath', 'Missile support vehicles active'],
     'Count operational Serath launchers.', 'low_confidence',
     'sys_serath_lrs', 'count', None, 'component J-2', 75),
    ('req_06', 'pir_01', 'Is Sondria moving toward Varenia?',
     ['Security cooperation with Varenia', 'Restrictions on Ilmaran access'],
     'Determine Sondrian political alignment.', 'low_confidence',
     'ent_sondria', 'alignment', None, 'component J-2', 75),
]


def build(ctx):
    for rid, pir, eei, indicators, sir, gap, subject, predicate, assumption, routing, days in REQUIREMENTS:
        ctx.add('collection_requirements', dict(req_id=rid, pir_id=pir, eei=eei,
            indicators=indicators, sir=sir, gap_type=gap, subject_id=subject, predicate=predicate,
            assumption_id=assumption, rfi_disposition='gap_confirmed', routing=routing,
            ltiov=ctx.day(days), created_at=ctx.day(0), status='research'))
