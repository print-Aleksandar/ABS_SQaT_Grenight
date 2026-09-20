import numpy as np
from domain.pieces import Piece, PIECES_NUMBERS
from domain.configs import ROWS, COLUMNS


class PiecePlaneEncoder:

    NUM_PLANES = 10

    def __init__(self, is_absolute_perspective: bool | None=False,
                 is_legacy_encoder: bool | None=False) -> None:

        self.is_absolute_perspective = is_absolute_perspective
        self.is_legacy_encoder = is_legacy_encoder

        self.num_planes = self.NUM_PLANES

        if self.is_absolute_perspective:
            self.num_planes += 1

        if self.is_legacy_encoder:
            self.num_planes += 2

        self.no_progress_plane = self.num_planes - 2
        self.repetition_plane = self.num_planes - 1

    def encode_planes(self, pieces: list[Piece],
                      current_player_is_white: bool,
                      steps_without_progress: int = 0,
                      max_steps_without_progress: int = 1,
                      repetition_count: int = 0,
                      repetition_limit: int = 3) -> np.ndarray:

        state = np.zeros((self.num_planes, ROWS, COLUMNS), dtype=np.float32)

        if self.is_absolute_perspective:
            state[0, :, :] = 1.0 if current_player_is_white else 0.0

        state[self.no_progress_plane, :, :] = min(
            steps_without_progress / max_steps_without_progress, 1.0
        )

        state[self.repetition_plane, :, :] = min(
            repetition_count / repetition_limit, 1.0
        )

        for piece in pieces:
            y, x = piece.position

            color_offest = 4 if piece.is_white else 0
            piece_number = PIECES_NUMBERS[type(piece)]
            piece_offest = 4 - 1 - piece_number

            if self.is_legacy_encoder:
                state[self.num_planes - piece_offest - color_offest - 5, y, x] = 1.0
            else:
                state[self.num_planes - piece_offest - color_offest - 3, y, x] = 1.0

            if self.is_legacy_encoder:
                if current_player_is_white:
                    state[-4, y, x] = 1.0
                else:
                    state[-3, y, x] = 1.0

        return state
