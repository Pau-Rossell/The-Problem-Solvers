"""
Minimax with alpha-beta pruning, using a combined material and positional evaluation.
Scores are always from White's perspective: White maximizes, Black minimizes.
Depth counts individual player moves (plies), including the chosen root move.
Root moves and recursive moves are ordered to maximize pruning efficiency.
"""

import random
import chess
from algorithm_bot import (evaluate_board as material_score, terminal_score)

def positional_terms(board: chess.Board) -> float:
    """
    Calculate a positional bonus using small weights relative to a pawn (100).
    Test each feature individually to measure its impact on playing strength.
    """
    score = 0
    
    # 1. Center control (mirrored colors)
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece:
            score += 10 if piece.color == chess.WHITE else -10
            
    # 2. Piece development (penalize Knights on starting squares)
    for sq in [chess.B1, chess.G1]:
        piece = board.piece_at(sq)
        if piece and piece.piece_type == chess.KNIGHT and piece.color == chess.WHITE:
            score -= 15
    for sq in [chess.B8, chess.G8]:
        piece = board.piece_at(sq)
        if piece and piece.piece_type == chess.KNIGHT and piece.color == chess.BLACK:
            score += 15

    # 3. King safety (simple bonus for castling/moving from the center)
    if board.king(chess.WHITE) not in [chess.E1, chess.D1]:
        score += 20
    if board.king(chess.BLACK) not in [chess.E8, chess.D8]:
        score -= 20

    # 4. Pawn structure (penalize doubled pawns)
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    
    for file_index in range(8): # Iterate through files A to H (0 to 7)
        # Count how many white and black pawns are on the current file
        w_pawns_on_file = sum(1 for sq in white_pawns if chess.square_file(sq) == file_index)
        b_pawns_on_file = sum(1 for sq in black_pawns if chess.square_file(sq) == file_index)
        
        # Penalize 15 points for each extra pawn on the same file
        if w_pawns_on_file > 1:
            score -= 15 * (w_pawns_on_file - 1)
        if b_pawns_on_file > 1:
            score += 15 * (b_pawns_on_file - 1)

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