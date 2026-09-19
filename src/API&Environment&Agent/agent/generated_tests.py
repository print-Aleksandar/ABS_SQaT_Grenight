import copy
import torch
from domain.configs import ROWS, COLUMNS
from domain.pieces import Pawn, Rook, King, Queen
from environment.grenight_environment import (
    GrenightEnvironment,
    rotate_pieces_helper,
)


AGENT_VERSIONS = [
    ("S111111", 10_000, True, True, True,  True, True, True),
    ("S110111", 10_000, True, True, False, True, True, True),
    ("S111110", 10_000, True, True, True,  True, True, False),
    ("S110110", 10_000, True, True, False, True, True, False),
]

PROMO_ROOK = 1
PROMO_QUEEN = 2


def free_pawn_captures():
    return [
        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Pawn('w3p', True, (3, 1), True),
          Queen('bq', False, (4, 2), True)],
         "White pawn b4 x free black queen c5",
         (3, 1), (4, 2), "free_capture"),

        ([King('wk', True,  (4, 3), False),
          King('bk', False, (4, 0), False),
          Pawn('b1p', False, (1, 2), True),
          Rook('wr', True, (0, 1), True)],
         "Black pawn c2 x free white rook b1",
         (1, 2), (0, 1), "free_capture"),

        ([King('wk', True,  (0, 3), False),
          King('bk', False, (0, 0), False),
          Pawn('w3p', True, (3, 0), True),
          Rook('br', False, (4, 1), True)],
         "White pawn a4 x free black rook b5",
         (3, 0), (4, 1), "free_capture"),

        ([King('wk', True,  (4, 1), False),
          King('bk', False, (4, 3), False),
          Pawn('b1p', False, (1, 3), True),
          Queen('wq', True, (0, 2), True)],
         "Black pawn d2 x free white queen c1",
         (1, 3), (0, 2), "free_capture"),
    ]


def free_rook_captures():
    return [
        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('wr', True, (2, 0), True),
          Queen('bq', False, (2, 3), True)],
         "White rook a3 x free black queen d3",
         (2, 0), (2, 3), "free_capture"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('br', False, (3, 3), True),
          Rook('wr', True, (3, 0), True)],
         "Black rook d4 x free white rook a4",
         (3, 3), (3, 0), "free_capture"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('wr', True, (2, 1), True),
          Pawn('b2p', False, (2, 3), True)],
         "White rook b3 x free black pawn d3",
         (2, 1), (2, 3), "free_capture"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('br', False, (1, 3), True),
          Pawn('w1p', True, (1, 1), True)],
         "Black rook d2 x free white pawn b2",
         (1, 3), (1, 1), "free_capture"),
    ]


def free_queen_captures():
    return [
        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Queen('wq', True, (2, 1), True),
          Rook('br', False, (2, 3), True)],
         "White queen b3 x free black rook d3",
         (2, 1), (2, 3), "free_capture"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Queen('bq', False, (1, 1), True),
          Rook('wr', True, (3, 1), True)],
         "Black queen b2 x free white rook b4",
         (1, 1), (3, 1), "free_capture"),

        ([King('wk', True,  (0, 1), False),
          King('bk', False, (0, 3), False),
          Queen('wq', True, (4, 0), True),
          Rook('br', False, (4, 3), True)],
         "White queen a5 x free black rook d5",
         (4, 0), (4, 3), "free_capture"),
    ]


def immediate_mating_moves():
    mate1 = ([King('wk', True,  (0, 3), False),
              King('bk', False, (4, 1), False),
              Pawn('b1p', False, (3, 1), True),
              Pawn('b2p', False, (3, 2), True),
              Pawn('b3p', False, (3, 3), True),
              Rook('wr', True, (2, 0), True)],
             "White Ra3 -> a5 (4,0) = back-rank mate",
             (2, 0), (4, 0), "mate")

    mate2 = ([King('wk', True,  (0, 0), False),
              Pawn('w1p', True, (1, 0), True),
              Pawn('w2p', True, (0, 1), True),
              King('bk', False, (4, 0), False),
              Rook('br', False, (4, 3), True)],
             "Black Rd5 -> d1 (0,3) = mate",
             (4, 3), (0, 3), "mate")

    mate3 = ([King('wk', True,  (0, 3), False),
              King('bk', False, (4, 2), False),
              Pawn('b1p', False, (3, 1), True),
              Pawn('b2p', False, (3, 2), True),
              Pawn('b3p', False, (3, 3), True),
              Queen('wq', True, (2, 0), True)],
             "White Qa3 -> a5 (4,0) = back-rank mate",
             (2, 0), (4, 0), "mate")

    return [mate1, mate2, mate3]


def checking_is_bad():
    s1 = ([King('wk', True,  (0, 0), False),
           King('bk', False, (4, 2), False),
           Queen('wq', True, (2, 0), True),
           Rook('br', False, (2, 3), True)],
          "White Qc3+ (to 2,2) hangs to ...Rxc3",
          (2, 0), (2, 2), "bad_check")

    s2 = ([King('wk', True,  (0, 0), False),
           King('bk', False, (4, 2), False),
           Rook('wr', True, (3, 0), True),
           Rook('br', False, (3, 3), True)],
          "White Ra4+ (to 4,0) allows ...Ra1+ skewer",
          (3, 0), (4, 0), "bad_check")

    s3 = ([King('wk', True,  (0, 1), False),
           King('bk', False, (4, 3), False),
           Queen('wq', True, (2, 2), True),
           Rook('br', False, (2, 0), True)],
          "White Qc3+ (to 2,3) hangs to ...Rxc3 along rank 2",
          (2, 2), (2, 3), "bad_check")

    return [s1, s2, s3]


def promotion_situations():
    p1 = ([King('wk', True,  (0, 3), False),
           King('bk', False, (0, 0), False),
           Pawn('w3p', True, (3, 0), True)],
          "White pawn a4 -> a5 (row 4) promotion",
          (3, 0), (4, 0), "promotion")

    p2 = ([King('wk', True,  (4, 3), False),
           King('bk', False, (4, 0), False),
           Pawn('b1p', False, (1, 3), True)],
          "Black pawn d2 -> d1 (row 0) promotion",
          (1, 3), (0, 3), "promotion")

    p3 = ([King('wk', True,  (0, 3), False),
           King('bk', False, (0, 0), False),
           Pawn('w3p', True, (3, 1), True),
           Rook('br', False, (4, 2), True)],
          "White pawn b4 x rook c5 with promotion",
          (3, 1), (4, 2), "promotion")

    p4 = ([King('wk', True,  (4, 3), False),
           King('bk', False, (4, 0), False),
           Pawn('b1p', False, (1, 2), True),
           Queen('wq', True, (0, 1), True)],
          "Black pawn c2 x queen b1 with promotion",
          (1, 2), (0, 1), "promotion")

    return [p1, p2, p3, p4]


def poisoned_captures():
    s1 = ([King('wk', True,  (4, 3), False),
           King('bk', False, (4, 0), False),
           Queen('wq', True, (2, 1), True),
           Pawn('b1p', False, (1, 1), True),
           Pawn('b2p', False, (0, 0), True)],
          "White Qxb2?? poisoned by axb2",
          (2, 1), (1, 1), "poisoned")

    s2 = ([King('wk', True,  (0, 0), False),
           King('bk', False, (0, 3), False),
           Rook('wr', True, (2, 0), True),
           Pawn('b1p', False, (2, 1), True),
           Rook('br', False, (2, 3), True)],
          "White Rxb2?? poisoned by ...Rxb2",
          (2, 0), (2, 1), "poisoned")

    s3 = ([King('wk', True,  (4, 2), False),
           King('bk', False, (4, 0), False),
           Queen('wq', True, (0, 1), True),
           Pawn('b1p', False, (0, 0), True),
           Queen('bq', False, (3, 0), True)],
          "White Qxa1?? poisoned by ...Qxa1",
          (0, 1), (0, 0), "poisoned")

    return [s1, s2, s3]


def behavioral_checks():
    return [
        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 2), False),
          Queen('wq', True, (2, 1), True),
          Rook('br', False, (2, 3), True)],
         "Qc3+ loses queen to ...Rxc3 (should avoid)",
         (2, 1), (2, 2), "behavioral_check"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 2), False),
          Rook('wr', True, (3, 1), True),
          Rook('br', False, (3, 3), True)],
         "Rc4+ walks into ...Rc1+ skewer (should avoid)",
         (3, 1), (4, 1), "behavioral_check"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 1), False),
          Queen('wq', True, (3, 2), True),
          Rook('br', False, (4, 3), True)],
         "Qd4+ is a pointless check, rook recaptures if queen enters",
         (3, 2), (3, 3), "behavioral_check"),
    ]


def behavioral_material():
    return [
        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('wr', True, (2, 1), True),
          Rook('br', False, (2, 3), True)],
         "Rxb3 takes a free rook (should play)",
         (2, 1), (2, 3), "behavioral_material"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('wr', True, (2, 1), True),
          Pawn('b2p', False, (2, 3), True)],
         "Rxd3 takes a free pawn (should play)",
         (2, 1), (2, 3), "behavioral_material"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Rook('wr', True, (2, 0), True),
          Queen('bq', False, (2, 3), True)],
         "Rxd3 takes a free queen (should play)",
         (2, 0), (2, 3), "behavioral_material"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (0, 3), False),
          Pawn('w2p', True, (2, 1), True),
          Rook('br', False, (3, 2), True)],
         "Pawn b3 x rook c4 (should play)",
         (2, 1), (3, 2), "behavioral_material"),
    ]


def behavioral_rook():
    return [
        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 3), False),
          Rook('wr', True, (2, 0), True)],
         "Rook a3 -> d3 (open-file activity)",
         (2, 0), (2, 3), "behavioral_rook"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 2), False),
          Rook('wr', True, (2, 1), True)],
         "Rook b3 -> d3 (advance toward enemy king)",
         (2, 1), (2, 3), "behavioral_rook"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 0), False),
          Rook('wr', True, (2, 2), True)],
         "Rook c3 -> c5 (4th rank, cut off king)",
         (2, 2), (4, 2), "behavioral_rook"),
    ]


def behavioral_mates():
    return [
        ([King('wk', True,  (0, 3), False),
          King('bk', False, (4, 0), False),
          Pawn('b1p', False, (3, 0), True),
          Pawn('b2p', False, (3, 1), True),
          Queen('wq', True, (2, 2), True)],
         "White Qc3 -> c5 (4,2) = corner mate",
         (2, 2), (4, 2), "behavioral_mate"),

        ([King('wk', True,  (0, 2), False),
          King('bk', False, (4, 0), False),
          Pawn('b1p', False, (3, 0), True),
          Pawn('b2p', False, (3, 1), True),
          Rook('wr', True, (2, 3), True)],
         "White Rd3 -> d5 (4,3) = rank mate",
         (2, 3), (4, 3), "behavioral_mate"),

        ([King('wk', True,  (0, 0), False),
          King('bk', False, (4, 2), False),
          Pawn('b1p', False, (3, 2), True),
          Queen('wq', True, (0, 1), True)],
         "White Qb1 -> b5 (4,1) = rank mate",
         (0, 1), (4, 1), "behavioral_mate"),
    ]


def promotion_choice():
    return [
        ([King('wk', True,  (0, 3), False),
          King('bk', False, (0, 0), False),
          Pawn('w3p', True, (3, 0), True)],
         "Promotion on empty square: R vs Q",
         (3, 0), (4, 0), "promo_choice"),

        ([King('wk', True,  (0, 3), False),
          King('bk', False, (0, 0), False),
          Pawn('w3p', True, (3, 1), True),
          Rook('br', False, (4, 2), True)],
         "Capture-promotion on rook: R vs Q",
         (3, 1), (4, 2), "promo_choice"),
    ]


ALL_SCENARIOS = [
    ("FREE PAWN CAPTURES",     free_pawn_captures()),
    ("FREE ROOK CAPTURES",     free_rook_captures()),
    ("FREE QUEEN CAPTURES",    free_queen_captures()),
    ("IMMEDIATE MATING MOVES", immediate_mating_moves()),
    ("CHECKING IS BAD",        checking_is_bad()),
    ("PROMOTION SITUATIONS",   promotion_situations()),
    ("POISONED CAPTURES",      poisoned_captures()),
    ("BEHAVIORAL: CHECKS",     behavioral_checks()),
    ("BEHAVIORAL: MATERIAL",   behavioral_material()),
    ("BEHAVIORAL: ROOKS",      behavioral_rook()),
    ("BEHAVIORAL: MATES",      behavioral_mates()),
    ("BEHAVIORAL: PROMO CHOICE", promotion_choice()),
]


def build_env_for(pieces, is_white_on_turn, is_canonical):
    env = GrenightEnvironment(
        is_canonical_version=is_canonical
    )
    env.reset()

    mirrored = is_canonical and not is_white_on_turn
    if mirrored:
        new_pieces = copy.deepcopy(pieces)
        rotate_pieces_helper(new_pieces)
        env.pieces = new_pieces
    else:
        env.pieces = pieces

    env.is_white_on_turn = True
    env._invalidate_legal_actions_cache()
    env._state_cache = None
    env.position_counts = {}
    key = env.position_key()
    env.current_repetition_count = 1
    env.position_counts[key] = 1

    return env, mirrored


def decode_action(env, action):
    if env.action_encoder.is_promotion_action(action):
        f, t, p = env.action_encoder.decode_promotion(action, True)
        suffix = {PROMO_ROOK: "=R", PROMO_QUEEN: "=Q"}.get(p, f"={p}")
        return f, t, suffix
    f, t = env.action_encoder.decode(action)
    return f, t, ""


def find_target_action(env, from_pos, to_pos, mirrored):
    if mirrored:
        from_pos = (ROWS - 1 - from_pos[0], from_pos[1])
        to_pos   = (ROWS - 1 - to_pos[0],   to_pos[1])

    for a in env.legal_actions():
        f, t, _ = decode_action(env, a)
        if f == from_pos and t == to_pos:
            return a
    return None


def promotion_q_for(env, q, legal, from_pos, to_pos, promote_to, mirrored):
    if mirrored:
        from_pos = (ROWS - 1 - from_pos[0], from_pos[1])
        to_pos   = (ROWS - 1 - to_pos[0],   to_pos[1])
    for a in legal:
        if env.action_encoder.is_promotion_action(a):
            f, t, p = env.action_encoder.decode_promotion(a, True)
            if f == from_pos and t == to_pos and p == promote_to:
                return float(q[a])
    return float("nan")


def q_values_for(agent, state, mask):
    with torch.no_grad():
        state_t = torch.from_numpy(state).unsqueeze(0).to(agent.device)
        mask_t = (
            None if not agent.is_dueling_net
            else torch.from_numpy(mask).unsqueeze(0).to(agent.device)
        )
        return agent._q(agent.policy_net, state_t, mask_t).squeeze(0).cpu().numpy()


PASS_HEURISTICS = {
    "free_capture":        lambda rank, n: rank == 1,
    "mate":                lambda rank, n: rank == 1,
    "promotion":           lambda rank, n: rank is not None and rank <= 3,
    "bad_check":           lambda rank, n: rank is not None and rank > 1,
    "poisoned":            lambda rank, n: rank is not None and rank > 1,
    "behavioral_check":    lambda rank, n: rank is not None and rank > 1,
    "behavioral_material": lambda rank, n: rank == 1,
    "behavioral_rook":     lambda rank, n: rank is not None and rank <= 3,
    "behavioral_mate":     lambda rank, n: rank == 1,
    "promo_choice":        lambda rank, n: rank is not None and rank <= 2,
}


def inspect_scenario(agent, is_canonical, title, scenarios, results):
    print("=" * 78)
    print(f"  {title}")
    print("=" * 78)

    for pieces, desc, from_pos, to_pos, kind in scenarios:
        mover = next(p for p in pieces if p.position == from_pos)
        is_white_on_turn = mover.is_white

        env, mirrored = build_env_for(pieces, is_white_on_turn, is_canonical)
        state = env.get_state()
        mask = env.action_mask()

        q = q_values_for(agent, state, mask)
        legal = env.legal_actions()

        if not legal:
            print(f"\n  [{kind}]  {desc}")
            print("    !! no legal moves in this position; scenario is broken. Skipping.")
            results.append({
                "category": title, "kind": kind, "desc": desc,
                "rank": None, "n_legal": 0,
                "target_q": float("nan"), "best_q": float("nan"),
                "gap": float("nan"), "passed": False,
            })
            continue

        legal_q = q[legal]
        target_action = find_target_action(env, from_pos, to_pos, mirrored)

        if target_action is None:
            rank, target_q, gap = None, float("nan"), float("nan")
        else:
            target_q = float(q[target_action])
            sorted_legal = sorted(legal, key=lambda a: -q[a])
            rank = sorted_legal.index(target_action) + 1
            gap = float(legal_q.max() - target_q)

        passed = (rank is not None) and PASS_HEURISTICS[kind](rank, len(legal))

        header = f"\n  [{kind}]  {desc}"
        if mirrored:
            header += "   (mirrored to canonical)"
        print(header)
        print(f"    side to move        : {'White' if is_white_on_turn else 'Black'}")
        print(f"    # legal moves       : {len(legal)}")
        print(f"    target move index   : {target_action}")
        print(f"    target Q            : {target_q: .4f}")
        print(f"    rank among legal    : {rank} / {len(legal)}")
        print(f"    best Q              : {legal_q.max(): .4f}")
        print(f"    gap (best - target) : {gap: .4f}")
        print(f"    mean / min Q (legal): {legal_q.mean(): .4f} / {legal_q.min(): .4f}")
        print(f"    verdict             : {'PASS' if passed else 'FAIL'}")

        top3 = sorted(legal, key=lambda a: -q[a])[:3]
        for i, a in enumerate(top3, start=1):
            f, t, suffix = decode_action(env, a)
            print(f"      #{i}: {f}->{t}{suffix}  Q={q[a]: .4f}")

        if kind == "promo_choice":
            r_q = promotion_q_for(env, q, legal, from_pos, to_pos,
                                  PROMO_ROOK, mirrored)
            q_q = promotion_q_for(env, q, legal, from_pos, to_pos,
                                  PROMO_QUEEN, mirrored)
            preferred = "=" if abs(r_q - q_q) < 1e-6 else ("R" if r_q > q_q else "Q")
            print(f"      =R Q: {r_q: .4f}   =Q Q: {q_q: .4f}   prefers: {preferred}")

        results.append({
            "category": title,
            "kind": kind,
            "desc": desc,
            "rank": rank,
            "n_legal": len(legal),
            "target_q": target_q,
            "best_q": float(legal_q.max()),
            "gap": gap,
            "passed": passed,
        })


def print_summary(results):
    print("\n" + "=" * 78)
    print("  SUMMARY")
    print("=" * 78)

    by_cat = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)

    for cat, rs in by_cat.items():
        n_pass = sum(1 for r in rs if r["passed"])
        print(f"\n  {cat}: {n_pass}/{len(rs)} pass")
        for r in rs:
            status = "PASS" if r["passed"] else "FAIL"
            rank_s = f"{r['rank']}/{r['n_legal']}" if r["rank"] else "—"
            gap_s = f"{r['gap']: .3f}" if r["gap"] == r["gap"] else "  nan"
            print(f"    [{status}] rank={rank_s:>7}  "
                  f"gap={gap_s}  {r['desc']}")

    total_pass = sum(1 for r in results if r["passed"])
    total = len(results)
    pct = 100.0 * total_pass / total if total else 0.0
    print(f"\n  TOTAL: {total_pass}/{total} pass  ({pct:.1f}%)")

    print("\n  BY KIND:")
    by_kind = {}
    for r in results:
        by_kind.setdefault(r["kind"], []).append(r)
    for kind, rs in by_kind.items():
        n = sum(1 for r in rs if r["passed"])
        print(f"    {kind:<22}: {n}/{len(rs)}")


def print_comparison(per_agent_results):
    print("\n\n" + "#" * 88)
    print("#  CROSS-AGENT COMPARISON")
    print("#" * 88)

    tags = list(per_agent_results.keys())

    # --- category table ---
    categories = [c for c, _ in ALL_SCENARIOS]
    header = f"{'CATEGORY':<28}" + "".join(f"{t:>14}" for t in tags)
    print("\n" + header)
    print("-" * len(header))

    for cat in categories:
        line = f"{cat:<28}"
        for tag in tags:
            rs = [r for r in per_agent_results[tag] if r["category"] == cat]
            n = sum(1 for r in rs if r["passed"])
            d = len(rs)
            pct = 100.0 * n / d if d else 0.0
            line += f"{n:>4}/{d:<3}({pct:>4.0f}%)"
        print(line)

    print("-" * len(header))
    total_line = f"{'TOTAL':<28}"
    for tag in tags:
        rs = per_agent_results[tag]
        n = sum(1 for r in rs if r["passed"])
        d = len(rs)
        pct = 100.0 * n / d if d else 0.0
        total_line += f"{n:>4}/{d:<3}({pct:>4.0f}%)"
    print(total_line)

    print("\n" + "BY KIND".ljust(len(header), "-"))
    kinds = sorted({r["kind"] for rs in per_agent_results.values() for r in rs})
    for kind in kinds:
        line = f"{kind:<28}"
        for tag in tags:
            rs = [r for r in per_agent_results[tag] if r["kind"] == kind]
            n = sum(1 for r in rs if r["passed"])
            d = len(rs)
            pct = 100.0 * n / d if d else 0.0
            line += f"{n:>4}/{d:<3}({pct:>4.0f}%)"
        print(line)

    # --- per-scenario agreement matrix ---
    # For each scenario (identified by category + desc), show PASS/FAIL per agent.
    print("\n" + "PER-SCENARIO PASS/FAIL".ljust(len(header), "-"))
    print(f"{'SCENARIO':<56}" + "".join(f"{t:>8}" for t in tags))

    scenario_keys = []
    for cat, scenarios in ALL_SCENARIOS:
        for (_, desc, _, _, kind) in scenarios:
            scenario_keys.append((cat, desc, kind))

    for (cat, desc, kind) in scenario_keys:
        short = desc if len(desc) <= 54 else desc[:51] + "..."
        line = f"{short:<56}"
        for tag in tags:
            match = next(
                (r for r in per_agent_results[tag]
                 if r["category"] == cat and r["desc"] == desc),
                None,
            )
            mark = "PASS" if (match and match["passed"]) else "FAIL"
            line += f"{mark:>8}"
        print(line)


def main():
    from agent.grenight_agent import GrenightAgent
    from agent.helpers.load_checkpoint import load_checkpoint

    per_agent_results = {}

    for (tag, step, is_self_play, is_double_net, is_dueling_net,
         is_residual_net, is_canonical, reward_shaping) in AGENT_VERSIONS:

        print("\n" + "#" * 88)
        print(f"#  AGENT {tag}   (self_play={is_self_play}, double={is_double_net}, "
              f"dueling={is_dueling_net}, residual={is_residual_net}, "
              f"canonical={is_canonical}, shaping={reward_shaping})")
        print("#" * 88)

        env = GrenightEnvironment(
            is_canonical_version=is_canonical,
        )
        state = env.reset()
        num_planes = state.shape[0]
        num_actions = env.action_encoder.num_actions
        print(f"num_planes = {num_planes}, num_actions = {num_actions}")
        print(f"loading checkpoint {tag} @ step {step}")

        agent = GrenightAgent(
            is_self_play=is_self_play,
            is_double_net=is_double_net,
            is_dueling_net=is_dueling_net,
            is_residual_net=is_residual_net,
            num_planes=num_planes,
            rows=ROWS,
            columns=COLUMNS,
            num_actions=num_actions
        )

        load_checkpoint(agent, tag, step)

        results = []
        for title, scenarios in ALL_SCENARIOS:
            inspect_scenario(agent, is_canonical, title, scenarios, results)

        print_summary(results)
        per_agent_results[tag] = results

    print_comparison(per_agent_results)


if __name__ == "__main__":
    main()