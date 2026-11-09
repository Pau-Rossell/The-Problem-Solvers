"""
Minimax with alpha-beta pruning, using a combined material and positional evaluation.
Scores are always from White's perspective: White maximizes, Black minimizes.
Depth counts individual player moves (plies), including the chosen root move.
Root moves and recursive moves are ordered to maximize pruning efficiency.
"""

import random
import chess
from algorithm_bot import (evaluate_board as material_score, terminal_score)

def king_safety(board, color):
    """+20 if castled, -20 if castling rights are lost without castling."""
    rank = 0 if color == chess.WHITE else 7
    king = board.king(color)
    rook = chess.Piece(chess.ROOK, color)
    castled = (
        (king == chess.square(6, rank) and board.piece_at(chess.square(5, rank)) == rook) or  # O-O: king g1, rook f1
        (king == chess.square(2, rank) and board.piece_at(chess.square(3, rank)) == rook)     # O-O-O: king c1, rook d1
    )
    if castled:
        return 20
    if not board.has_castling_rights(color):
        return -20
    return 0

def positional_terms(board: chess.Board) -> float:
    """
    Evaluate positional characteristics from White's perspective.
    Positive scores favor White; negative scores favor Black.
    """

    score = 0

    # 1. Center occupation and control
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]

    for sq in center_squares:
        piece = board.piece_at(sq)

        # Reward occupying central squares
        if piece:
            score += 10 if piece.color == chess.WHITE else -10

        # Reward attacking central squares
        score += 5 * (
            len(board.attackers(chess.WHITE, sq))
            - len(board.attackers(chess.BLACK, sq))
        )

    # 2. Piece development (penalize undeveloped knights and bishops)
    white_starting_squares = [
        chess.B1, chess.G1,
        chess.C1, chess.F1
    ]

    black_starting_squares = [
        chess.B8, chess.G8,
        chess.C8, chess.F8
    ]

    for sq in white_starting_squares:
        piece = board.piece_at(sq)
        if piece and piece.color == chess.WHITE and piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            score -= 15

    for sq in black_starting_squares:
        piece = board.piece_at(sq)
        if piece and piece.color == chess.BLACK and piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            score += 15

    # 3. King safety (reward castling)
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        score += sign * king_safety(board, color)

    # 4. Pawn structure (penalize doubled pawns)
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    for file_index in range(8):
        w_pawns_on_file = sum(
            1 for sq in white_pawns
            if chess.square_file(sq) == file_index
        )

        b_pawns_on_file = sum(
            1 for sq in black_pawns
            if chess.square_file(sq) == file_index
        )

        if w_pawns_on_file > 1:
            score -= 15 * (w_pawns_on_file - 1)

        if b_pawns_on_file > 1:
            score += 15 * (b_pawns_on_file - 1)

    # 5. Pawn structure (penalize isolated pawns)
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)

        for sq in pawns:
            file_index = chess.square_file(sq)

            adjacent_files = [
                f for f in (file_index - 1, file_index + 1)
                if 0 <= f < 8
            ]

            isolated = not any(
                chess.square_file(other_sq) in adjacent_files
                for other_sq in pawns
            )

            if isolated:
                score += -15 if color == chess.WHITE else 15

    # 6. Mobility (reward positions with more attack positions available, even it cannot be captured)
    white_mobility = sum(len(board.attacks(sq)) for sq in chess.SquareSet(board.occupied_co[chess.WHITE]))
    black_mobility = sum(len(board.attacks(sq)) for sq in chess.SquareSet(board.occupied_co[chess.BLACK]))

    score += 2 * (white_mobility - black_mobility)

    return score

def evaluate_board(board: chess.Board) -> float:
    """Combine the original material evaluation with positional terms."""
    return material_score(board) + positional_terms(board)

def order_moves(board: chess.Board):
    """
    Order moves to improve alpha-beta pruning efficiency. 
    Moves are shuffled first to vary equally good choices, then sorted 
    by captures, promotions, and checks.
    """
    moves = list(board.legal_moves)
    random.shuffle(moves)
    moves.sort(
        key=lambda m: (
            board.is_capture(m),
            bool(m.promotion),
            board.gives_check(m)
        ), 
        reverse=True
    )
    return moves

def alpha_beta(
    board: chess.Board,
    depth: int,
    alpha: float = float('-inf'),
    beta: float = float('inf'),
) -> float:
    """
    Search a position with the bounds inherited from its ancestors.
    alpha: the lower bound established by White's alternatives so far.
    beta: the upper bound established by Black's alternatives so far.
    When alpha >= beta, remaining siblings cannot improve an ancestor's
    decision, so they can be skipped. A full window (-inf, inf) returns the
    exact minimax score; a cutoff may return only a bound on that score.
    """
    # Check endings before the depth limit, including mates at the horizon.
    result = terminal_score(board)
    if result is not None:
        return result
    
    if depth <= 0:
        return evaluate_board(board)

    if board.turn == chess.WHITE:
        best_score = float('-inf')
        for move in order_moves(board):
            board.push(move)
            try:
                child_score = alpha_beta(board, depth - 1, alpha, beta)
            finally:
                board.pop()
            best_score = max(best_score, child_score)
            # White can already obtain at least this score.
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break  # Black has an alternative that is no worse.
        return best_score

    else:
        best_score = float('inf')
        for move in order_moves(board):
            board.push(move)
            try:
                child_score = alpha_beta(board, depth - 1, alpha, beta)
            finally:
                board.pop()
            best_score = min(best_score, child_score)
            # Black can already hold the score down to this value.
            beta = min(beta, best_score)
            if alpha >= beta:
                break  # White has an alternative that is no worse.
        return best_score


def choose_move(board: chess.Board, depth: int = 10):
    """Return a legal move, or None for a finished game, without changing board."""
    if depth < 1:
        raise ValueError('Search depth must be at least 1.')
    if terminal_score(board) is not None:
        return None

    maximizing = board.turn == chess.WHITE
    best_score = float('-inf') if maximizing else float('inf')
    best_move = None
    alpha, beta = float('-inf'), float('inf')

    # Use the custom order_moves function for the root as well.
    moves = order_moves(board)

    for move in moves:
        board.push(move)
        try:
            score = alpha_beta(board, depth - 1, alpha, beta)
        finally:
            board.pop()
            
        # Keep the first move on a tie. Internal cutoff scores can be bounds,
        # so a later equal return is not necessarily an exact minimax tie.
        if best_move is None or (maximizing and score > best_score) or (
            not maximizing and score < best_score
        ):
            best_score = score
            best_move = move

        # Carry the root's best bound into the next sibling's search.
        # Resetting both bounds for every move would lose some pruning.
        if maximizing:
            alpha = max(alpha, best_score)
        else:
            beta = min(beta, best_score)
            
    return best_move