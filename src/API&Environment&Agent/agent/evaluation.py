from collections import Counter
import numpy as np
from domain.configs import (
    MAX_STEPS_PER_EPISODE,
    LOG_EVERY_EPISODE,
    EVALUATE_GAMES,
    DISCOUNT_FACTOR_GAMMA
)
from environment.grenight_environment import GrenightEnvironment
from agent.grenight_agent import GrenightAgent


def evaluate_agent_by_all_combos(env: GrenightEnvironment,
                                 agent: GrenightAgent,
                                 is_self_play: bool) -> None:

    cp = env.curriculum_prob
    env.curriculum_prob = 0.0

    evaluate_agent(env, agent, is_self_play,True, False)

    if is_self_play:
        evaluate_agent(env, agent, is_self_play,False, True)

    env.curriculum_prob = cp


def evaluate_agent(env: GrenightEnvironment,
                   agent: GrenightAgent,
                   is_self_play: bool,
                   is_agent_playing_for_white: bool,
                   is_agent_playing_for_black: bool) -> None:

    current_agent_step = 0
    log_q_every = EVALUATE_GAMES // 10
    if not is_self_play:
        log_q_every //= 2

    eval_losses = []
    recent_outcomes = Counter()
    draw_reasons = Counter()
    total_moves = 0
    q_averages, q_maxs, q_mins = [], [], []
    td_target_values, td_abs_values = [], []

    for _ in range(EVALUATE_GAMES):
        env.reset()
        done = False
        is_draw = False
        is_white_on_turn = True
        info = None
        move_count = 0

        while not done and move_count < MAX_STEPS_PER_EPISODE:
            is_white_on_turn = True
            white_old_state = env.get_state()
            white_legal_mask = env.action_mask()

            if is_agent_playing_for_white:
                white_action = agent.select_action(white_old_state, white_legal_mask, 0.0)
            else:
                white_action = env.sample()

            black_old_state, white_reward, done, is_draw, info = env.step(white_action)
            move_count += 1

            if is_agent_playing_for_white:
                current_agent_step += 1
                collect = current_agent_step % log_q_every == 0
                if collect:
                    agent.set_legal_q_stats(white_old_state, white_legal_mask)
                    q_averages.append(agent.last_mean_legal_q)
                    q_mins.append(agent.last_min_legal_q)
                    q_maxs.append(agent.last_max_legal_q)

            black_legal_mask = env.action_mask()
            black_reward = 0.0

            if not done and move_count < MAX_STEPS_PER_EPISODE:
                if is_agent_playing_for_black:
                    black_action = agent.select_action(black_old_state, black_legal_mask, 0.0)
                else:
                    black_action = env.sample()

                is_white_on_turn = False
                white_new_state, black_reward, done, is_draw, info = env.step(black_action)
                move_count += 1

                if is_self_play and is_agent_playing_for_black:
                    current_agent_step += 1
                    collect = current_agent_step % log_q_every == 0
                    if collect:
                        agent.set_legal_q_stats(black_old_state, black_legal_mask)
                        q_averages.append(agent.last_mean_legal_q)
                        q_mins.append(agent.last_min_legal_q)
                        q_maxs.append(agent.last_max_legal_q)

                    loss = agent.calculate_td_loss(
                        black_old_state, black_legal_mask, black_action,
                        black_reward, env.get_state(), done, env.action_mask(), collect
                    )

                    eval_losses.append(loss)
                    if collect:
                        td_target_values.append(agent.last_td_target)
                        td_abs_values.append(agent.last_td_abs)

            if is_agent_playing_for_white:
                if not is_self_play:
                    white_reward -= DISCOUNT_FACTOR_GAMMA * black_reward

                collect = current_agent_step % log_q_every == 0

                if is_self_play:
                    loss = agent.calculate_td_loss(
                        white_old_state, white_legal_mask, white_action,
                        white_reward, black_old_state, done, black_legal_mask, collect
                    )

                    eval_losses.append(loss)
                    if collect:
                        td_target_values.append(agent.last_td_target)
                        td_abs_values.append(agent.last_td_abs)

                else:
                    loss = agent.calculate_td_loss(
                        white_old_state, white_legal_mask, white_action,
                        white_reward, env.get_state(), done, env.action_mask(), collect
                    )

                    eval_losses.append(loss)
                    if collect:
                        td_target_values.append(agent.last_td_target)
                        td_abs_values.append(agent.last_td_abs)

        if not done:
            outcome = "truncated"
        else:
            if is_draw:
                outcome = "draw"
            else:
                outcome = "white_win" if is_white_on_turn else "black_win"

        recent_outcomes[outcome] += 1
        total_moves += move_count
        if info["draw_reason"] is not None:
            draw_reasons[info["draw_reason"]] += 1

    process_stats(recent_outcomes, draw_reasons, total_moves, eval_losses, q_averages, q_maxs, q_mins, False,
                  is_agent_playing_for_white, is_agent_playing_for_black,
                  td_target_values, td_abs_values)


def process_stats(outcomes: Counter,
                  draw_reasons: Counter,
                  total_moves: int,
                  losses: list[float],
                  q_averages: list[float],
                  q_maxs: list[float],
                  q_mins: list[float],
                  is_training_stats: bool,
                  is_agent_playing_for_white: bool,
                  is_agent_playing_for_black: bool,
                  td_target_values: list[float] | None=None,
                  td_abs_values: list[float] | None=None) -> None:


    if is_training_stats:
        avg_loss = np.mean(losses[-5000:]) if losses else float("nan")
    else:
        avg_loss = np.mean(losses) if losses else float("nan")

    completed = (
            outcomes.get("white_win", 0)
            + outcomes.get("black_win", 0)
            + outcomes.get("draw", 0)
    )

    total_episodes = completed + outcomes.get("truncated", 0)

    win_pct = (
        100.0 * outcomes.get("white_win", 0) / completed
        if completed > 0 else 0.0
    )

    black_pct = (
        100.0 * outcomes.get("black_win", 0) / completed
        if completed > 0 else 0.0
    )

    draw_pct = (
        100.0 * outcomes.get("draw", 0) / completed
        if completed > 0 else 0.0
    )

    truncated_pct = (
        100.0 * outcomes.get("truncated", 0) / total_episodes
        if total_episodes > 0 else 0.0
    )

    n = LOG_EVERY_EPISODE if is_training_stats else EVALUATE_GAMES
    label = "training" if is_training_stats else "evaluation"

    if is_agent_playing_for_white and is_agent_playing_for_black:
        label += " self play"
    else:
        if is_agent_playing_for_white:
            label += " (agent=white vs random)"

        else:
            label += " (agent=black vs random)"

    stalemate_pct = (
        100 * draw_reasons.get("stalemate", 0) / outcomes.get("draw", 1)
    )

    threefold_repetition_pct = (
        100 * draw_reasons.get("threefold_repetition", 0) / outcomes.get("draw", 1)
    )

    insufficient_material_pct = (
        100 * draw_reasons.get("insufficient_material", 0) / outcomes.get("draw", 1)
    )

    max_steps_without_progress_pct = (
        100 * draw_reasons.get("max_steps_without_progress", 0) / outcomes.get("draw", 1)
    )

    print()

    if is_training_stats:
        print(f"{label} statistics — last {n:,} episodes")
    else:
        print(f"{label} statistics — another new {n:,} games")


    print(
        f"  outcomes     "
        f"white {win_pct:5.1f}%   "
        f"black {black_pct:5.1f}%   "
        f"draw {draw_pct:5.1f}%   "
        f"truncated {truncated_pct:5.1f}%"
    )

    print(
        f"  draw_reasons  "
        f"threefold_repetition {threefold_repetition_pct:5.1f}%   "
        f"stalemate {stalemate_pct:5.1f}%   "
        f"insufficient_material {insufficient_material_pct:5.1f}%   "
        f"max_steps_without_progress {max_steps_without_progress_pct:5.1f}%   "
    )

    print(f"  average env moves per game: {(total_moves / n):5.1f}")

    print(
        f"  agent       "        
        f"loss {avg_loss:10.8f}   "
        f"registered Q avg {np.mean(q_averages):8.4f}   "
        f"registered Q max {np.mean(q_maxs):8.4f}   "
        f"registered Q min {np.mean(q_mins):8.4f}"
    )

    if not is_training_stats:
        print(
            f"  diagnostics "
            f"registered target avg {np.mean(td_target_values):8.4f}   "
            f"registered target max {np.max(td_target_values):8.4f}   "
            f"registered target min {np.min(td_target_values):8.4f}"
        )

        print(
            f"              "
            f"registered |TD| avg {np.mean(td_abs_values):8.4f}   "
            f"registered |TD| max {np.max(td_abs_values):8.4f}"
        )
