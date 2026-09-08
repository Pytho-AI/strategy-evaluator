"""Worked instantiation A: rock-paper-scissors as game_id 'rps' (v2 §2.9). Smallest cardinality
of the same 6-tuple so the schema is visibly generic. One document, two facts, two P1 strategies
(the spec's mixed-uniform policy plus a pure 'always paper' policy that would exploit a biased P2)."""
from __future__ import annotations

from gen.context import Ctx
from gen.render_common import product_header, product_footer, locate_span


def build(ctx: Ctx) -> None:
    p1 = ctx.add("entities", {"entity_id": "ent_rps_p1", "entity_type": "actor", "canonical_name": "Player 1", "aliases": ["P1"], "description": "rock-paper-scissors player one"})
    p2 = ctx.add("entities", {"entity_id": "ent_rps_p2", "entity_type": "actor", "canonical_name": "Player 2", "aliases": ["P2"], "description": "rock-paper-scissors player two"})
    ctx.add("games", {"game_id": "rps", "name": "rock-paper-scissors", "actor_ids": [p1["entity_id"], p2["entity_id"]], "horizon": 1,
                      "horizon_map": [{"period": 1, "jsps_horizon": "near"}], "state_variables": [], "observables": []})
    for actor in (p1, p2):
        tag = actor["entity_id"].split("_")[-1]
        for mv in ("rock", "paper", "scissors"):
            ctx.add("actions", {"action_id": f"act_rps_{tag}_{mv}", "game_id": "rps", "actor_id": actor["entity_id"], "name": f"play {mv}",
                                "tactic_class": "signal", "line_of_effort": "play", "mechanism": "play", "cost": {}, "preconditions": True, "effects": []})
    ctx.add("actions", {"action_id": "act_rps_p1_paper_commit", "game_id": "rps", "actor_id": p1["entity_id"], "name": "commit to paper",
                        "tactic_class": "signal", "line_of_effort": "exploit", "mechanism": "exploit", "cost": {}, "preconditions": True, "effects": []})
    # objectives and a minimal guidance row so the suitable test is not vacuous
    ctx.add("guidance", {"guidance_id": "gd_rps_rules", "product_type": "OPORD", "title": "Rules of play: achieve a non-negative expected score",
                         "issuing_role": "game referee", "parent_guidance_id": None, "objective_ids": ["obj_rps_p1_score", "obj_rps_p2_score"], "source_id": None})
    for actor in (p1, p2):
        tag = actor["entity_id"].split("_")[-1]
        ctx.add("objectives", {"objective_id": f"obj_rps_{tag}_end", "game_id": "rps", "actor_id": actor["entity_id"], "name": "game concluded without a losing record",
                               "kind": "end_state", "guidance_id": "gd_rps_rules", "metric": "final score sign", "direction": "max", "aspiration": None})
        ctx.add("objectives", {"objective_id": f"obj_rps_{tag}_score", "game_id": "rps", "actor_id": actor["entity_id"], "name": "expected score",
                               "kind": "objective", "guidance_id": "gd_rps_rules", "parent_objective_id": f"obj_rps_{tag}_end", "metric": "expected score in {-1, 0, +1}",
                               "direction": "max", "aspiration": 0.0, "statement": "Achieve a non-negative expected score"})
    # facts and the one document
    facts = []
    for actor in (p1, p2):
        facts.append(ctx.add("facts", {"fact_id": f"fct_rps_{actor['entity_id'].split('_')[-1]}_bias", "subject_id": actor["entity_id"], "predicate": "mixing_bias",
                                       "value": 0.0, "value_type": "number", "unit": "fraction", "valid_from": ctx.day(-30), "valid_to": None,
                                       "estimative": False, "likelihood_icd203": None, "confidence_icd203": "high", "confidence": 0.97, "first_asserted_batch": 0}))
    body = [
        "Reference Entry: Rock-Paper-Scissors Players",
        "1. Purpose. This entry records the observed mixing behaviour of the two players in the reference game rock-paper-scissors.",
        "2. Players.",
        "a. Player 1 (also P1) has a mixing bias of 0.0 across the last thirty sessions, playing rock, paper and scissors with equal frequency [src: src_rps_0001].",
        "b. Player 2 (also P2) has a mixing bias of 0.0 over the same sessions [src: src_rps_0001].",
        "3. Sources. src_rps_0001 is the session log kept by the referee: reliability A, credibility 1. Both entries are reported facts, not analytic judgments. Confidence in the log is high.",
    ]
    text = product_header() + "\n".join(body) + "\n" + product_footer([])
    rel = "corpus/rps_reference_0001.md"
    sha = ctx.add_doc(rel, text)
    ctx.add("sources", {"source_id": "src_rps_0001", "doc_type": "reference_entry", "title": "Reference Entry: Rock-Paper-Scissors Players", "published_at": ctx.day(0),
                        "author_org": "game referee", "reliability": "A", "credibility": "1", "real_world": False, "public_reference": None,
                        "path": rel, "batch": 0, "text_sha256": sha, "perturbations": ["alias"]})
    claims = []
    for f, needle in zip(facts, ["Player 1 (also P1) has a mixing bias of 0.0", "Player 2 (also P2) has a mixing bias of 0.0"]):
        s, e = locate_span(text, needle)
        claims.append(ctx.add("claims", {"claim_id": f"clm_rps_{f['subject_id'].split('_')[-1]}_bias", "subject_id": f["subject_id"], "predicate": "mixing_bias", "value": 0.0,
                                         "value_type": "number", "unit": "fraction", "source_id": "src_rps_0001", "span_start": s, "span_end": e, "asserted_at": ctx.day(0),
                                         "valid_from": f["valid_from"], "valid_to": None, "estimative": False, "likelihood_icd203": None, "confidence_icd203": "high",
                                         "confidence": 0.97, "status": "approved", "supersedes_claim_id": None, "truth_claim_id": f["fact_id"]}))
    # opponent models
    ctx.add("opponent_models", {"opponent_model_id": "om_rps_p2", "actor_id": p2["entity_id"], "distribution": [{"strategy_id": "str_rps_p2_uniform", "probability": 1.0}]})
    ctx.add("opponent_models", {"opponent_model_id": "om_rps_p1", "actor_id": p1["entity_id"], "distribution": [{"strategy_id": "str_rps_p1_uniform", "probability": 1.0}]})

    def strategy(sid, actor, name, summary, main_effort, mechanism_label, rules, om, k_subject, k_statement):
        tag = actor["entity_id"].split("_")[-1]
        ctx.add("strategies", {
            "strategy_id": sid, "game_id": "rps", "actor_id": actor["entity_id"], "name": name, "summary": summary, "echelon": "tactical",
            "guidance_source": "gd_rps_rules", "mission_who": actor["canonical_name"], "mission_what": "plays one round of rock-paper-scissors",
            "mission_when": "on the referee's signal", "mission_where": "at the table", "mission_why": "to achieve a non-negative expected score",
            "end_state_objective_id": f"obj_rps_{tag}_end", "constraints": ["must show exactly one hand on the signal"], "restraints": ["cannot observe the opponent's hand before the signal"],
            "main_effort": main_effort, "sequencing": "simultaneous", "task_org": [actor["entity_id"]], "reserve_policy": "none", "mitigates_he_ids": [],
            "risk_functional": "expected", "risk_alpha": None, "opponent_model_id": om, "theory_of_victory": [],
        })
        ctx.add("strategy_objectives", {"strategy_id": sid, "objective_id": f"obj_rps_{tag}_score", "weight": 1.0})
        for i, (aid, pr) in enumerate(rules):
            ctx.add("policy_rules", {"rule_id": f"rule_{sid[4:]}_{i}", "strategy_id": sid, "priority": 0, "condition": True, "action_id": aid, "probability": pr,
                                     "periods": None, "rationale_claim_ids": [claims[1]["claim_id"] if tag == "p1" else claims[0]["claim_id"]], "decision_point_id": None})
        ctx.add("assumptions", {"assumption_id": f"asm_{sid[4:]}_k0", "strategy_id": sid, "index_k": 0, "statement": k_statement, "subject_id": k_subject, "predicate": "mixing_bias",
                                "tolerance": {"op": "abs_le", "value": 0.05}, "role": "opponent", "jp50_logical": True, "jp50_realistic": True, "jp50_essential": True,
                                "origin": "own", "in_decision_matrix": True})
        return sid

    uniform_rules = lambda tag: [(f"act_rps_{tag}_rock", 1 / 3), (f"act_rps_{tag}_paper", 1 / 3), (f"act_rps_{tag}_scissors", 1 / 3)]
    s1 = strategy("str_rps_p1_uniform", p1, "mixed uniform", "Play rock, paper and scissors each with probability one third; unexploitable against any opponent.",
                  "play", "play", uniform_rules("p1"), "om_rps_p2", p2["entity_id"], "Player 2 plays uniformly (mixing bias within 0.05 of zero).")
    s2 = strategy("str_rps_p1_paper", p1, "always paper", "Commit to paper every round; wins against a rock-biased opponent and is exploitable otherwise.",
                  "exploit", "exploit", [("act_rps_p1_paper_commit", 1.0)], "om_rps_p2", p2["entity_id"], "Player 2 plays uniformly (mixing bias within 0.05 of zero).")
    s3 = strategy("str_rps_p2_uniform", p2, "mixed uniform", "Play rock, paper and scissors each with probability one third.",
                  "play", "play", uniform_rules("p2"), "om_rps_p1", p1["entity_id"], "Player 1 plays uniformly (mixing bias within 0.05 of zero).")
    # dependencies: grounds, requires, theory-of-victory chains
    for sid, subj_claim in ((s1, claims[1]), (s2, claims[1]), (s3, claims[0])):
        ctx.add("dependencies", {"edge_id": f"dep_{sid[4:]}_grounds", "from_type": "claim", "from_id": subj_claim["claim_id"], "to_type": "assumption", "to_id": f"asm_{sid[4:]}_k0",
                                 "kind": "grounds", "weight": 1.0, "mechanism": "the mixing-bias claim decides whether the opponent is uniform", "evidence_claim_ids": [subj_claim["claim_id"]]})
        ctx.add("dependencies", {"edge_id": f"dep_{sid[4:]}_requires", "from_type": "assumption", "from_id": f"asm_{sid[4:]}_k0", "to_type": "strategy", "to_id": sid,
                                 "kind": "requires", "weight": 1.0, "mechanism": "the policy is optimal only if the opponent is uniform", "evidence_claim_ids": []})
    chains = {
        s1: ("act_rps_p1_rock", claims[0]["claim_id"], "obj_rps_p1_score", "obj_rps_p1_end"),
        s2: ("act_rps_p1_paper_commit", claims[0]["claim_id"], "obj_rps_p1_score", "obj_rps_p1_end"),
        s3: ("act_rps_p2_rock", claims[1]["claim_id"], "obj_rps_p2_score", "obj_rps_p2_end"),
    }
    for sid, (act, clm, obj, end) in chains.items():
        e1 = ctx.add("dependencies", {"edge_id": f"dep_{sid[4:]}_tov1", "from_type": "action", "from_id": act, "to_type": "claim", "to_id": clm, "kind": "enables", "weight": 1.0,
                                      "mechanism": "playing the policy produces the player's own mixing behaviour", "evidence_claim_ids": [clm]})
        e2 = ctx.add("dependencies", {"edge_id": f"dep_{sid[4:]}_tov2", "from_type": "claim", "from_id": clm, "to_type": "objective", "to_id": obj, "kind": "supports", "weight": 1.0,
                                      "mechanism": "an unexploitable mix secures a non-negative expected score", "evidence_claim_ids": [clm]})
        e3 = ctx.add("dependencies", {"edge_id": f"dep_{sid[4:]}_tov3", "from_type": "objective", "from_id": obj, "to_type": "objective", "to_id": end, "kind": "supports", "weight": 1.0,
                                      "mechanism": "the score objective defines the end state", "evidence_claim_ids": []})
        ctx.get("strategies", strategy_id=sid)["theory_of_victory"] = [e1["edge_id"], e2["edge_id"], e3["edge_id"]]
    # payoffs: u = base + theta_0 * delta. P1 uniform is 0 in both worlds; 'always paper' gains 0.3 when
    # P2 is rock-biased (theta_0 = 0) and loses 0.05 to predictability when P2 is uniform (theta_0 = 1).
    pay = {
        (s1, s3, "0"): [0.0], (s1, s3, "1"): [0.0],
        (s2, s3, "0"): [0.3], (s2, s3, "1"): [-0.05],
        (s3, s1, "0"): [0.0], (s3, s1, "1"): [0.0],
    }
    for (a, b, w), u in pay.items():
        ctx.add("payoffs", {"strategy_id": a, "opponent_strategy_id": b, "world": w, "utility": u})
