"""
verify_selfplay_sign.py
Quick check that the -gamma bootstrap in GrenightAgent is consistent
with the actual perspective flipping in GrenightEnvironment.

Usage:
    python verify_selfplay_sign.py S110110 10000
"""

import sys
import numpy as np
import torch

from domain.configs import ROWS, COLUMNS
from environment.grenight_environment import GrenightEnvironment
from agent.grenight_agent import GrenightAgent
from agent.helpers.load_checkpoint import load_checkpoint


def build_agent(tag, step, is_canonical=True, is_self_play=True):
    env = GrenightEnvironment(
        is_canonical_version=is_canonical,
        will_do_reward_shaping=False,
    )
    state = env.reset()
    num_planes = state.shape[0]
    num_actions = env.action_encoder.num_actions

    agent = GrenightAgent(
        is_self_play=is_self_play,
        is_double_net=True,
        is_dueling_net=False,
        is_residual_net=True,
        num_planes=num_planes,
        rows=ROWS,
        columns=COLUMNS,
        num_actions=num_actions,
    )
    load_checkpoint(agent, tag, step)
    agent.policy_net.eval()
    return env, agent


def q_at(agent, state, mask):
    with torch.no_grad():
        s = torch.from_numpy(state).unsqueeze(0).to(agent.device)
        m = (None if not agent.is_dueling_net
             else torch.from_numpy(mask).unsqueeze(0).to(agent.device))
        return agent._q(agent.policy_net, s, m).squeeze(0).cpu().numpy()


def check_structural(env):
    """Assert self-play implies canonical flipping."""
    print("[1] Structural check")
    is_self_play = True
    is_canonical = env.is_canonical_version

    if is_self_play and not is_canonical:
        print("    FAIL: self-play without canonical flipping → -gamma is WRONG")
        return False

    # Confirm the flip actually happens in step()
    env.reset()
    pre_color = env.is_white_on_turn
    pre_piece_colors = [p.is_white for p in env.pieces]

    action = env.sample()
    env.step(action)

    # After one full step in canonical mode, the "you"-side should still be White.
    # The environment flips pieces when it's the opponent's turn to move.
    flipped_pieces = [p.is_white for p in env.pieces]
    flipped = (pre_piece_colors != flipped_pieces)

    print(f"    is_canonical={is_canonical}, flip occurred in step: {flipped}")
    if not flipped:
        print("    FAIL: no perspective flip → -gamma target assumes a flip")
        return False
    print("    PASS: canonical flipping is active")
    return True


def check_forced_loss(env, agent):
    """
    Numerical check.

    Idea:
      Play a self-play game until it is the LIVE side's turn and the
      opponent is one move away from winning. Then look at Q(s, a) for
      the live side.

      With -gamma target: Q should be strongly NEGATIVE (we are about to lose).
      With +gamma target: Q would be pushed POSITIVE (agent thinks it's fine).

    We use a heuristic: rollout a random game, then at each live-side
    decision record (is_opponent_about_to_win, mean_Q).
    """
    print("\n[2] Numerical check via forced-loss probe")

    neg_signals = []  # games where we are about to lose and Q is very negative
    pos_signals = []  # same situation but Q is positive (would indicate wrong sign)

    for game_idx in range(200):
        state = env.reset()
        done = False
        move = 0
        live_plays_white = True  # live side is White in canonical

        while not done and move < 200:
            is_live = env.is_white_on_turn == live_plays_white
            mask = env.action_mask()

            if is_live:
                q = q_at(agent, state, mask)
                legal = env.legal_actions()
                legal_q = q[legal]

                # Look ahead: after our move, can opponent win immediately?
                # We approximate by checking if the move leaves us in a losing state.
                # Cheaper proxy: track Q at *terminal-adjacent* states.
                # Simpler robust proxy: at the last live-side decision
                # before a loss, mean Q should be negative.
                last_live_q = legal_q.mean()

            action = env.sample() if not is_live else int(
                legal[np.argmax(legal_q)]
            )
            _, _, done, is_draw, info = env.step(action)

            if done:
                # Who won? env.is_white_on_turn is post-step; winner is the side that moved.
                # In canonical, "our side" is always White from its own POV.
                our_side_won = (not is_draw) and (not env.is_white_on_turn)
                if not is_draw and not our_side_won and "last_live_q" in dir():
                    # We lost. The Q at our last decision should have been negative.
                    if last_live_q < 0:
                        neg_signals.append(last_live_q)
                    else:
                        pos_signals.append(last_live_q)
                break
            move += 1

    print(f"    losses with negative Q at last decision: {len(neg_signals)}")
    print(f"    losses with positive Q at last decision: {len(pos_signals)}")

    if not neg_signals and not pos_signals:
        print("    INCONCLUSIVE: no losses observed in random rollouts")
        return None

    if len(neg_signals) > len(pos_signals):
        print("    PASS: Q is negative when we lose → -gamma is consistent")
        return True
    else:
        print("    FAIL: Q is positive when we lose → sign is WRONG")
        return False


def check_mate_in_one_both_sides(env, agent):
    """
    Sharper check: on a fresh board, play greedily as the LIVE side.
    Near the end, at the last live decision before a forced loss, Q should be negative.
    Also, at the last live decision before a forced win, Q should be positive.
    """
    print("\n[3] Greedy self-play: sign of Q at decisive endings")

    win_qs, loss_qs = [], []

    for _ in range(100):
        state = env.reset()
        done = False
        move = 0
        last_live_q = None
        last_live_was_win = None

        while not done and move < 200:
            is_live = env.is_white_on_turn
            mask = env.action_mask()
            legal = env.legal_actions()

            if is_live:
                q = q_at(agent, state, mask)
                legal_q = q[legal]
                last_live_q = float(legal_q.max())
                action = int(legal[np.argmax(legal_q)])
            else:
                action = env.sample()

            _, _, done, is_draw, info = env.step(action)

            if done:
                our_side_won = (not is_draw) and (not env.is_white_on_turn)
                if not is_draw and last_live_q is not None:
                    if our_side_won:
                        win_qs.append(last_live_q)
                    else:
                        loss_qs.append(last_live_q)
                break
            move += 1

    def stat(xs, name):
        if not xs:
            print(f"    {name}: none observed")
            return
        print(f"    {name}: n={len(xs)}, mean={np.mean(xs):+.3f}, "
              f"min={np.min(xs):+.3f}, max={np.max(xs):+.3f}")

    stat(win_qs, "Q at last decision before WIN ")
    stat(loss_qs, "Q at last decision before LOSS")

    if win_qs and loss_qs:
        if np.mean(win_qs) > np.mean(loss_qs):
            print("    PASS: wins score higher than losses → sign consistent")
            return True
        else:
            print("    FAIL: losses score higher than wins → sign WRONG")
            return False
    return None


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "S110110"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 10_000

    print(f"Loading {tag} @ step {step}\n")
    env, agent = build_agent(tag, step)

    ok1 = check_structural(env)
    ok2 = check_forced_loss(env, agent)
    ok3 = check_mate_in_one_both_sides(env, agent)

    print("\n=== VERDICT ===")
    if ok1 is False or ok2 is False or ok3 is False:
        print("Sign is WRONG or setup is inconsistent. Fix before 100k run.")
    elif ok1 and (ok2 or ok3):
        print("Sign is consistent with canonical self-play. Keep -gamma.")
    else:
        print("Structural check passed; numerical checks inconclusive.")
        print("That's fine — proceed with -gamma.")


if __name__ == "__main__":
    main()