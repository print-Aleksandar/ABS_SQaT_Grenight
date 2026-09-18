import os
import random
from collections import Counter, defaultdict
from copy import deepcopy
import numpy as np
import torch
from agent.evaluation import process_stats, evaluate_agent_by_all_combos
from agent.network import Network
from agent.opponent_pool import OpponentPool
from domain.board_initialization import create_initial_board
from domain.configs import (
    ROWS,
    COLUMNS,
    MAX_STEPS_PER_EPISODE,
    TRAIN_EPISODES,
    EPSILON_START,
    EPSILON_END,
    EPSILON_DECAY_STEPS,
    CHECKPOINT_EVERY_EPISODES,
    LOG_EVERY_EPISODE,
    LOG_Q_EVERY_STEPS,
    DISCOUNT_FACTOR_GAMMA,
    CHECKPOINT_DIR_KAGGLE as CHECKPOINT_DIR
)
from agent.grenight_agent import GrenightAgent
from environment.grenight_environment import GrenightEnvironment


device = "cuda" if torch.cuda.is_available() else "cpu"


def epsilon_at(step: int) -> float:

    return max(EPSILON_END,
               EPSILON_START - (EPSILON_START - EPSILON_END) * step / EPSILON_DECAY_STEPS)


def save_checkpoint(agent: GrenightAgent,
                    ep: int, agent_step: int,
                    is_double_net: bool) -> None:
    path = os.path.join(CHECKPOINT_DIR, f"curr_impl_ep{ep}.pt")

    if is_double_net:
        torch.save({
            "policy_state_dict": agent.policy_net.state_dict(),
            "target_state_dict": agent.target_net.state_dict(),
            "optimizer_state_dict": agent.optimizer.state_dict(),
            "train_steps": agent.train_steps,
            "episode": ep,
            "agent_step": agent_step,
        }, path)

    else:
        torch.save({
            "policy_state_dict": agent.policy_net.state_dict(),
            "optimizer_state_dict": agent.optimizer.state_dict(),
            "train_steps": agent.train_steps,
            "episode": ep,
            "agent_step": agent_step,
        }, path)

    print(f"[checkpoint] saved: {path}")


def train_self_play_episode(env, agent, agent_step, losses, q_averages,
                            q_maxs, q_mins, opponent_net=None,
                            will_do_reward_shaping: bool | None=False):

    state = env.reset()
    done = False
    is_draw = False
    is_white_on_turn = True
    move_count = 0
    info = None
    live_plays_white = random.random() < 0.5

    while not done and move_count < MAX_STEPS_PER_EPISODE:
        is_white_on_turn = env.is_white_on_turn
        legal_mask = env.action_mask()
        is_live_turn = (is_white_on_turn == live_plays_white) or opponent_net is None

        # Note: this is true only when is canonical = True
        phi_s0 = (
            env.material_balance(env.pieces, True) if will_do_reward_shaping else 0
        )

        if is_live_turn:
            epsilon = epsilon_at(agent_step)
            action = agent.select_action(state, legal_mask, epsilon)
        else:
            with torch.no_grad():
                state_t = torch.from_numpy(state).unsqueeze(0).to(agent.device)
                mask_t = (
                    None if not agent.is_dueling_net
                    else torch.from_numpy(legal_mask).unsqueeze(0).to(agent.device)
                )
                q = agent._q(opponent_net, state_t, mask_t).squeeze(0).cpu().numpy()
                legal_indices = np.flatnonzero(legal_mask)
                masked_q = np.full(agent.num_actions, -np.inf, dtype=np.float32)
                masked_q[legal_indices] = q[legal_indices]
                action = int(np.argmax(masked_q))

        new_state, reward, done, is_draw, info = env.step(action)
        agent_step += 1
        next_legal_mask = env.action_mask()

        if is_live_turn:
            if not done and will_do_reward_shaping:
                phi_s1 = env.material_balance(env.pieces, False)
                shaping = DISCOUNT_FACTOR_GAMMA * phi_s1 - phi_s0
                reward += shaping

            agent.store(state, legal_mask, action, reward, new_state, done, next_legal_mask)
            loss = agent.train_step()
            if loss is not None:
                losses.append(loss)

        if is_live_turn and agent_step % LOG_Q_EVERY_STEPS == 0:
            agent.set_legal_q_stats(state, legal_mask)
            q_averages.append(agent.last_mean_legal_q)
            q_mins.append(agent.last_min_legal_q)
            q_maxs.append(agent.last_max_legal_q)

        state = new_state
        move_count += 1

    return done, is_draw, is_white_on_turn, agent_step, info, move_count


def train_vs_random_episode(env: GrenightEnvironment, agent: GrenightAgent,
                            agent_step: int, losses: list[float], q_averages: list[float],
                            q_maxs: list[float], q_mins: list[float],
                            will_do_reward_shaping: bool | None=False) -> tuple[bool, bool, bool, int, dict, int]:

    state = env.reset()
    done = False
    is_draw = False
    is_white_on_turn = True
    move_count = 0
    info = None

    while not done and move_count < MAX_STEPS_PER_EPISODE:
        is_white_on_turn = True
        white_old_state = state
        old_legal_mask = env.action_mask()
        epsilon = epsilon_at(agent_step)

        white_action = agent.select_action(white_old_state, old_legal_mask, epsilon)
        if will_do_reward_shaping:
            phi_s0 = env.material_balance(env.pieces, True)
        else:
            phi_s0 = 0
        _, white_reward, done, is_draw, info = env.step(white_action)

        agent_step += 1
        move_count += 1

        if not done and move_count < MAX_STEPS_PER_EPISODE:
            is_white_on_turn = False
            black_action = env.sample()
            _, black_reward, done, is_draw, info = env.step(black_action)
            if will_do_reward_shaping:
                phi_s2 = env.material_balance(env.pieces, True)
            else:
                phi_s2 = 0

            move_count += 1

            if done:
                if is_draw:
                    base_reward = black_reward
                else:
                    base_reward = -black_reward
                shaping = -phi_s0
            else:
                base_reward = white_reward - DISCOUNT_FACTOR_GAMMA * black_reward
                shaping = (DISCOUNT_FACTOR_GAMMA ** 2) * phi_s2 - phi_s0

            total_reward = base_reward + shaping
        else:
            total_reward = white_reward

        next_legal_mask = env.action_mask()

        agent.store(
            white_old_state,
            old_legal_mask,
            white_action,
            total_reward,
            env.get_state(),
            done,
            next_legal_mask,
        )

        if agent_step % LOG_Q_EVERY_STEPS == 0:
            agent.set_legal_q_stats(white_old_state, old_legal_mask)

            q_averages.append(agent.last_mean_legal_q)
            q_mins.append(agent.last_min_legal_q)
            q_maxs.append(agent.last_max_legal_q)

        loss = agent.train_step()
        if loss is not None:
            losses.append(loss)

        state = env.get_state()

    return done, is_draw, is_white_on_turn, agent_step, info, move_count


def train_agent(is_self_play: bool,
                is_double_net: bool,
                is_dueling_net: bool,
                is_residual_net: bool,
                is_canonical_version: bool,
                will_do_reward_shaping: bool) -> None:

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    print(f"will save checkpoints in: {CHECKPOINT_DIR}\n")

    print(f"number of rows                   : {ROWS}\n"
          f"number of columns                : {COLUMNS}\n"
          f"number of pieces                 : {len(create_initial_board())}\n"
          f"is self play                     : {is_self_play}\n"
          f"is double net                    : {is_double_net}\n"
          f"is dueling net                   : {is_dueling_net}\n"
          f"is residual net                  : {is_residual_net}\n"
          f"is canonical version             : {is_canonical_version}\n"
          f"will do reward shaping           : {will_do_reward_shaping}\n")

    env = GrenightEnvironment(
        is_canonical_version=is_canonical_version,
        will_do_reward_shaping=False
    )

    agent = GrenightAgent(
        is_self_play=is_self_play,
        is_double_net=is_double_net,
        is_dueling_net=is_dueling_net,
        is_residual_net=is_residual_net,
        will_do_bulk_update=True,
        rows=ROWS,
        columns=COLUMNS,
        num_actions=env.action_encoder.num_actions,
        num_planes=env.state_encoder.num_planes,
        device=device
    )

    print(f"policy_net device: {next(agent.policy_net.parameters()).device}")

    agent_step = 0
    episode_start = 1

    losses = []
    recent_outcomes = Counter()
    draw_reasons = Counter()
    total_moves = 0
    q_averages, q_maxs, q_mins = [], [], []

    prev_prev_policy = None
    prev_policy = None

    pool = OpponentPool(max_size=5)

    def make_network():
        return Network(agent.is_dueling_net, agent.is_residual_net,
                       env.state_encoder.num_planes, ROWS, COLUMNS,
                       env.action_encoder.num_actions)

    try:
        for episode in range(episode_start, TRAIN_EPISODES + 1):

            if is_self_play:
                use_pool_opponent = pool.snapshots and random.random() < 0.5

                opponent_net = (
                    pool.sample_opponent_net(make_network, device)
                    if use_pool_opponent else None
                )

                done, is_draw, is_white_on_turn, agent_step, info, move_count = train_self_play_episode(
                    env, agent, agent_step, losses, q_averages, q_maxs, q_mins,
                    opponent_net=opponent_net, will_do_reward_shaping=True
                )

            else:
                done, is_draw, is_white_on_turn, agent_step, info, move_count = train_vs_random_episode(
                    env, agent, agent_step, losses, q_averages, q_maxs, q_mins, will_do_reward_shaping
                )

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

            if episode % CHECKPOINT_EVERY_EPISODES == 0:
                save_checkpoint(agent, episode, agent_step, is_double_net)

            if episode % LOG_EVERY_EPISODE == 0:
                if episode % (LOG_EVERY_EPISODE // 2) == 0:
                    if prev_prev_policy is not None:
                        pool.add(prev_prev_policy)
                    prev_prev_policy = prev_policy
                    prev_policy = deepcopy(agent.policy_net)

                print()
                print("─" * 72)
                print(f"  EPISODE {episode:,}")
                print()

                print(
                    f"  ε (epsilon)     : {epsilon_at(agent_step):>8.4f}\n"
                    f"  agent step      : {agent_step:>8,}"
                )

                print()

                process_stats(recent_outcomes, draw_reasons, total_moves, losses, q_averages, q_maxs, q_mins,True, True, is_self_play)

                print()

                print("  Running evaluation...")
                evaluate_agent_by_all_combos(env, agent, is_self_play)

                print("─" * 72)

                print()

                recent_outcomes.clear()
                draw_reasons.clear()
                total_moves = 0
                q_averages, q_maxs, q_mins = [], [], []

    except KeyboardInterrupt:
        print("\n[interrupted] saving checkpoint before exit...")
        save_checkpoint(agent, episode, agent_step, is_double_net)

    finally:
        save_checkpoint(agent, episode, agent_step, is_double_net)
        print("Done.")

train_agent(True, True, True, True, True, True)
