import chess

# Material values in centipawns. Scores are always White-positive.
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 800,
    chess.BISHOP: 1000,
    chess.ROOK: 1350,
    chess.QUEEN: 3700,
    chess.KING: 0,
}
CHECKMATE_SCORE = 100000

def evaluate_board(board: chess.Board) -> float:
    """Material balance: positive favors White, negative favors Black."""
    total = 0
    for piece_type, value in PIECE_VALUES.items():
        total += value * (
            len(board.pieces(piece_type, chess.WHITE))
            - len(board.pieces(piece_type, chess.BLACK))
        )
    return total


def terminal_score(board: chess.Board):
    """Return a White-positive score if the game is over, else None."""
    outcome = board.outcome(claim_draw=False)
    if outcome is None:
        return None
    if outcome.winner == chess.WHITE:
        return CHECKMATE_SCORE
    if outcome.winner == chess.BLACK:
        return -CHECKMATE_SCORE
    return 0  # stalemate, insufficient material, etc.


def minimax(board: chess.Board, depth: int) -> float:
    """Value of `board` searched `depth` plies. White maximizes, Black minimizes."""
    # Terminal outcomes are checked BEFORE the depth-0 cutoff.
    result = terminal_score(board)
    if result is not None:
        return result
    if depth <= 0:
        return evaluate_board(board)

    white_to_move = board.turn == chess.WHITE
    best = float("-inf") if white_to_move else float("inf")
    for move in list(board.legal_moves):
        board.push(move)
        try:
            value = minimax(board, depth - 1)
        finally:
            board.pop()  # always restore the board
        best = max(best, value) if white_to_move else min(best, value)
    return best


def choose_move(board: chess.Board, depth: int = 1):
    """Pick a legal move for the side to move, or None if the game is over."""
    if depth < 1:
        raise ValueError("Search depth must be at least 1.")
    if terminal_score(board) is not None:
        return None

    white_to_move = board.turn == chess.WHITE
    best_move, best_value = None, None
    for move in list(board.legal_moves):  # every legal candidate is explored
        board.push(move)
        try:
            value = minimax(board, depth - 1)
        finally:
            board.pop()
        better = (
            best_move is None
            or (white_to_move and value > best_value)
            or (not white_to_move and value < best_value)
        )
        if better:
            best_move, best_value = move, value
    return best_move
