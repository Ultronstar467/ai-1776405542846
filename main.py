from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Allow CORS for all origins during development
# In a production environment, you should restrict allow_origins
# to the specific domain(s) where your frontend is hosted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameState(BaseModel):
    board: List[List[str]]
    current_player: str
    winner: Optional[str] = None # 'X', 'O', 'Draw', or None
    game_over: bool = False

# Global game state variable
_game_state: GameState = None

def initialize_game() -> GameState:
    """Initializes and returns a new game state."""
    return GameState(
        board=[['', '', ''], ['', '', ''], ['', '', '']],
        current_player='X',
        winner=None,
        game_over=False
    )

def get_game_state_instance() -> GameState:
    """Returns the current game state, initializing it if it's the first request."""
    global _game_state
    if _game_state is None:
        _game_state = initialize_game()
    return _game_state

def check_winner(board: List[List[str]]) -> Optional[str]:
    """Checks the board for a winner."""
    # Check rows
    for row in board:
        if row[0] != '' and row[0] == row[1] == row[2]:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] != '' and board[0][col] == board[1][col] == board[2][col]:
            return board[0][col]
    # Check diagonals
    if board[0][0] != '' and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != '' and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return None

def check_draw(board: List[List[str]], winner: Optional[str]) -> bool:
    """Checks if the game is a draw."""
    if winner:
        return False # A winner means it's not a draw
    for row in board:
        if '' in row:
            return False # Empty cell found, game is not over yet
    return True # No winner and no empty cells means it's a draw

@app.get("/game", response_model=GameState)
async def get_current_game_state():
    """Retrieves the current state of the Tic Tac Toe game."""
    return get_game_state_instance()

class Move(BaseModel):
    row: int
    col: int

@app.post("/game/move", response_model=GameState)
async def make_player_move(move: Move):
    """
    Allows a player to make a move on the board.
    Validates the move and updates the game state.
    """
    global _game_state
    current_game = get_game_state_instance()

    if current_game.game_over:
        raise HTTPException(status_code=400, detail="Game is over. Please reset to play again.")

    if not (0 <= move.row < 3 and 0 <= move.col < 3):
        raise HTTPException(status_code=400, detail="Invalid move coordinates. Row and column must be between 0 and 2.")

    if current_game.board[move.row][move.col] != '':
        raise HTTPException(status_code=400, detail="Cell is already occupied. Choose an empty cell.")

    # Update board with the current player's move
    current_game.board[move.row][move.col] = current_game.current_player

    # Check for winner
    winner = check_winner(current_game.board)
    if winner:
        current_game.winner = winner
        current_game.game_over = True
    else:
        # Check for draw if no winner
        if check_draw(current_game.board, winner):
            current_game.winner = 'Draw'
            current_game.game_over = True
        else:
            # If no winner or draw, switch to the next player
            current_game.current_player = 'O' if current_game.current_player == 'X' else 'X'

    _game_state = current_game # Update the global state
    return _game_state

@app.post("/game/reset", response_model=GameState)
async def reset_game_endpoint():
    """Resets the game to its initial state."""
    global _game_state
    _game_state = initialize_game()
    return _game_state

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return open("index.html").read()
