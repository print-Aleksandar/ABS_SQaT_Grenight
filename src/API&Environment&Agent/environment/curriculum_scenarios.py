import copy
import numpy as np
from domain.configs import COLUMNS
from domain.pieces import Pawn, Rook, Queen, King
from domain.requests import ValidMovesPiecesRequest
from application.game_service import gather_valid_moves_player

FREE_CAPTURE = "free_capture"
MATE = "mate"
POISONED = "poisoned"
ROOK_ACTIVITY = "rook_activity"

DEFAULT_CATEGORY_WEIGHTS: dict[str, float] = {
    FREE_CAPTURE: 0.40,
    ROOK_ACTIVITY: 0.25,
    MATE: 0.20,
    POISONED: 0.15
}


def _scenario(pieces_factory,
              mover_is_white: bool,
              category: str) -> dict:

    return {
        "pieces_factory": pieces_factory,
        "mover_is_white": mover_is_white,
        "category": category
    }


_FREE_CAPTURE_SCENARIOS = [
    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (0, 3), False),
        Pawn('w3p', True, (3, 1), True),
        Queen('bq', False, (4, 2), True),
    ], True, FREE_CAPTURE),

    _scenario(lambda: [
        King('wk', True, (4, 3), False),
        King('bk', False, (4, 0), False),
        Pawn('b1p', False, (1, 2), True),
        Rook('wr', True, (0, 1), True),
    ], False, FREE_CAPTURE),

    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (0, 3), False),
        Rook('wr', True, (2, 0), True),
        Queen('bq', False, (2, 3), True),
    ], True, FREE_CAPTURE),

    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (0, 3), False),
        Rook('br', False, (3, 3), True),
        Rook('wr', True, (3, 0), True),
    ], False, FREE_CAPTURE),

    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (0, 3), False),
        Queen('wq', True, (2, 1), True),
        Rook('br', False, (2, 3), True),
    ], True, FREE_CAPTURE),

    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (0, 3), False),
        Pawn('w2p', True, (2, 1), True),
        Rook('br', False, (3, 2), True),
    ], True, FREE_CAPTURE),
]

_MATE_SCENARIOS = [
    _scenario(lambda: [
        King('wk', True, (0, 3), False),
        King('bk', False, (4, 1), False),
        Pawn('b1p', False, (3, 1), True),
        Pawn('b2p', False, (3, 2), True),
        Pawn('b3p', False, (3, 3), True),
        Rook('wr', True, (2, 0), True),
    ], True, MATE),

    _scenario(lambda: [
        King('wk', True, (0, 3), False),
        King('bk', False, (4, 2), False),
        Pawn('b1p', False, (3, 1), True),
        Pawn('b2p', False, (3, 2), True),
        Pawn('b3p', False, (3, 3), True),
        Queen('wq', True, (2, 0), True),
    ], True, MATE),
]

_POISONED_SCENARIOS = [
    _scenario(lambda: [
        King('wk', True, (4, 3), False),
        King('bk', False, (4, 0), False),
        Queen('wq', True, (2, 1), True),
        Pawn('b1p', False, (1, 1), True),
        Pawn('b2p', False, (0, 0), True),
    ], True, POISONED),

    _scenario(lambda: [
        King('wk', True, (4, 2), False),
        King('bk', False, (4, 0), False),
        Queen('wq', True, (0, 1), True),
        Pawn('b1p', False, (0, 0), True),
        Queen('bq', False, (3, 0), True),
    ], True, POISONED),
]

_ROOK_ACTIVITY_SCENARIOS = [
    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (4, 3), False),
        Rook('wr', True, (2, 0), True),
    ], True, ROOK_ACTIVITY),

    _scenario(lambda: [
        King('wk', True, (0, 0), False),
        King('bk', False, (4, 0), False),
        Rook('wr', True, (2, 2), True),
    ], True, ROOK_ACTIVITY)
]

ALL_SCENARIOS = (
    _FREE_CAPTURE_SCENARIOS
    + _MATE_SCENARIOS
    + _POISONED_SCENARIOS
    + _ROOK_ACTIVITY_SCENARIOS
)

_BY_CATEGORY: dict[str, list[dict]] = {}
for _s in ALL_SCENARIOS:
    _BY_CATEGORY.setdefault(_s["category"], []).append(_s)


def _mirror_horizontal(pieces: list) -> list:
    mirrored = copy.deepcopy(pieces)
    for p in mirrored:
        y, x = p.position
        p.position = (y, COLUMNS - 1 - x)
    return mirrored


def _has_legal_move(pieces: list,
                    is_white_on_turn: bool) -> bool:

    request = ValidMovesPiecesRequest(
        pieces=pieces,
        is_for_white=is_white_on_turn,
        is_for_white_turn=is_white_on_turn,
        is_current_move_promotion=False,
    )

    moves = gather_valid_moves_player(request)
    return any(len(v) > 0 for v in moves.values())


def random_scenario(rng: np.random.Generator,
                    category_weights: dict[str, float] | None = None,
                    max_attempts: int = 10) -> tuple[list, bool]:

    weights = category_weights or DEFAULT_CATEGORY_WEIGHTS
    categories = [c for c in weights if _BY_CATEGORY.get(c)]
    probs = np.array([weights[c] for c in categories], dtype=float)
    probs = probs / probs.sum()

    for _ in range(max_attempts):
        category = rng.choice(categories, p=probs)
        options = _BY_CATEGORY[category]
        base = options[int(rng.integers(len(options)))]

        pieces = base["pieces_factory"]()
        mover_is_white = base["mover_is_white"]

        if rng.random() < 0.5:
            pieces = _mirror_horizontal(pieces)

        if _has_legal_move(pieces, mover_is_white):
            return pieces, mover_is_white

    for s in ALL_SCENARIOS:
        pieces = s["pieces_factory"]()
        if _has_legal_move(pieces, s["mover_is_white"]):
            return pieces, s["mover_is_white"]

    raise RuntimeError("No valid curriculum scenario available")
