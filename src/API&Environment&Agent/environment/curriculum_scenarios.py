import random
from domain.configs import COLUMNS, ROWS
from domain.pieces import Pawn, Rook, King, Piece

def generate_random_curriculum_scenario() -> list[Piece]:

    white_rooks = random.randint(1, 2)
    black_rooks = random.randint(1, 2)
    white_pawns = 1
    black_pawns = 1

    one_more_pawn = random.random()
    if one_more_pawn > 1/3:
        if one_more_pawn > 2/3:
            white_pawns += 1
        else:
            black_pawns += 1

    remove_one_rook = random.random()
    if remove_one_rook < 1/2:
        if remove_one_rook < 1/4:
            white_rooks -= 1
        else:
            black_rooks -= 1

    pieces_to_generate = dict()
    pieces_to_generate[(Rook, True)] = white_rooks
    pieces_to_generate[(Rook, False)] = black_rooks
    pieces_to_generate[(Pawn, True)] = white_pawns
    pieces_to_generate[(Pawn, False)] = black_pawns

    pieces = []
    pieces_positions = []

    wy, wx = random.randint(0, ROWS - 1), random.randint(0, COLUMNS - 1)
    wpos = (wy, wx)
    king = King("wk", True, wpos, True)
    pieces.append(king)
    pieces_positions.append(wpos)

    while True:
        by, bx = random.randint(0, ROWS - 1), random.randint(0, COLUMNS - 1)
        bpos = (by, bx)
        if abs(by - wy) > 1 or abs(bx - wx) > 1:
            king = King("bk", False, bpos, True)
            pieces.append(king)
            pieces_positions.append(bpos)
            break

    for k, v in pieces_to_generate.items():
        cls, clr = k
        for _ in range(v):
            for i in range(200):
                y, x = random.randint(0 if cls == Rook else 1, ROWS - 1 if cls == Rook else ROWS - 2), random.randint(0, COLUMNS - 1)
                pos = (y, x)
                if pos not in pieces_positions:
                    if cls == Pawn:
                        if clr:
                            if bpos not in [(y + 1, x + 1), (y + 1, x - 1)]:
                                pawn = Pawn(("p" + str(len(pieces))), clr, pos, True)
                                pieces.append(pawn)
                                pieces_positions.append(pos)
                                break
                        else:
                            if wpos not in [(y - 1, x + 1), (y - 1, x - 1)]:
                                pawn = Pawn(("p" + str(len(pieces))), clr, pos, True)
                                pieces.append(pawn)
                                pieces_positions.append(pos)
                                break
                    else:
                        if clr:
                            if y != by and x != bx:
                                rook = Rook(("r" + str(len(pieces))), clr, pos, True)
                                pieces.append(rook)
                                pieces_positions.append(pos)
                                break
                        else:
                            if y != wy and x != wx:
                                rook = Rook(("r" + str(len(pieces))), clr, pos, True)
                                pieces.append(rook)
                                pieces_positions.append(pos)
                                break
            else:
                raise RuntimeError("No valid curriculum scenario could've been generated")

    return pieces
