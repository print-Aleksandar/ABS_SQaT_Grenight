import random
import numpy as np
from domain.configs import MAX_STEPS_WITHOUT_PROGRESS, ROWS
from domain.pieces import Piece, Pawn, PIECES_NUMBERS
from domain.requests import MoveRequest, ValidMovesPiecesRequest
from domain.exceptions import GrenightException
from domain.board_initialization import create_initial_board
from application.game_service import make_move, gather_valid_moves_player
from application.board_getter import get_piece_by_position
from environment.action_encoder import ActionEncoder
from environment.curriculum_scenarios import generate_random_curriculum_scenario
from environment.piece_plane_encoder import PiecePlaneEncoder


def rotate_pieces_helper(pieces: list[Piece]) -> None:
    for piece in pieces:
        piece.is_white = not piece.is_white

        y, x = piece.position
        piece.position = ROWS - 1 - y, x

        piece.update_after_flipping()


class GrenightEnvironment:

    PAWN, ROOK, QUEEN = 0, 1, 2
    PIECE_VALUES = {PAWN: 0.03, ROOK: 0.15, QUEEN: 0.27}

    def __init__(self, is_canonical_version: bool,
                 will_do_reward_shaping: bool | None = False,
                 curriculum_prob: float = 0.0,
                 is_legacy_encoder: bool | None=False) -> None:

        self.will_do_reward_shaping = will_do_reward_shaping

        self.HARDER_DRAWS = -1.0
        self.LIGHTER_DRAWS = -0.5
        self.THREEFOLD_REPETITION_RULE_VALUE = 0.0

        self.is_threefold_repetition_better = None

        self.is_canonical_version = is_canonical_version
        self.is_legacy_encoder = is_legacy_encoder

        self.action_encoder = ActionEncoder(self.is_canonical_version)
        self.state_encoder = PiecePlaneEncoder(not self.is_canonical_version, self.is_legacy_encoder)

        self.pieces = None

        self.is_white_on_turn = True
        self.done = False
        self.is_enemy_in_check = False

        self.current_repetition_count = 0
        self.steps_without_pawn_move_or_capture = 0

        self.position_counts: dict[tuple, int] = {}
        self.is_draw_by_rule = False
        self.draw_reason: str | None = None

        self._legal_actions_cache: list[int] | None = None
        self._legal_actions_set_cache: set[int] | None = None

        self._state_cache: np.ndarray | None = None

        self.curriculum_prob = curriculum_prob
        self.use_curriculum = False

    def load_pieces_absolute(self, pieces: list[Piece]) -> None:
        self.pieces = pieces
        self.is_white_on_turn = not self.is_white_on_turn

        key = self.position_key()
        self.current_repetition_count = self.position_counts.get(key, 0) + 1
        self.position_counts[key] = self.current_repetition_count

    def reset(self) -> np.ndarray:
        self.use_curriculum = 0.0 < random.random() < self.curriculum_prob

        if self.use_curriculum:
            for _ in range(10):
                self.pieces = generate_random_curriculum_scenario()
                self.is_white_on_turn = True if random.random() < 1/2 else False

                if len(self.legal_actions()) > 0:
                    break
            else:
                self.pieces, self.is_white_on_turn = create_initial_board(), True

        else:
            self.pieces, self.is_white_on_turn = create_initial_board(), True

        self.done = False
        self.is_threefold_repetition_better
        self.steps_without_pawn_move_or_capture = 0
        self.position_counts = {}
        self.current_repetition_count = 0
        self.is_draw_by_rule = False
        self.draw_reason = None
        self._state_cache = None
        self._invalidate_legal_actions_cache()

        key = self.position_key()
        self.current_repetition_count = self.position_counts.get(key, 0) + 1
        self.position_counts[key] = self.current_repetition_count

        state = self.get_state()
        self._state_cache = state
        return state

    def get_state(self) -> np.ndarray:
        if self._state_cache is not None:
            return self._state_cache

        return self.state_encoder.encode_planes(
            pieces=self.pieces,
            current_player_is_white=self.is_white_on_turn,
            steps_without_progress=self.steps_without_pawn_move_or_capture,
            max_steps_without_progress=MAX_STEPS_WITHOUT_PROGRESS,
            repetition_count=self.current_repetition_count,
            repetition_limit=3,
        )

    def _invalidate_legal_actions_cache(self) -> None:
        self._legal_actions_cache = None
        self._legal_actions_set_cache = None

    def material_balance(self, pieces: list[Piece], is_white_perspective: bool) -> float:
        balance = 0.0
        for p in pieces:
            value = self.PIECE_VALUES.get(PIECES_NUMBERS[type(p)], 0.0)
            if p.is_white == is_white_perspective:
                balance += value
            else:
                balance -= value
        return balance

    def legal_actions(self) -> list[int]:

        if self._legal_actions_cache is not None:
            return self._legal_actions_cache

        if self.done:
            return []

        request = ValidMovesPiecesRequest(
            pieces=self.pieces,
            is_for_white=True if self.is_canonical_version else self.is_white_on_turn,
            is_for_white_turn=True if self.is_canonical_version else self.is_white_on_turn,
            is_current_move_promotion=False
        )

        uids_with_valid_moves = gather_valid_moves_player(request)
        uids_with_piece = {piece.uid: piece for piece in self.pieces}
        actions = []

        for uid, positions in uids_with_valid_moves.items():
            piece = uids_with_piece.get(uid)
            if piece is None:
                continue

            is_pawn_about_to_promote = (
                piece.can_implement_pawn_moves and piece.is_next_move_pawn_promotion
            )

            for to_position in positions:
                if is_pawn_about_to_promote:
                    for promote_to in (1, 2): # TODO: put when scaling for knight and bishop: 1, 2, 3, 4, easy to forget place
                        action = self.action_encoder.encode_promotion(
                            from_position=piece.position,
                            to_position=to_position,
                            promote_to=promote_to,
                            current_player_is_white=True if self.is_canonical_version else self.is_white_on_turn
                        )
                        actions.append(action)
                else:
                    action = self.action_encoder.encode(
                        from_position=piece.position,
                        to_position=to_position,
                    )
                    actions.append(action)

        self._legal_actions_cache = actions
        self._legal_actions_set_cache = set(actions)
        return actions

    def action_mask(self) -> np.ndarray:
        mask = np.zeros(self.action_encoder.num_actions, dtype=bool)
        if self.done:
            return mask

        actions = self.legal_actions()
        if actions:
            mask[actions] = True
        return mask

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:

        if self.done:
            raise RuntimeError("step() called on a finished episode; call reset() first.")

        self.is_threefold_repetition_better = (
            self._is_threefold_repetition_better() if self.will_do_reward_shaping else False
        )

        self.steps_without_pawn_move_or_capture += 1
        self.is_enemy_in_check = False

        self.legal_actions()
        if action not in self._legal_actions_set_cache:
            raise ValueError(f"Illegal action {action}")

        if self.action_encoder.is_promotion_action(action):
            from_position, to_position, promote_to = self.action_encoder.decode_promotion(action, True if self.is_canonical_version else self.is_white_on_turn)
            is_promotion = True

        else:
            from_position, to_position = self.action_encoder.decode(action)
            promote_to = None
            is_promotion = False

        piece = get_piece_by_position(self.pieces, from_position)
        if piece is None:
            raise ValueError(f"Illegal action {action}: no piece at {from_position}")

        if piece.can_implement_pawn_moves:
            self.steps_without_pawn_move_or_capture = 0

        request = MoveRequest(
            pieces=self.pieces,
            uid=piece.uid,
            position=to_position,
            is_white_on_turn=True if self.is_canonical_version else self.is_white_on_turn,
            is_from_white_player=True if self.is_canonical_version else self.is_white_on_turn,
            is_current_move_promotion=False,
            promote_to=None
        )

        try:
            response = make_move(request)
        except GrenightException as e:
            raise ValueError(f"Action {action} rejected by make_move: {type(e).__name__}")

        if is_promotion:
            request = MoveRequest(
                pieces=response.pieces,
                uid=piece.uid,
                position=to_position,
                is_white_on_turn=True if self.is_canonical_version else self.is_white_on_turn,
                is_from_white_player=True if self.is_canonical_version else self.is_white_on_turn,
                is_current_move_promotion=True,
                promote_to=promote_to
            )

            try:
                response = make_move(request)
            except GrenightException as e:
                raise ValueError(f"Action {action} rejected by make_move: {type(e).__name__}")

        if len(response.pieces) < len(self.pieces) or type(piece) == Pawn:
            self.steps_without_pawn_move_or_capture = 0

        self.pieces = response.pieces
        self.is_enemy_in_check = response.is_enemy_in_check

        self.is_draw_by_rule = False
        self.draw_reason = None
        self.done = response.is_game_finished

        if not self.done:
            if self.steps_without_pawn_move_or_capture >= MAX_STEPS_WITHOUT_PROGRESS:
                self.done = True
                self.is_draw_by_rule = True
                self.draw_reason = "max_steps_without_progress"

            elif self.is_insufficient_material():
                self.done = True
                self.is_draw_by_rule = True
                self.draw_reason = "insufficient_material"

        else:
            if response.is_game_finished and response.is_draw:
                self.done = True
                self.draw_reason = "stalemate"

        if self.is_canonical_version and not self.is_white_on_turn and not self.done:
            rotate_pieces_helper(self.pieces)

        if not self.done:
            key = self.position_key()
            self.current_repetition_count = self.position_counts.get(key, 0) + 1
            self.position_counts[key] = self.current_repetition_count

            if self.current_repetition_count >= 3:
                self.done = True
                self.is_draw_by_rule = True
                self.draw_reason = "threefold_repetition"

        self.is_white_on_turn = not self.is_white_on_turn
        self._state_cache = None
        self._invalidate_legal_actions_cache()

        if self.is_canonical_version and not self.is_white_on_turn and not self.done:
            rotate_pieces_helper(self.pieces)

        reward = self.calculate_reward_registry(response)

        next_state = self.get_state()

        self._state_cache = next_state

        info = {
            "is_enemy_in_check": response.is_enemy_in_check,
            "draw_reason": self.draw_reason,
        }

        return next_state, reward, self.done, self.draw_reason is not None, info

    def sample(self) -> int:

        return np.random.choice(self.legal_actions())

    def position_key(self) -> tuple:

        pieces_key = tuple(sorted(
            (PIECES_NUMBERS[type(p)], p.is_white, p.position)
            for p in self.pieces
        ))
        return pieces_key, self.is_white_on_turn

    def is_insufficient_material(self) -> bool:

        piece_types = [PIECES_NUMBERS[type(p)] for p in self.pieces]

        if any(t in (self.PAWN, self.ROOK, self.QUEEN) for t in piece_types):
            return False
        return True

    def _is_threefold_repetition_better(self) -> bool:
        ally_pieces = [p for p in self.pieces if (
                (not self.is_canonical_version and p.is_white == self.is_white_on_turn)
                or (self.is_canonical_version and p.is_white == True)
        )]

        enemy_pieces = [p for p in self.pieces if (
                (not self.is_canonical_version and p.is_white != self.is_white_on_turn)
                or (self.is_canonical_version and p.is_white == False)
        )]

        if not any(p for p in ally_pieces if PIECES_NUMBERS[type(p)] in [self.QUEEN, self.ROOK]) \
                and any(p for p in enemy_pieces if PIECES_NUMBERS[type(p)] in [self.QUEEN, self.ROOK]):
            return True

        return len(ally_pieces) <= len(enemy_pieces) and \
            not any(p for p in ally_pieces if PIECES_NUMBERS[type(p)] in [self.QUEEN, self.ROOK]) \
            and not any(p for p in enemy_pieces if PIECES_NUMBERS[type(p)] in [self.QUEEN, self.ROOK])

    def calculate_reward_registry(self, response) -> float:
        if self.will_do_reward_shaping:
            return self.calculate_reward_with_shaping(response)
        else:
            return self.calculate_reward_terminal_only(response)

    def calculate_reward_terminal_only(self, response) -> float:
        if not self.done:
            return 0.0

        if response.is_draw or self.is_draw_by_rule:
            return 0.0
        return 1.0

    def calculate_reward_with_shaping(self, response) -> float:
        if self.draw_reason == "stalemate":
            return self.HARDER_DRAWS

        if self.draw_reason == "insufficient_material":
            return self.LIGHTER_DRAWS

        if self.draw_reason == "threefold_repetition":
            if self.is_threefold_repetition_better:
                return self.THREEFOLD_REPETITION_RULE_VALUE
            return self.LIGHTER_DRAWS

        if self.draw_reason == "max_steps_without_progress" or response.is_draw:
            return self.HARDER_DRAWS

        if self.done:
            return 1.0

        return 0.0
