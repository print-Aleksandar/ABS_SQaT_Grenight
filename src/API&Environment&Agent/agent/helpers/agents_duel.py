from collections import Counter
from agent.grenight_agent import GrenightAgent
from domain.configs import MAX_STEPS_PER_EPISODE
from environment.action_encoder import ActionEncoder
from environment.grenight_environment import GrenightEnvironment

def test_agents(left_agent: GrenightAgent,
                right_agent: GrenightAgent,
                left_name: str,
                right_name: str) -> str:

    env = GrenightEnvironment(
        is_canonical_version=True,
        will_do_reward_shaping=False
    )
    env.action_encoder = ActionEncoder(is_canonical_version=False)

    outcomes = Counter()

    for _ in range(10):
        env.reset()

        move_count = 0
        is_white_on_turn = True
        is_draw = False
        done = False

        while move_count < MAX_STEPS_PER_EPISODE and not done:
            is_white_on_turn = True

            left_state = env.get_state()
            left_mask = env.action_mask()
            left_act = left_agent.select_action(left_state, left_mask, 0.05)

            _, _, done, is_draw, _ = env.step(left_act)
            move_count += 1

            if move_count < MAX_STEPS_PER_EPISODE and not done:
                is_white_on_turn = False

                right_state = env.get_state()
                right_mask = env.action_mask()
                right_act = right_agent.select_action(right_state, right_mask, 0.05)

                _, _, done, is_draw, _ = env.step(right_act)
                move_count += 1

        if not done:
            outcomes["truncated"] += 1
        else:
            if is_draw:
                outcomes["draw"] += 1
            else:
                outcomes["white_win" if is_white_on_turn else "black_win"] += 1

    return (f"white={left_name}, black={right_name}\n"
            f"Outcomes: {outcomes}")
