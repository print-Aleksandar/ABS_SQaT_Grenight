from collections import Counter
from agent.grenight_agent import GrenightAgent
from domain.configs import MAX_STEPS_PER_EPISODE
from environment.action_encoder import ActionEncoder
from environment.grenight_environment import GrenightEnvironment
from environment.piece_plane_encoder import PiecePlaneEncoder


def test_agents(left_agent: GrenightAgent,
                right_agent: GrenightAgent,
                left_name: str,
                right_name: str,
                is_left_canonical: bool | None=True,
                is_right_canonical: bool | None=True,
                is_left_legacy: bool | None=True,
                is_right_legacy: bool | None=True) -> str:

    env = GrenightEnvironment(
        is_canonical_version=True
    )

    outcomes = Counter()

    for _ in range(1_000):
        env.reset()

        move_count = 0
        is_white_on_turn = True
        is_draw = False
        done = False

        while move_count < MAX_STEPS_PER_EPISODE and not done:
            is_white_on_turn = True

            env.action_encoder = ActionEncoder(is_canonical_version=is_left_canonical)
            env.state_encoder = PiecePlaneEncoder(is_absolute_perspective=not is_left_canonical,
                                                  is_legacy_encoder=is_left_legacy)
            env._state_cache = None

            left_state = env.get_state()
            left_mask = env.action_mask()
            left_act = left_agent.select_action(left_state, left_mask, 0.05)

            _, _, done, is_draw, _ = env.step(left_act)
            move_count += 1

            if move_count < MAX_STEPS_PER_EPISODE and not done:
                is_white_on_turn = False

                env.action_encoder = ActionEncoder(is_canonical_version=is_right_canonical)
                env.state_encoder = PiecePlaneEncoder(is_absolute_perspective=not is_right_canonical,
                                                      is_legacy_encoder=is_right_legacy)
                env._state_cache = None

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
