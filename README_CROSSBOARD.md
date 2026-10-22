# CROSSBOARD prototype

This is a local, hot-seat prototype. The rules engine is independent from the
Tkinter screen; a later online or AI client can call the same GameState API.

## Run

Use Python 3.10 or later. Tkinter and unittest are part of the standard
Windows Python installation.

Run the game with: `python InterGameBoard.py`

`python main.py` is an equivalent alternate entry point.

No third-party package is required. Tkinter was selected so the prototype can
run on a standard desktop Python installation without downloading assets or
libraries.

## Tests

Run tests with: python -m unittest -v test_crossboard.py

## Provisional values and rules

- Shogi Rook and Bishop are included; promotion adds diagonal steps to the Rook and orthogonal steps to the Bishop. Xiangqi Horse checks its blocking leg square.
- Reversi movement and hand deployment require a valid bracket. Any friendly non-wall piece can anchor a ray; all bracketed enemy pieces flip together. Walls cut rays. These mixed-piece bracket details are provisional.
- Go groups use four-way adjacency. All occupants close liberties; walls interrupt adjacency because they are edges. Opponent groups are captured first in coordinate order, then any zero-liberty groups of the mover are removed without entering a hand. Self-atari is prohibited by default; `prohibit_self_atari=False` allows self-atari Go drops.

- The draft pool contains 20 distinct choices: two randomly chosen leaders and
  18 ordinary lots sampled across the ten source games. Each player first picks
  one leader, then the players alternate until each has taken ten sets. There
  are no draft points. Pawns and Checkers come in five-piece sets; Reversi, Go,
  and Quoridor lots contain ten pieces. The board is 8 by 8, and the player who
  drafted second takes the first game turn to balance the draft order.
- Each side drafts one leader. A Taishi is a normal draft piece; while on the
  board it lets its owner continue after losing their drafted leader. Captured
  Taishi changes hands and protects its new owner only after being redeployed.
- An even board treats the central four cells as the SLIPE goal area.
- Shogi promotion is automatic on entering the opponent's promotion zone;
  captured promoted Shogi pieces demote. Chess pawns can promote to a queen,
  bishop, knight, or rook and return to pawn form if captured. Shogi pawn
  drops enforce nifu.
- Chess castling is available only to an unmoved Chess King and unmoved Chess
  Rook on their home row, with a clear path and unattacked king path. En
  passant lasts for one reply.
- Checkers must capture when a capture is available and can chain captures.
- Quoridor walls are modeled as one blocked edge per wall token. They cannot be
  flipped or captured by Go. A wall may not remove a route for an on-board
  Quoridor runner.
- The listed Taikyoku moves and Chaturanga elephant are labeled provisional.
- Check/checkmate and Xiangqi facing-general rules are omitted; generals can
  be captured directly. Maximum 200 actions ends in a draw.

## Files

- crossboard.py: settings, draft catalog, state, move generation, captures,
  special abilities, and win conditions.
- crossboard_ui.py: Tkinter board, draft, hand, and restart screens.
- InterGameBoard.py: requested application entry point.
- main.py: application entry point.
- test_crossboard.py: standard-library engine tests.
