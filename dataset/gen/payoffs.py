"""Structured finite payoff tensor: base + sum(theta[k] * delta[k]) + seeded noise.

Coefficients are scenario utility judgments, not doctrinal scores. Nonzero deltas follow the
authored assumption dependencies. Objective-specific profiles let the ordinal table differ by criterion.
"""
import random
from eval.engine import objective_order
from eval.value import world_bits

BASE = {'str_blue_1': 0.0, 'str_blue_2': .47, 'str_blue_3': .38}
DELTA = {
    'str_blue_1': [.36, 0, .59, .02, 0, .02],
    'str_blue_2': [.005, 0, 0, .07, .07, .06],
    'str_blue_3': [0, .08, .12, 0, 0, .10],
}


def build(ctx):
    for s in ctx.tables['strategies']:
        sid, actor = s['strategy_id'], s['actor_id']
        if s['game_id'] != 'meridian':
            continue
        order = objective_order(ctx.tables, 'meridian', actor)
        opponents = ctx.get('opponent_models', opponent_model_id=s['opponent_model_id'])['distribution']
        for opp in opponents:
            osid = opp['strategy_id']
            for world in world_bits(6 if actor == 'ent_blue' else 1):
                rng = random.Random(f'{ctx.seed}:payoff:{sid}:{osid}:{world}')
                if actor == 'ent_blue':
                    scalar = BASE[sid] + sum(int(bit)*d for bit, d in zip(world, DELTA[sid]))
                    shift = {'str_red_ml': .003, 'str_red_md': -.006, 'str_red_alt': -.001}[osid]
                    utility = [round(scalar + shift + rng.uniform(-.001, .001), 9) for _ in order]
                else:
                    utility = [round(.62 - .08*int(world) + rng.uniform(-.01, .01), 9) for _ in order]
                ctx.add('payoffs', dict(strategy_id=sid, opponent_strategy_id=osid, world=world, utility=utility))
