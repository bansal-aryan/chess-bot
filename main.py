import random
import sys

import chess

from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

PIECE_SYMBOLS = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}

class ChessWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chess Bot")

        self.board = chess.Board()
        self.selected_square = None

        container = QWidget()
        page_layout = QVBoxLayout(container)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        self.status_label = QLabel("White to Move") 
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        board_frame = QFrame()
        board_frame.setFixedSize(568, 568)
        board_frame.setFrameShape(QFrame.Shape.Box)
        board_frame.setFrameShadow(QFrame.Shadow.Plain)
        board_frame.setLineWidth(4)

        board_layout = QGridLayout(board_frame)
        board_layout.setSpacing(0)
        board_layout.setContentsMargins(4, 4, 4, 4)

        self.buttons = {}

        for row in range(8):
            for col in range(8):
                chess_square = chess.square(col, 7 - row)

                square = QPushButton()
                square.setFixedSize(70, 70)
                
                square.clicked.connect(lambda checked=False, sq=chess_square: self.handle_square_click(sq))

                self.buttons[chess_square] = square

                board_layout.addWidget(square, row, col)

        page_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(board_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(
            board_frame,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        reset_button = QPushButton("New Game")
        reset_button.clicked.connect(self.reset_game)
        page_layout.addWidget(reset_button)

        self.setCentralWidget(container)
        self.refresh_board()

    def refresh_board(self):
        legal_destinations = set()

        if self.selected_square is not None:
            for move in self.board.legal_moves:
                if move.from_square == self.selected_square:
                    legal_destinations.add(move.to_square)

        for square, button in self.buttons.items():
            piece = self.board.piece_at(square)

            if piece is None:
                button.setText("")
            else:
                symbol = piece.symbol()
                button.setText(PIECE_SYMBOLS[symbol])

            file_number = chess.square_file(square)
            rank_number = chess.square_rank(square)

            if (file_number + rank_number) % 2 == 0:
                color = "#b58863"
            else:
                color = "#f0d9b5"
            if square == self.selected_square:
                color = "#f6f669"
            elif square in legal_destinations:
                color = "#90c978"

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    border: none;
                    font-size: 42px;
                }}
                """
            )

    def reset_game(self):
        self.board.reset()
        self.selected_square = None
        self.status_label.setText("White to move")
        self.refresh_board()

    def handle_square_click(self, square):
        if self.board.is_game_over(claim_draw=True):
            self.status_label.setText("The game is over")
            return

        clicked_piece = self.board.piece_at(square)

        if self.selected_square is None:
            self.select_piece(square, clicked_piece)
            return

        if (
            clicked_piece is not None
            and clicked_piece.color == self.board.turn
        ):
            self.select_piece(square, clicked_piece)
            return

        move = chess.Move(self.selected_square, square)

        selected_piece = self.board.piece_at(
            self.selected_square
        )

        if (
            selected_piece.piece_type == chess.PAWN
            and chess.square_rank(square) in (0, 7)
        ):
            move = chess.Move(
                self.selected_square,
                square,
                promotion=chess.QUEEN,
            )

        if move not in self.board.legal_moves:
            self.status_label.setText("That move is not legal")
            return

        move_name = self.board.san(move)

        self.board.push(move)
        self.selected_square = None

        self.update_status(move_name)
        self.refresh_board()

        self.make_bot_move()

    def select_piece(self, square, piece):
        square_name = chess.square_name(square)

        if piece is None:
            self.status_label.setText(
                f"{square_name} is empty"
            )
            return

        if piece.color != self.board.turn:
            self.status_label.setText(
                "Select one of your own pieces"
            )
            return

        self.selected_square = square
        self.status_label.setText(
            f"Selected {square_name}"
        )

        self.refresh_board()

    def update_status(self, move_name):
        if self.board.is_checkmate():
            winner = (
                "Black"
                if self.board.turn == chess.WHITE
                else "White"
            )

            self.status_label.setText(
                f"{winner} wins by checkmate"
            )
            return

        if self.board.is_game_over(claim_draw=True):
            outcome = self.board.outcome(claim_draw=True)

            self.status_label.setText(
                f"Game over: {outcome.result()}"
            )
            return

        current_player = (
            "White"
            if self.board.turn == chess.WHITE
            else "Black"
        )

        if self.board.is_check():
            self.status_label.setText(
                f"{move_name} — {current_player} is in check"
            )
        else:
            self.status_label.setText(
                f"{move_name} — {current_player} to move"
            )
            
    def make_bot_move(self):
        if self.board.is_game_over(claim_draw=True):
            return

        if self.board.turn != chess.BLACK:
            return

        legal_moves = list(self.board.legal_moves)
        move = random.choice(legal_moves)

        move_name = self.board.san(move)
        self.board.push(move)

        self.update_status(move_name)
        self.refresh_board()

app = QApplication(sys.argv)

window = ChessWindow()
window.show()

sys.exit(app.exec())