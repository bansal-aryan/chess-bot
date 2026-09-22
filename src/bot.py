import chess


PIECE_VALUES = {
    chess.PAWN: 1000,
    chess.KNIGHT: 3000,
    chess.BISHOP: 3700,
    chess.ROOK: 5000,
    chess.QUEEN: 9000,
    chess.KING: 0,
}

MATE_SCORE = 1_000_000

PHASE_WEIGHTS = {
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
}

STARTING_PHASE = 24

PASSED_PAWN_BONUS = (0, 0, 100, 200, 400, 700, 1200, 0)


def terminal_score(board, ply=0):
    outcome = board.outcome()

    if outcome is None:
        return None

    if outcome.winner is None:
        return 0

    if outcome.winner == chess.WHITE:
        return MATE_SCORE - ply

    return -MATE_SCORE + ply


def game_phase(board):
    phase = 0

    for piece_type, weight in PHASE_WEIGHTS.items():
        count = (
            len(board.pieces(piece_type, chess.WHITE))
            + len(board.pieces(piece_type, chess.BLACK))
        )
        phase += count * weight

    return min(phase, STARTING_PHASE) / STARTING_PHASE


def piece_position_score(piece_type, square, color, phase):
    file = chess.square_file(square)
    rank = chess.square_rank(square)

    relative_rank = rank if color == chess.WHITE else 7 - rank

    file_center = min(file, 7 - file)
    rank_center = min(rank, 7 - rank)
    centrality = file_center + rank_center

    if piece_type == chess.PAWN:
        return (
            25 * relative_rank
            + 20 * file_center
            + 15 * relative_rank * file_center
        )

    if piece_type == chess.KNIGHT:
        return 70 * centrality - 210

    if piece_type == chess.BISHOP:
        development = 60 if relative_rank > 0 else 0
        return 35 * centrality + development

    if piece_type == chess.ROOK:
        return 180 if relative_rank == 6 else 0

    if piece_type == chess.QUEEN:
        return int(25 * centrality * (1 - phase))

    if piece_type == chess.KING:
        opening = -90 * centrality - 70 * relative_rank

        if relative_rank == 0 and file in (2, 6):
            opening += 250

        ending = 100 * centrality

        return int(
            phase * opening
            + (1 - phase) * ending
        )

    return 0


def pawn_structure_score(board, color, phase):
    score = 0
    pawns = board.pieces(chess.PAWN, color)
    enemy_pawns = board.pieces(chess.PAWN, not color)

    pawns_per_file = [0] * 8

    for square in pawns:
        pawns_per_file[chess.square_file(square)] += 1

    for count in pawns_per_file:
        score -= 140 * max(0, count - 1)

    for square in pawns:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        relative_rank = rank if color == chess.WHITE else 7 - rank

        has_left_neighbor = (
            file > 0 and pawns_per_file[file - 1] > 0
        )
        has_right_neighbor = (
            file < 7 and pawns_per_file[file + 1] > 0
        )

        if not has_left_neighbor and not has_right_neighbor:
            score -= 160

        if board.attackers(color, square) & pawns:
            score += 70

        is_passed = True

        for enemy_square in enemy_pawns:
            enemy_file = chess.square_file(enemy_square)
            enemy_rank = chess.square_rank(enemy_square)

            same_or_adjacent_file = abs(enemy_file - file) <= 1

            if color == chess.WHITE:
                enemy_is_ahead = enemy_rank > rank
            else:
                enemy_is_ahead = enemy_rank < rank

            if same_or_adjacent_file and enemy_is_ahead:
                is_passed = False
                break

        if is_passed:
            bonus = PASSED_PAWN_BONUS[relative_rank]
            score += int(bonus * (1 + (1 - phase)))

    return score


def rook_activity_score(board, color):
    score = 0

    own_pawn_files = {
        chess.square_file(square)
        for square in board.pieces(chess.PAWN, color)
    }

    enemy_pawn_files = {
        chess.square_file(square)
        for square in board.pieces(chess.PAWN, not color)
    }

    for square in board.pieces(chess.ROOK, color):
        file = chess.square_file(square)

        if file not in own_pawn_files:
            if file not in enemy_pawn_files:
                score += 200
            else:
                score += 100

    return score


def king_safety_score(board, color, phase):
    king_square = board.king(color)

    if king_square is None:
        raise ValueError("The position must contain both kings.")

    score = 0
    file = chess.square_file(king_square)
    rank = chess.square_rank(king_square)

    forward = 1 if color == chess.WHITE else -1
    shield_rank = rank + forward

    if 0 <= shield_rank < 8:
        for shield_file in range(max(0, file - 1), min(8, file + 2)):
            shield_square = chess.square(shield_file, shield_rank)
            piece = board.piece_at(shield_square)

            if (
                piece is not None
                and piece.color == color
                and piece.piece_type == chess.PAWN
            ):
                score += 100

    for nearby_square in board.attacks(king_square):
        attacker_count = len(
            board.attackers(not color, nearby_square)
        )
        score -= 45 * attacker_count

    return int(score * phase)


def evaluate_board(board, ply=0):
    result = terminal_score(board, ply)

    if result is not None:
        return result

    phase = game_phase(board)
    score = 0

    for color in (chess.WHITE, chess.BLACK):
        side_score = 0

        for piece_type, value in PIECE_VALUES.items():
            squares = board.pieces(piece_type, color)
            side_score += len(squares) * value

            for square in squares:
                side_score += piece_position_score(
                    piece_type,
                    square,
                    color,
                    phase,
                )

        if len(board.pieces(chess.BISHOP, color)) >= 2:
            side_score += 250

        side_score += pawn_structure_score(board, color, phase)
        side_score += rook_activity_score(board, color)
        side_score += king_safety_score(board, color, phase)

        if color == chess.WHITE:
            score += side_score
        else:
            score -= side_score

    return score


def move_order_score(board, move):
    score = 0

    if board.is_capture(move):
        attacker = board.piece_at(move.from_square)

        if board.is_en_passant(move):
            victim_value = PIECE_VALUES[chess.PAWN]
        else:
            victim = board.piece_at(move.to_square)
            victim_value = PIECE_VALUES[victim.piece_type]

        score += (
            10 * victim_value
            - PIECE_VALUES[attacker.piece_type]
        )

    if move.promotion is not None:
        score += PIECE_VALUES[move.promotion]

    return score


def ordered_moves(board):
    return sorted(
        board.legal_moves,
        key=lambda move: move_order_score(board, move),
        reverse=True,
    )


def minimax(board, depth, alpha, beta, ply):
    result = terminal_score(board, ply)

    if result is not None:
        return result

    if depth == 0:
        return evaluate_board(board, ply)

    if board.turn == chess.WHITE:
        best_score = float("-inf")

        for move in ordered_moves(board):
            board.push(move)

            try:
                score = minimax(
                    board, depth - 1, alpha, beta, ply + 1
                )
            finally:
                board.pop()

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)

            if alpha >= beta:
                break

        return best_score

    best_score = float("inf")

    for move in ordered_moves(board):
        board.push(move)

        try:
            score = minimax(
                board, depth - 1, alpha, beta, ply + 1
            )
        finally:
            board.pop()

        best_score = min(best_score, score)
        beta = min(beta, best_score)

        if alpha >= beta:
            break

    return best_score


def find_best_move(board, depth=2):
    if depth < 1:
        raise ValueError("Search depth must be at least 1.")

    if terminal_score(board) is not None:
        return None

    maximizing = board.turn == chess.WHITE

    best_move = None
    best_score = (
        float("-inf") if maximizing else float("inf")
    )

    alpha = float("-inf")
    beta = float("inf")

    for move in ordered_moves(board):
        board.push(move)

        try:
            score = minimax(
                board, depth - 1, alpha, beta, ply=1
            )
        finally:
            board.pop()

        if (
            best_move is None
            or (maximizing and score > best_score)
            or (not maximizing and score < best_score)
        ):
            best_score = score
            best_move = move

        if maximizing:
            alpha = max(alpha, best_score)
        else:
            beta = min(beta, best_score)

    return best_move


if __name__ == "__main__":
    board = chess.Board()

    print("Starting evaluation:", evaluate_board(board))
    print("Suggested move:", find_best_move(board, depth=2))