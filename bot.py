import chess

PIECE_VALUES = {
    chess.PAWN: 1000, 
    chess.KNIGHT: 3000,
    chess.BISHOP: 3700, 
    chess.ROOK: 5000,
    chess.QUEEN: 9000,
    chess.KING: 0,
}

def evaluate_board(board):
    score = 0

    for piece_type, value in PIECE_VALUES.items():
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))

        score += white_count * value
        score -= black_count * value

    return score

def find_best_move(board):
    best_move = None
    best_score = float("inf")

    for move in board.legal_moves:
        board.push(move)

        score = evaluate_board(board)

        board.pop()

        if score < best_score:
            best_score = score
            best_move = move

    return best_move