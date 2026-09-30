"""
Profiles the board-flow that matters for training: repeated
gather_valid_moves_player() + make_move() calls, i.e. what actually
runs on every simulated ply.

Usage:
    python profile_boards.py            # cumulative time, top 30
    python profile_boards.py tottime    # self time, top 30 (best for finding hotspots)
"""
import cProfile
import pstats
import random
import sys

from domain.board_initialization import create_initial_board
from domain.requests import MoveRequest, ValidMovesPiecesRequest
from application.game_service import gather_valid_moves_player, make_move


def play_random_game(max_plies: int = 60) -> int:
    """Plays one random-move game to completion or max_plies, calling the
    exact functions the training loop calls. Returns plies actually played."""
    pieces = create_initial_board()
    is_white_on_turn = True

    for ply in range(max_plies):
        valid_moves_request = ValidMovesPiecesRequest(
            pieces=pieces,
            is_for_white_turn=is_white_on_turn,
            is_current_move_promotion=False,
            is_for_white=is_white_on_turn,
        )
        uids_with_valid_moves = gather_valid_moves_player(valid_moves_request)

        if not uids_with_valid_moves:
            break  # no legal moves: checkmate/stalemate

        uid = random.choice(list(uids_with_valid_moves.keys()))
        position = random.choice(uids_with_valid_moves[uid])

        move_request = MoveRequest(
            pieces=pieces,
            uid=uid,
            position=position,
            is_current_move_promotion=False,
            promote_to=None,
            is_white_on_turn=is_white_on_turn,
            is_from_white_player=is_white_on_turn,
        )
        response = make_move(move_request)

        pieces = response.pieces
        is_white_on_turn = response.is_white_on_turn

        if response.is_game_finished:
            break

        # naive: if the move produced a promotion prompt, just always promote to queen
        if response.is_next_move_promotion:
            # figure out uid/position of the piece that needs to finish promoting
            # (assumes it's the same uid/position we just moved to)
            promo_request = MoveRequest(
                pieces=pieces,
                uid=uid,
                position=position,
                is_current_move_promotion=True,
                promote_to=2,  # Queen
                is_white_on_turn=is_white_on_turn,
                is_from_white_player=is_white_on_turn
            )
            response = make_move(promo_request)
            pieces = response.pieces
            is_white_on_turn = response.is_white_on_turn
            if response.is_game_finished:
                break

    return ply + 1


def run(n_games: int = 200, max_plies: int = 60) -> None:
    random.seed(42)
    total_plies = 0
    for _ in range(n_games):
        total_plies += play_random_game(max_plies)
    print(f"Played {n_games} games, {total_plies} total plies simulated.")


if __name__ == "__main__":
    sort_key = sys.argv[1] if len(sys.argv) > 1 else "cumulative"

    profiler = cProfile.Profile()
    profiler.enable()
    run(n_games=200, max_plies=60)
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats(sort_key)
    stats.print_stats(30)
