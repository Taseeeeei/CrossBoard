"""CROSSBOARD: a configurable local mixed-board-game prototype.

The rule engine is UI-independent. All numbers marked provisional live in
GameConfig or PieceSpec so playtesting can rebalance them without rule rewrites.
"""
from __future__ import annotations

from collections import deque
from copy import copy
from dataclasses import dataclass, field
import random
from typing import Iterable, Optional

Coord = tuple[int, int]
Edge = frozenset[Coord]
WallPlacement = tuple[str, int, int]

# Coordinate notation helpers: column = 9-1 (size - x), row = 一〜九 (y) (top-right is 1一)
_ROW_KANJI = "一二三四五六七八九"


def _coord(pos: Coord, size: int = 9) -> str:
    """Return a human-readable board coordinate string like '5五' (top-right is 1一)."""
    x, y = pos
    col = size - x
    row = _ROW_KANJI[y] if 0 <= y < len(_ROW_KANJI) else str(y + 1)
    return f"{col}{row}"

GAMES = (
    "Shogi", "Chess", "Othello", "Go", "Quoridor",
    "Xiangqi", "Taikyoku Shogi", "Checkers", "Chaturanga", "SLIPE",
)

@dataclass(frozen=True)
class PieceSpec:
    name: str
    source: str
    kind: str
    cost: int = 1
    quantity: int = 1
    general: bool = False
    goal: str = ""
    promotes_to: str = ""
    provisional: bool = False
    description: str = ""

LEADERS = (
    PieceSpec("王将", "Shogi", "shogi_king", 6, general=True),
    PieceSpec("キング", "Chess", "chess_king", 6, general=True),
    PieceSpec("ムーブピース", "Quoridor", "quoridor_runner", 6, general=True,
              goal="reach_far_rank"),
    PieceSpec("帥", "Xiangqi", "xiangqi_general", 6, general=True),
    PieceSpec("ラージャ", "Chaturanga", "chaturanga_king", 6, general=True),
    PieceSpec("SLIPEキング", "SLIPE", "slipe_king", 6, general=True,
              goal="reach_center"),
)

# Candidate lots, including repeated ten-piece bundles. Repeated lots are
# separate draft cards; each still has a single source game for weighting.
NORMAL_LOTS = (
    PieceSpec("歩", "Shogi", "shogi_pawn", 1, 5),
    PieceSpec("桂馬", "Shogi", "shogi_knight", 2),
    PieceSpec("銀将", "Shogi", "shogi_silver", 2),
    PieceSpec("金将", "Shogi", "shogi_gold", 3),
    PieceSpec("飛車", "Shogi", "shogi_rook", 4),
    PieceSpec("角行", "Shogi", "shogi_bishop", 4),
    PieceSpec("ポーン", "Chess", "chess_pawn", 1, 5),
    PieceSpec("ルーク", "Chess", "chess_rook", 4),
    PieceSpec("ビショップ", "Chess", "chess_bishop", 3),
    PieceSpec("ナイト", "Chess", "chess_knight", 3),
    PieceSpec("クイーン", "Chess", "chess_queen", 7),
    PieceSpec("リバーシ駒10枚", "Othello", "reversi", 5, 10),
    PieceSpec("リバーシ駒10枚", "Othello", "reversi", 5, 10),
    PieceSpec("リバーシ駒10枚", "Othello", "reversi", 5, 10),
    PieceSpec("囲碁駒10枚", "Go", "go_stone", 5, 10),
    PieceSpec("囲碁駒10枚", "Go", "go_stone", 5, 10),
    PieceSpec("囲碁駒10枚", "Go", "go_stone", 5, 10),
    PieceSpec("壁10枚", "Quoridor", "wall", 4, 10),
    PieceSpec("壁10枚", "Quoridor", "wall", 4, 10),
    PieceSpec("壁10枚", "Quoridor", "wall", 4, 10),
    PieceSpec("砲", "Xiangqi", "xiangqi_cannon", 4),
    PieceSpec("馬", "Xiangqi", "xiangqi_horse", 3),
    PieceSpec("象", "Xiangqi", "xiangqi_elephant", 2),
    PieceSpec("車", "Xiangqi", "xiangqi_rook", 4),
    # Taikyoku Shogi movement profiles follow the Wikipedia entries.
    PieceSpec("犬", "Taikyoku Shogi", "taikyoku_dog", 2),
    PieceSpec("仲人", "Taikyoku Shogi", "taikyoku_nakoudo", 2),
    PieceSpec("左車", "Taikyoku Shogi", "taikyoku_left_chariot", 2),
    PieceSpec("横猿", "Taikyoku Shogi", "taikyoku_side_monkey", 2),
    PieceSpec("竪行", "Taikyoku Shogi", "taikyoku_vertical_mover", 2),
    PieceSpec("飛牛", "Taikyoku Shogi", "taikyoku_flying_ox", 2),
    PieceSpec("弩兵", "Taikyoku Shogi", "taikyoku_crossbow_soldier", 2),
    PieceSpec("竪狗", "Taikyoku Shogi", "taikyoku_vertical_dog", 2),
    PieceSpec("竪馬", "Taikyoku Shogi", "taikyoku_vertical_horse", 2),
    PieceSpec("炮兵", "Taikyoku Shogi", "taikyoku_cannon_soldier", 2),
    PieceSpec("刀兵", "Taikyoku Shogi", "taikyoku_sword_soldier", 2),
    PieceSpec("角鷹", "Taikyoku Shogi", "taikyoku_angle_hawk", 2),
    PieceSpec("飛鷲", "Taikyoku Shogi", "taikyoku_flying_eagle", 2),
    PieceSpec("鎗兵", "Taikyoku Shogi", "taikyoku_spear_soldier", 2),
    PieceSpec("竪豹", "Taikyoku Shogi", "taikyoku_vertical_leopard", 2),
    PieceSpec("猛虎", "Taikyoku Shogi", "taikyoku_fierce_tiger", 2),
    PieceSpec("弓兵", "Taikyoku Shogi", "taikyoku_archer", 2),
    PieceSpec("狛犬", "Taikyoku Shogi", "taikyoku_komainu", 2),
    PieceSpec("吼犬", "Taikyoku Shogi", "taikyoku_roaring_dog", 2),
    PieceSpec("右車", "Taikyoku Shogi", "taikyoku_right_chariot", 2),
    PieceSpec("チェッカー駒", "Checkers", "checker", 2, 5),
    PieceSpec("ローカ", "Chaturanga", "chaturanga_rook", 3),
    PieceSpec("パダーティ", "Chaturanga", "chaturanga_pawn", 1, 5),
    PieceSpec("アシュワ", "Chaturanga", "chaturanga_knight", 3),
    PieceSpec("ガジャ", "Chaturanga", "chaturanga_elephant", 2, provisional=True,
              description="象の移動は再構成に幅があるため暫定移動"),
    PieceSpec("SLIPE駒", "SLIPE", "slipe_slider", 2),
    PieceSpec("SLIPE駒", "SLIPE", "slipe_slider", 2),
    PieceSpec("SLIPE駒", "SLIPE", "slipe_slider", 2),
)

@dataclass(frozen=True)
class DraftCard:
    card_id: str
    spec: PieceSpec

@dataclass
class GameConfig:
    size: int = 9
    max_turns: int = 200
    promotion_depth: int = 3
    prohibit_self_atari: bool = True
    allow_checkers_chain: bool = True

    def __post_init__(self) -> None:
        if self.size != 9:
            raise ValueError("盤面サイズは9×9固定です")

def sample_draft_pool(seed: Optional[int] = None) -> list[DraftCard]:
    """Build a 20-card pool with two leaders and 18 distinct piece lots."""
    rng = random.Random(seed)
    leaders = rng.sample(list(LEADERS), 2)
    by_game: dict[str, list[PieceSpec]] = {game: [] for game in GAMES}
    seen_kinds: set[str] = set()
    for spec in NORMAL_LOTS:
        if spec.kind not in seen_kinds:
            by_game[spec.source].append(spec)
            seen_kinds.add(spec.kind)
    pool: list[DraftCard] = [
        DraftCard(f"L{i}", spec) for i, spec in enumerate(leaders)
    ]
    available_games = [game for game in GAMES if by_game[game]]
    for i in range(18):
        source = rng.choice(available_games)
        choices = by_game[source]
        spec = rng.choice(choices)
        choices.remove(spec)
        if not choices:
            available_games.remove(source)
        pool.append(DraftCard(f"P{i}", spec))
    rng.shuffle(pool)
    return pool

@dataclass
class DraftSession:
    cards: list[DraftCard]
    config: GameConfig = field(default_factory=GameConfig)
    active: int = 0
    starting_player: int = 0
    rosters: list[list[PieceSpec]] = field(default_factory=lambda: [[], []])
    leader_selected: list[bool] = field(default_factory=lambda: [False, False])
    started: bool = False

    @classmethod
    def new(cls, seed: Optional[int] = None,
            config: Optional[GameConfig] = None) -> "DraftSession":
        rng = random.Random(seed)
        starting_player = rng.randrange(2)
        return cls(
            sample_draft_pool(seed), config or GameConfig(),
            active=starting_player, starting_player=starting_player,
        )

    def available_cards(self) -> list[DraftCard]:
        if not all(self.leader_selected):
            return [card for card in self.cards if card.spec.general]
        return self.cards

    def choose(self, card_id: str) -> PieceSpec:
        if self.started:
            raise ValueError("ドラフトは終了しています")
        card = next((c for c in self.cards if c.card_id == card_id), None)
        if card is None:
            raise ValueError("その候補はすでに取得済みです")
        if card not in self.available_cards():
            raise ValueError("最初に各プレイヤーが大将駒を1つずつ選んでください")
        player = self.active
        spec = card.spec
        if spec.general and self.leader_selected[player]:
            raise ValueError("大将駒は各プレイヤー1つまでです")
        self.cards.remove(card)
        self.rosters[player].append(spec)
        if spec.general:
            self.leader_selected[player] = True
        self.active = 1 - player
        if not self.cards:
            if not all(self.leader_selected):
                raise RuntimeError("各プレイヤーの大将駒が選ばれていません")
            self.started = True
        return spec

@dataclass
class Piece:
    uid: int
    spec: PieceSpec
    owner: int
    moved: bool = False
    promoted: bool = False
    base_kind: str = ""
    protected_royal: bool = False
    promotion_kind: str = ""

    @property
    def kind(self) -> str:
        return self.spec.kind if not self.promoted else {
            "shogi_pawn": "shogi_gold",
            "shogi_knight": "shogi_gold",
            "shogi_silver": "shogi_gold",
            "shogi_rook": "promoted_shogi_rook",
            "shogi_bishop": "promoted_shogi_bishop",
            "chess_pawn": self.promotion_kind or "chess_queen",
        }.get(self.base_kind or self.spec.kind, self.spec.kind)

    @property
    def general(self) -> bool:
        return self.spec.general

    @property
    def taishi(self) -> bool:
        return self.kind == "taishi"

@dataclass
class Move:
    origin: Coord
    target: Coord
    special: str = ""
    captured: Optional[Coord] = None

@dataclass
class GameResult:
    winner: Optional[int]
    draw: bool = False
    reason: str = ""

def edge(a: Coord, b: Coord) -> Edge:
    return frozenset((a, b))

class GameState:
    """Rule authority for moves, captures, abilities, and outcome."""
    def __init__(self, config: Optional[GameConfig] = None,
                 first_player: int = 0) -> None:
        self.config = config or GameConfig()
        self.size = self.config.size
        self.board: dict[Coord, Piece] = {}
        self.hands: list[list[Piece]] = [[], []]
        self.wall_hands = [0, 0]
        # Each wall is (orientation, x, y), anchored in a 2x2 block of cells.
        self.walls: set[WallPlacement] = set()
        self.turn = first_player
        self.turns = 0
        self.result: Optional[GameResult] = None
        self.events: list[str] = []
        self.en_passant: Optional[tuple[Coord, Coord, int]] = None
        self.forced_checker: Optional[int] = None
        self._next_uid = 1

    def in_bounds(self, p: Coord) -> bool:
        return 0 <= p[0] < self.size and 0 <= p[1] < self.size

    def at(self, p: Coord) -> Optional[Piece]:
        return self.board.get(p)

    def make_piece(self, spec: PieceSpec, owner: int) -> Piece:
        p = Piece(self._next_uid, spec, owner, base_kind=spec.kind)
        self._next_uid += 1
        return p

    def add_piece(self, spec: PieceSpec, owner: int, pos: Coord) -> Piece:
        if owner not in (0, 1) or not self.in_bounds(pos) or pos in self.board:
            raise ValueError("駒を配置できません")
        if spec.kind == "wall":
            raise ValueError("壁はマスではなく辺に配置します")
        p = self.make_piece(spec, owner)
        self.board[pos] = p
        return p

    def add_roster_to_hand(self, rosters: list[list[PieceSpec]]) -> None:
        if len(rosters) != 2 or any(sum(s.general for s in roster) != 1 for roster in rosters):
            raise ValueError("各プレイヤーは大将駒をちょうど1つ必要とします")
        for owner, roster in enumerate(rosters):
            for spec in roster:
                if spec.kind == "wall":
                    self.wall_hands[owner] += spec.quantity
                else:
                    for _ in range(spec.quantity):
                        self.hands[owner].append(self.make_piece(spec, owner))

    def setup_rosters(self, rosters: list[list[PieceSpec]]) -> None:
        """Place pieces in each player's home three ranks.

        Layout rules:
        - General: center of the front row (closest row to the player).
        - Weak pieces (cost == 1, e.g. pawns): front row, centered; overflow
          to the second row if the front row is full.
        - Other pieces: remaining home cells (rows 2-3 from front), shuffled.
        - reversi / go_stone pieces stay in hand (they are dropped during play).
        """
        self.add_roster_to_hand(rosters)
        for owner in (0, 1):
            # Row indices from the player's perspective:
            #   home_y    = back row (closest to player)  → general placed here
            #   mid_y     = middle row                    → strong pieces (random)
            #   vanguard_y= front row (closest to foe)   → weak pieces (centered)
            if owner == 0:
                home_y, mid_y, vanguard_y = self.size - 1, self.size - 2, self.size - 3
            else:
                home_y, mid_y, vanguard_y = 0, 1, 2
            cx = self.size // 2

            hand = self.hands[owner]

            # --- Place general at center of the home (back) row ---
            leader = next(p for p in hand if p.general)
            hand.remove(leader)
            self.board[(cx, home_y)] = leader

            # Chess king: also place rooks at the edges of the home row for
            # castling before distributing other pieces.
            if leader.kind == "chess_king":
                for rook_x in (0, self.size - 1):
                    rook = next((p for p in hand if p.kind == "chess_rook"), None)
                    if rook is not None and (rook_x, home_y) not in self.board:
                        hand.remove(rook)
                        self.board[(rook_x, home_y)] = rook

            # --- Separate deployable pieces into weak vs. strong ---
            def _is_deployable(p) -> bool:
                return p.kind not in ("reversi", "go_stone", "wall")

            weak_pieces = [p for p in hand if _is_deployable(p) and (p.spec.cost <= 1 or p.kind == "checker")]
            strong_pieces = [p for p in hand if _is_deployable(p) and p.spec.cost > 1 and p.kind != "checker"]

            for p in weak_pieces + strong_pieces:
                hand.remove(p)
            # Wall pieces stay in hand as wall counts.
            for p in [p for p in hand if p.kind == "wall"]:
                hand.remove(p)
                self.wall_hands[owner] += 1

            # --- Vanguard row: weak pieces, center-out, overflow to mid row ---
            vanguard_cells = sorted(
                [(x, vanguard_y) for x in range(self.size)],
                key=lambda c: abs(c[0] - cx),
            )
            mid_cells = [(x, mid_y) for x in range(self.size)]
            overflow_pool = iter(mid_cells)

            vanguard_iter = iter(vanguard_cells)
            for p in weak_pieces:
                placed = False
                for cell in vanguard_iter:
                    if cell not in self.board:
                        self.board[cell] = p
                        placed = True
                        break
                if not placed:
                    for cell in overflow_pool:
                        if cell not in self.board:
                            self.board[cell] = p
                            break

            # --- Mid + remaining home cells only: strong pieces (random) ---
            # Vanguard row is reserved for weak pieces and is excluded here.
            remaining_cells = [
                (x, y)
                for y in (mid_y, home_y)
                for x in range(self.size)
                if (x, y) not in self.board
            ]
            random.shuffle(remaining_cells)

            for p, cell in zip(strong_pieces, remaining_cells):
                self.board[cell] = p

    def _forward(self, owner: int) -> int:
        return -1 if owner == 0 else 1

    def _neighbors(self, p: Coord, diagonals: bool = False) -> list[Coord]:
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        if diagonals:
            dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
        return [(p[0]+dx,p[1]+dy) for dx,dy in dirs
                if self.in_bounds((p[0]+dx,p[1]+dy))]

    def _blocked(self, a: Coord, b: Coord) -> bool:
        return self._movement_crosses_wall(a, b)

    def _movement_crosses_wall(
        self, a: Coord, b: Coord,
        walls: Optional[set[WallPlacement]] = None,
    ) -> bool:
        """Return whether the straight movement path intersects a wall."""
        ax, ay = a[0] + 0.5, a[1] + 0.5
        bx, by = b[0] + 0.5, b[1] + 0.5
        placements = self.walls if walls is None else walls
        for orientation, x, y in placements:
            if orientation == "horizontal":
                wall_y = y + 1
                if ay == by or (ay - wall_y) * (by - wall_y) > 0:
                    continue
                t = (wall_y - ay) / (by - ay)
                crossing_x = ax + t * (bx - ax)
                if x <= crossing_x <= x + 2:
                    return True
            else:
                wall_x = x + 1
                if ax == bx or (ax - wall_x) * (bx - wall_x) > 0:
                    continue
                t = (wall_x - ax) / (bx - ax)
                crossing_y = ay + t * (by - ay)
                if y <= crossing_y <= y + 2:
                    return True
        return False

    def _ray(self, origin: Coord, dirs: Iterable[Coord], piece: Piece,
             max_steps: Optional[int] = None) -> list[Move]:
        moves: list[Move] = []
        limit = max_steps or self.size
        for dx, dy in dirs:
            cur = origin
            for _ in range(limit):
                nxt = (cur[0]+dx, cur[1]+dy)
                if not self.in_bounds(nxt) or self._blocked(cur, nxt):
                    break
                target = self.board.get(nxt)
                if target is None:
                    moves.append(Move(origin, nxt))
                    cur = nxt
                    continue
                if target.owner != piece.owner and target.kind != "wall":
                    moves.append(Move(origin, nxt, captured=nxt))
                break
        return moves

    def _step_moves(
        self, origin: Coord, piece: Piece,
        offsets: Iterable[Coord],
        ignore_walls: bool = False,
    ) -> list[Move]:
        out = []
        for dx, dy in offsets:
            q = (origin[0]+dx, origin[1]+dy)
            if not self.in_bounds(q):
                continue
            if not ignore_walls and self._blocked(origin, q):
                continue
            target = self.board.get(q)
            if target is None:
                out.append(Move(origin, q))
            elif target.owner != piece.owner and target.kind != "wall":
                out.append(Move(origin, q, captured=q))
        return out

    def _jump_moves(
        self, origin: Coord, piece: Piece, jumps: Iterable[tuple[int, int, int]]
    ) -> list[Move]:
        """Generate leaps, skipping intervening pieces while respecting walls."""
        out: list[Move] = []
        for dx, dy, distance in jumps:
            cur = origin
            for _ in range(distance):
                nxt = (cur[0] + dx, cur[1] + dy)
                if not self.in_bounds(nxt) or self._blocked(cur, nxt):
                    break
                cur = nxt
            else:
                target = self.board.get(cur)
                if target is None:
                    out.append(Move(origin, cur))
                elif target.owner != piece.owner and target.kind != "wall":
                    out.append(Move(origin, cur, captured=cur))
        return out

    def _taikyoku_moves(self, pos: Coord, piece: Piece) -> list[Move]:
        """Wikipedia movement profiles for the Taikyoku Shogi pieces in this set."""
        kind = piece.kind
        f = self._forward(piece.owner)
        orth = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        diag = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        forward_diags = [(1, f), (-1, f)]
        backward_diags = [(1, -f), (-1, -f)]
        step_dirs: list[Coord] = []
        rays: list[tuple[list[Coord], Optional[int]]] = []
        jumps: list[tuple[int, int, int]] = []

        if kind == "taikyoku_dog":
            step_dirs = [(-1, f), (0, f), (1, f)]
        elif kind == "taikyoku_nakoudo":
            step_dirs = [(0, f), (0, -f)]
        elif kind == "taikyoku_left_chariot":
            left = f
            step_dirs = [(left, 0)]
            rays = [([(0, f)], None), ([(-left, f)], None), ([(left, -f)], None)]
        elif kind == "taikyoku_side_monkey":
            step_dirs = [(0, -f), (-1, f), (1, f)]
            rays = [([(1, 0), (-1, 0)], None)]
        elif kind == "taikyoku_vertical_mover":
            step_dirs = [(1, 0), (-1, 0)]
            rays = [([(0, 1), (0, -1)], None)]
        elif kind == "taikyoku_flying_ox":
            rays = [([(0, 1), (0, -1)], None), (diag, None)]
        elif kind == "taikyoku_crossbow_soldier":
            # 弩兵 (longbow soldier): its side range is two, its forward
            # diagonal range is five, and its forward orthogonal range is unlimited.
            step_dirs = [(0, -f)]
            rays = [([(1, 0), (-1, 0)], 2), (forward_diags, 5), ([(0, f)], None)]
        elif kind == "taikyoku_vertical_dog":
            step_dirs = [(-1, -f), (0, -f), (1, -f)]
            rays = [([(0, f)], None)]
        elif kind == "taikyoku_vertical_horse":
            step_dirs = [(0, -f), *forward_diags]
            rays = [([(0, f)], None)]
        elif kind == "taikyoku_cannon_soldier":
            step_dirs = [(0, -f)]
            rays = [([(1, 0), (-1, 0)], 3), (forward_diags, 5), ([(0, f)], 7)]
        elif kind == "taikyoku_sword_soldier":
            step_dirs = [(0, -f), *forward_diags]
        elif kind == "taikyoku_angle_hawk":
            rays = [(orth + diag, None)]
            jumps = [(0, f, 2)]
        elif kind == "taikyoku_flying_eagle":
            rays = [(orth + diag, None)]
            jumps = [(dx, f, 2) for dx in (-1, 1)]
        elif kind == "taikyoku_spear_soldier":
            step_dirs = [(0, -f), (1, 0), (-1, 0)]
            rays = [([(0, f)], None)]
        elif kind == "taikyoku_vertical_leopard":
            step_dirs = [(0, -f), (1, 0), (-1, 0), *forward_diags]
            rays = [([(0, f)], None)]
        elif kind == "taikyoku_fierce_tiger":
            rays = [([(0, f)], None)]
        elif kind == "taikyoku_archer":
            # 弓兵 (crossbow soldier), distinct from the 弩兵 above.
            step_dirs = [(0, -f)]
            rays = [([(1, 0), (-1, 0)], 3), (forward_diags, 3), ([(0, f)], 5)]
        elif kind == "taikyoku_komainu":
            rays = [(orth + diag, None)]
            jumps = [(dx, dy, 3) for dx, dy in orth + diag]
        elif kind == "taikyoku_roaring_dog":
            rays = [([(0, 1), (0, -1), (1, 0), (-1, 0)], None),
                    (forward_diags, None), (backward_diags, 3)]
            jumps = [(dx, dy, 3) for dx, dy in orth + forward_diags]
        elif kind == "taikyoku_right_chariot":
            right = -f
            step_dirs = [(right, 0)]
            rays = [([(0, f)], None), ([(-right, f)], None), ([(right, -f)], None)]
        else:
            return []

        out = self._step_moves(pos, piece, step_dirs)
        for directions, limit in rays:
            out.extend(self._ray(pos, directions, piece, limit))
        out.extend(self._jump_moves(pos, piece, jumps))
        # Roaring dog has jump targets that overlap its ranging moves.
        unique: dict[Coord, Move] = {move.target: move for move in out}
        return list(unique.values())

    def _reversi_flips(self, pos: Coord, owner: int) -> set[Coord]:
        """Return enemy pieces bracketed by a Reversi landing.

        Only a friendly Reversi piece closes a ray. Enemy pieces of any kind
        can be flipped; walls and friendly non-Reversi pieces interrupt a ray.
        """
        flips: set[Coord] = set()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),
                       (1,1),(1,-1),(-1,1),(-1,-1)):
            ray: list[Coord] = []
            cur = pos
            while True:
                nxt = (cur[0] + dx, cur[1] + dy)
                if not self.in_bounds(nxt) or self._blocked(cur, nxt):
                    break
                victim = self.board.get(nxt)
                if victim is None:
                    break
                if victim.owner == owner:
                    if victim.kind != "reversi":
                        break
                    if ray:
                        flips.update(ray)
                    break
                ray.append(nxt)
                cur = nxt
        return flips

    def _line_clear(self, a: Coord, b: Coord) -> bool:
        dx = (b[0] > a[0]) - (b[0] < a[0])
        dy = (b[1] > a[1]) - (b[1] < a[1])
        cur = a
        while cur != b:
            nxt = (cur[0]+dx, cur[1]+dy)
            if self._blocked(cur, nxt):
                return False
            cur = nxt
        return True

    def pseudo_moves(self, pos: Coord, include_castles: bool = True) -> list[Move]:
        piece = self.board[pos]
        k, o, f = piece.kind, piece.owner, self._forward(piece.owner)
        orth = [(1,0),(-1,0),(0,1),(0,-1)]
        diag = [(1,1),(1,-1),(-1,1),(-1,-1)]
        king = orth + diag
        gold = [(0,f),(1,f),(-1,f),(1,0),(-1,0),(0,-f)]
        if k in ("shogi_king","chess_king","xiangqi_general","chaturanga_king","taishi"):
            offsets = king if k != "xiangqi_general" else [(0,1),(0,-1),(1,0),(-1,0)]
            if k == "xiangqi_general":
                rows = range(self.size-3, self.size) if o == 0 else range(0,3)
                return [m for m in self._step_moves(pos,piece,offsets)
                        if m.target[0] in range(self.size//2-1,self.size//2+2)
                        and m.target[1] in rows]
            out = self._step_moves(pos, piece, offsets)
            if k == "chess_king" and include_castles:
                out += self._castles(pos, piece)
            return out
        if k in ("chess_rook","xiangqi_rook","chaturanga_rook"):
            return self._ray(pos, orth, piece)
        if k in ("chess_bishop",):
            return self._ray(pos, diag, piece)
        if k in ("chess_queen",):
            return self._ray(pos, king, piece)
        if k in ("chess_knight","shogi_knight","chaturanga_knight"):
        # Leapers jump over pieces. Knights and Keima also leap over Quoridor walls.
            steps = [(1,2),(-1,2),(1,-2),(-1,-2)] if k == "shogi_knight" else [
                (1,2),(-1,2),(1,-2),(-1,-2),(2,1),(-2,1),(2,-1),(-2,-1)]
            return self._step_moves(pos, piece, steps, ignore_walls=True)
        if k == "shogi_pawn":
            return self._step_moves(pos,piece,[(0,f)])
        if k == "shogi_silver":
            return self._step_moves(pos,piece,[(0,f),(1,f),(-1,f),(1,-f),(-1,-f)])
        if k in ("shogi_gold","promoted_shogi_pawn"):
            return self._step_moves(pos,piece,gold)
        if k == "promoted_shogi_rook":
            return self._ray(pos,orth,piece) + self._step_moves(pos,piece,diag)
        if k == "promoted_shogi_bishop":
            return self._ray(pos,diag,piece) + self._step_moves(pos,piece,orth)
        if k == "shogi_bishop":
            return self._ray(pos,diag,piece)
        if k == "shogi_rook":
            return self._ray(pos,orth,piece)
        if k == "chess_pawn":
            out = []
            one = (pos[0], pos[1]+f)
            if self.in_bounds(one) and one not in self.board and not self._blocked(pos,one):
                out.append(Move(pos,one))
            start = self.size-2 if o == 0 else 1
            two = (pos[0],pos[1]+2*f)
            if (
                pos[1] == start and not piece.moved and self.in_bounds(two)
                and two not in self.board and not self._blocked(pos,one)
                and not self._blocked(one,two)
            ):
                out.append(Move(pos,two,"pawn_double"))
            for dx in (-1,1):
                q=(pos[0]+dx,pos[1]+f)
                if not self.in_bounds(q) or self._blocked(pos,q):
                    continue
                enemy=self.board.get(q)
                if enemy and enemy.owner != o:
                    out.append(Move(pos,q,captured=q))
                elif self.en_passant and self.en_passant[0] == q \
                        and self.en_passant[2] == o:
                    out.append(Move(pos,q,"en_passant",self.en_passant[1]))
            return out
        if k == "chaturanga_pawn":
            out=[]
            forward=(pos[0],pos[1]+f)
            if self.in_bounds(forward) and forward not in self.board and not self._blocked(pos,forward):
                out.append(Move(pos,forward))
            for dx in (-1,1):
                q=(pos[0]+dx,pos[1]+f)
                if not self.in_bounds(q) or self._blocked(pos,q):
                    continue
                target=self.board.get(q)
                if target is not None and target.owner != o:
                    out.append(Move(pos,q,captured=q))
            return out
        if k == "chaturanga_elephant":
            # Provisional CROSSBOARD profile: two-square diagonal leap.
            out=[]
            for dx,dy in diag:
                q=(pos[0]+2*dx,pos[1]+2*dy)
                if self.in_bounds(q) and not self._blocked(pos,q):
                    t=self.board.get(q)
                    if t is None or t.owner != o:
                        out.append(Move(pos,q,captured=q if t else None))
            return out
        if k == "xiangqi_elephant":
            out=[]
            for dx,dy in diag:
                q=(pos[0]+2*dx,pos[1]+2*dy)
                eye=(pos[0]+dx,pos[1]+dy)
                if (not self.in_bounds(q) or eye in self.board
                    or self._blocked(pos,eye) or self._blocked(eye,q)
                    or self._blocked(pos,q)):
                    continue
                if (o == 0 and q[1] < self.size//2) or (o == 1 and q[1] >= self.size//2):
                    continue
                t=self.board.get(q)
                if t is None or t.owner != o:
                    out.append(Move(pos,q,captured=q if t else None))
            return out
        if k == "xiangqi_horse":
            out=[]
            for dx,dy in ((1,2),(-1,2),(1,-2),(-1,-2),
                          (2,1),(-2,1),(2,-1),(-2,-1)):
                q=(pos[0]+dx,pos[1]+dy)
                leg=(pos[0]+(1 if dx > 0 else -1),pos[1]) if abs(dx)==2 else (
                    pos[0],pos[1]+(1 if dy > 0 else -1))
                if not self.in_bounds(q) or leg in self.board or self._blocked(pos,q):
                    continue
                if self._blocked(pos,leg) or self._blocked(leg,q):
                    continue
                t=self.board.get(q)
                if t is None or t.owner != o:
                    out.append(Move(pos,q,captured=q if t else None))
            return out
        if k == "xiangqi_cannon":
            return self._cannon_moves(pos,piece)
        if k == "checker":
            out=[]
            dirs=[(-1,f),(1,f)]
            if piece.promoted:
                dirs += [(-1,-f),(1,-f)]
            for dx,dy in dirs:
                q=(pos[0]+dx,pos[1]+dy)
                if self.in_bounds(q) and not self._blocked(pos,q):
                    t=self.board.get(q)
                    if t is None:
                        out.append(Move(pos,q))
                    elif t.owner != o:
                        jump=(pos[0]+2*dx,pos[1]+2*dy)
                        if (self.in_bounds(jump) and jump not in self.board
                            and not self._blocked(q,jump) and not self._blocked(pos,jump)):
                            out.append(Move(pos,jump,"checker_capture",q))
            return out
        if k == "reversi":
            return [m for m in self._step_moves(pos,piece,king)
                    if m.captured is None and self._reversi_flips(m.target,o)]
        if k == "go_stone":
            # Go stones are stationary once placed; use reserve deployment.
            return []
        if k in ("slipe_slider","slipe_king"):
            out=[]
            for dx,dy in orth:
                cur=pos
                while True:
                    q=(cur[0]+dx,cur[1]+dy)
                    if not self.in_bounds(q) or self._blocked(cur,q) or q in self.board:
                        break
                    cur=q
                if cur != pos:
                    out.append(Move(pos,cur,"slipe"))
            return out
        if k == "quoridor_runner":
            return self._step_moves(pos,piece,orth)
        if piece.spec.source == "Taikyoku Shogi":
            return self._taikyoku_moves(pos, piece)
        if k == "chaturanga_rook":
            return self._ray(pos,orth,piece)
        return []

    def _cannon_moves(self, pos: Coord, piece: Piece) -> list[Move]:
        out=[]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            cur=pos
            screen=False
            for _ in range(self.size):
                q=(cur[0]+dx,cur[1]+dy)
                if not self.in_bounds(q) or self._blocked(cur,q):
                    break
                t=self.board.get(q)
                if not screen:
                    if t is None:
                        out.append(Move(pos,q))
                    else:
                        screen=True
                elif t is not None:
                    if t.owner != piece.owner:
                        out.append(Move(pos,q,captured=q))
                    break
                cur=q
        return out

    def _castles(self, pos: Coord, king: Piece) -> list[Move]:
        if king.moved:
            return []
        home_y=self.size-1 if king.owner == 0 else 0
        if pos != (self.size//2,home_y):
            return []
        out=[]
        for rook_x, dest_x, rook_dest_x in (
            (0, self.size//2-2, self.size//2-1),
            (self.size-1, self.size//2+2, self.size//2+1),
        ):
            rook=self.board.get((rook_x,home_y))
            if not rook or rook.kind != "chess_rook" or rook.owner != king.owner or rook.moved:
                continue
            lo,hi=sorted((pos[0],rook_x))
            if any((x,home_y) in self.board for x in range(lo+1,hi)):
                continue
            path=[(x,home_y) for x in range(pos[0],dest_x+((dest_x>pos[0])-(dest_x<pos[0])),(dest_x>pos[0])-(dest_x<pos[0]))]
            if any(not self.in_bounds(q) or self._is_attacked(q,1-king.owner) for q in path):
                continue
            if any(self._blocked((x,home_y),(x+((dest_x>pos[0])-(dest_x<pos[0])),home_y))
                   for x in range(min(pos[0],dest_x),max(pos[0],dest_x))):
                continue
            out.append(Move(pos,(dest_x,home_y),"castle"))
        return out

    def _is_attacked(self, target: Coord, by: int) -> bool:
        # Attack zones are based on piece movement, with pawn diagonals handled
        # separately because they attack differently from how they move.
        for pos,p in self.board.items():
            if p.owner != by:
                continue
            if p.kind in ("chess_pawn","chaturanga_pawn"):
                f=self._forward(by)
                if (target[1] == pos[1]+f and abs(target[0]-pos[0]) == 1
                        and not self._blocked(pos,target)):
                    return True
                continue
            # A king standing on target is treated as capturable by the usual
            # pseudo-move generator. Exclude castling to avoid recursive checks.
            if any(move.target == target or move.captured == target
                   for move in self.pseudo_moves(pos, include_castles=False)):
                return True
        return False

    def _is_checkable_royal(self, piece: Piece) -> bool:
        # The Quoridor runner wins by reaching a goal instead of using check
        # rules. All kings and every Taishi must remain outside attack zones.
        return piece.taishi or (
            (piece.general or piece.protected_royal)
            and piece.kind != "quoridor_runner"
        )

    def _side_in_check(self, owner: int) -> bool:
        return any(
            self._is_attacked(pos, 1 - owner)
            for pos, piece in self.board.items()
            if piece.owner == owner and self._is_checkable_royal(piece)
        )

    def is_in_check(self, owner: int) -> bool:
        """Return whether any royal piece belonging to owner is attacked."""
        return self._side_in_check(owner)

    def _move_keeps_royals_safe(
        self,
        move: Move,
        owner: int,
        promote: bool = False,
        promotion_kind: str | None = None,
    ) -> bool:
        original_board = self.board
        original_hands = self.hands
        original_events = self.events
        original_result = self.result
        sim_board = {pos: copy(piece) for pos, piece in original_board.items()}
        mover = sim_board.pop(move.origin)

        if move.special == "castle":
            home_y = move.origin[1]
            rook_x = 0 if move.target[0] < move.origin[0] else self.size - 1
            rook_dest = (move.origin[0] - 1 if rook_x == 0 else move.origin[0] + 1, home_y)
            rook = sim_board.pop((rook_x, home_y))
            rook.moved = True
            sim_board[rook_dest] = rook

        capture_pos = move.captured or (
            move.target if move.target in sim_board and sim_board[move.target].owner != owner else None
        )
        if capture_pos is not None:
            sim_board.pop(capture_pos, None)
        mover.moved = True
        if promotion_kind is not None:
            mover.promoted = True
            mover.promotion_kind = promotion_kind
        elif promote or (
            mover.kind == "chess_pawn"
            and move.target[1] == (0 if owner == 0 else self.size - 1)
        ):
            mover.promoted = True
            if (mover.base_kind or mover.spec.kind) == "chess_pawn":
                mover.promotion_kind = "chess_queen"
        sim_board[move.target] = mover

        self.board = sim_board
        self.hands = [hand.copy() for hand in original_hands]
        self.events = original_events.copy()
        try:
            if mover.kind == "reversi":
                for pos in self._reversi_flips(move.target, owner):
                    flipped = self.board.get(pos)
                    if flipped is None:
                        continue
                    if flipped.general:
                        self.board.pop(pos, None)
                    else:
                        flipped.owner = owner
            self._resolve_go(owner)
            return not self._side_in_check(owner)
        finally:
            self.board = original_board
            self.hands = original_hands
            self.events = original_events
            self.result = original_result

    def _drop_keeps_royals_safe(self, piece: Piece, pos: Coord, owner: int) -> bool:
        original_board = self.board
        original_hands = self.hands
        original_events = self.events
        original_result = self.result
        sim_board = {square: copy(placed) for square, placed in original_board.items()}
        dropped = copy(piece)
        dropped.owner = owner
        dropped.moved = True
        sim_board[pos] = dropped

        self.board = sim_board
        self.hands = [hand.copy() for hand in original_hands]
        self.events = original_events.copy()
        try:
            if dropped.kind == "reversi":
                for flipped_pos in self._reversi_flips(pos, owner):
                    flipped = self.board.get(flipped_pos)
                    if flipped is None:
                        continue
                    if flipped.general:
                        self.board.pop(flipped_pos, None)
                    else:
                        flipped.owner = owner
            self._resolve_go(owner)
            return not self._side_in_check(owner)
        finally:
            self.board = original_board
            self.hands = original_hands
            self.events = original_events
            self.result = original_result

    def legal_moves(self, pos: Coord) -> list[Move]:
        if self.result or pos not in self.board or self.board[pos].owner != self.turn:
            return []
        piece=self.board[pos]
        moves=self.pseudo_moves(pos)
        captures=[m for q,p in self.board.items() if p.owner==self.turn
                  and p.kind=="checker"
                  for m in self.pseudo_moves(q) if m.special=="checker_capture"]
        if captures:
            if piece.kind != "checker":
                return []
            moves=[m for m in moves if m.special=="checker_capture"]
        if self.forced_checker is not None and piece.uid != self.forced_checker:
            return []
        return [move for move in moves if self._move_keeps_royals_safe(move, piece.owner)]

    def promotion_target_name(self, piece: Piece) -> str:
        if piece.base_kind == "chess_pawn" and piece.promoted:
            return {
                "chess_queen": "クイーン",
                "chess_bishop": "ビショップ",
                "chess_knight": "ナイト",
                "chess_rook": "ルーク",
            }.get(piece.kind, "クイーン")
        return piece.spec.promotes_to

    def can_promote(self, move: Move) -> bool:
        piece=self.board.get(move.origin)
        if piece is None or piece.promoted:
            return False
        kind=piece.base_kind or piece.spec.kind
        if kind == "chess_pawn":
            last_rank = 0 if piece.owner == 0 else self.size - 1
            return move.target[1] == last_rank
        shogi_kinds={
            "shogi_pawn", "shogi_knight", "shogi_silver", "shogi_rook",
            "shogi_bishop",
        }
        is_taikyoku=(piece.spec.source == "Taikyoku Shogi"
                     and bool(self.promotion_target_name(piece)))
        if kind not in shogi_kinds and not is_taikyoku:
            return False
        depth=self.config.promotion_depth
        def in_zone(pos: Coord) -> bool:
            if piece.owner == 0:
                return pos[1] < depth
            return pos[1] >= self.size-depth

        origin_in_zone=in_zone(move.origin)
        target_in_zone=in_zone(move.target)
        if is_taikyoku:
            # In Taikyoku Shogi, promotion is available on entering the zone,
            # or by capturing while already inside it.
            entered_zone=target_in_zone and not origin_in_zone
            captured_in_zone=(origin_in_zone and target_in_zone
                              and (move.captured is not None or move.target in self.board))
            return entered_zone or captured_in_zone
        return origin_in_zone or target_in_zone

    def _can_drop(self, piece: Piece, pos: Coord, owner: int) -> bool:
        if self.result or owner != self.turn or not self.in_bounds(pos) or pos in self.board:
            return False
        k=piece.kind
        last_rank = 0 if self._forward(owner) == -1 else self.size-1
        if k in ("shogi_pawn","chess_pawn","chaturanga_pawn") and pos[1] == last_rank:
            return False
        if k == "shogi_knight":
            forbidden = {0, 1} if self._forward(owner) == -1 else {self.size-2, self.size-1}
            if pos[1] in forbidden:
                return False
        if k == "shogi_pawn":
            if any(p.owner==owner and p.kind=="shogi_pawn" and q[0]==pos[0]
                   for q,p in self.board.items()):
                return False
        if k == "xiangqi_general":
            rows=range(self.size-3,self.size) if owner==0 else range(0,3)
            if pos[0] not in range(self.size//2-1,self.size//2+2) or pos[1] not in rows:
                return False
        if k == "go_stone" and self.config.prohibit_self_atari:
            if self._go_drop_is_self_atari(piece, pos, owner):
                return False
        if piece.taishi and sum(
            p.owner == owner and p.taishi for p in self.board.values()
        ) >= 2:
            return False
        return self._drop_keeps_royals_safe(piece, pos, owner)

    def legal_drops(self, hand_index: int) -> list[Coord]:
        if self.result or not 0 <= hand_index < len(self.hands[self.turn]):
            return []
        piece=self.hands[self.turn][hand_index]
        return [(x,y) for y in range(self.size) for x in range(self.size)
                if self._can_drop(piece,(x,y),self.turn)]

    def apply_drop(self, hand_index: int, pos: Coord) -> None:
        if self.result:
            raise ValueError("対局は終了しています")
        if pos not in self.legal_drops(hand_index):
            raise ValueError("不正な手駒配置です")
        piece=self.hands[self.turn][hand_index]
        if piece.kind == "go_stone" and self.config.prohibit_self_atari:
            if self._go_drop_is_self_atari(piece, pos, self.turn):
                raise ValueError("自軍の囲碁集団の呼吸点をすべて塞ぐ配置です")
        piece=self.hands[self.turn].pop(hand_index)
        piece.owner=self.turn
        piece.moved=True
        self.board[pos]=piece
        self.events.append(f"{piece.spec.name}打{_coord(pos, self.size)}")
        self._resolve_after_action(self.turn, moved_piece=piece, pos=pos)

    def apply_move(
        self,
        move: Move,
        promote: bool = False,
        promotion_kind: str | None = None,
    ) -> None:
        if self.result:
            raise ValueError("対局は終了しています")
        if move not in self.legal_moves(move.origin):
            raise ValueError("不正な移動です")
        moving_piece = self.board[move.origin]
        is_chess_pawn = (moving_piece.base_kind or moving_piece.spec.kind) == "chess_pawn"
        last_rank = 0 if moving_piece.owner == 0 else self.size - 1
        is_chess_promotion = is_chess_pawn and move.target[1] == last_rank
        allowed_promotion_kinds = {
            "chess_queen", "chess_bishop", "chess_knight", "chess_rook",
        }
        if promotion_kind is not None:
            if not is_chess_promotion or promotion_kind not in allowed_promotion_kinds:
                raise ValueError("ポーンの昇格先が不正です")
        elif is_chess_promotion:
            promotion_kind = "chess_queen"
        if promote and not self.can_promote(move):
            raise ValueError("この移動では成れません")
        actor=self.turn
        if not self._move_keeps_royals_safe(
            move, actor, promote=promote, promotion_kind=promotion_kind
        ):
            raise ValueError("王が敵の攻撃範囲に残る手です")
        piece=self.board.pop(move.origin)
        if move.special == "castle":
            home_y=move.origin[1]
            rook_x=0 if move.target[0] < move.origin[0] else self.size-1
            rook_dest=(move.origin[0]-1 if rook_x==0 else move.origin[0]+1,home_y)
            rook=self.board.pop((rook_x,home_y))
            self.board[rook_dest]=rook
            rook.moved=True
        capture_pos=move.captured or (move.target if move.target in self.board else None)
        if capture_pos and capture_pos in self.board:
            self._capture(capture_pos,actor)
        if move.special=="en_passant" and move.captured:
            if move.captured in self.board:
                self._capture(move.captured,actor)
        self.board[move.target]=piece
        piece.moved=True
        self.en_passant=None
        if move.special=="pawn_double":
            mid=(move.origin[0],(move.origin[1]+move.target[1])//2)
            self.en_passant=(mid,move.target,1-actor)
        self._promote_if_needed(piece,move.target,promote,promotion_kind)
        self.events.append(
            f"{piece.spec.name} {_coord(move.origin, self.size)}→{_coord(move.target, self.size)}"
        )
        self._resolve_after_action(
            actor,
            piece,
            move.target,
            checker_capture=move.special == "checker_capture",
        )

    def _capture(self, pos: Coord, captor: int) -> None:
        victim=self.board.pop(pos)
        if victim.general:
            self.events.append(f"大将駒「{victim.spec.name}」を捕獲")
            return
        # A promoted chess pawn becomes a pawn in hand; Shogi promotions demote.
        if victim.base_kind == "chess_pawn" and victim.promoted:
            victim.spec=PieceSpec("ポーン","Chess","chess_pawn",1)
            victim.base_kind="chess_pawn"
            victim.promoted=False
            victim.promotion_kind=""
        elif victim.promoted and victim.base_kind in (
            "shogi_pawn", "shogi_knight", "shogi_silver", "shogi_rook",
            "shogi_bishop",
        ):
            victim.promoted=False
        elif victim.promoted and victim.spec.source == "Taikyoku Shogi":
            victim.promoted=False
        victim.owner=captor
        victim.moved=True
        self.hands[captor].append(victim)
        self.events.append(f"{victim.spec.name}を手駒にした")

    def _promote_if_needed(
        self,
        p: Piece,
        pos: Coord,
        promote: bool = False,
        promotion_kind: str | None = None,
    ) -> None:
        last=0 if p.owner==0 else self.size-1
        if p.kind=="chess_pawn" and pos[1]==last:
            p.promoted=True
            p.promotion_kind = promotion_kind or "chess_queen"
            target_name = self.promotion_target_name(p)
            self.events.append(f"ポーンを{target_name}に昇格")
        elif p.kind=="checker" and pos[1]==last:
            p.promoted=True
            self.events.append("チェッカー駒をキング化")
        elif promote:
            p.promoted=True
            target_name=self.promotion_target_name(p)
            if target_name:
                self.events.append(f"{p.spec.name}が{target_name}に成った")
            else:
                self.events.append(f"{p.spec.name}が成った")

    def _capture_reversi(self, p: Piece, pos: Coord) -> None:
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            ray=[]; cur=pos
            while True:
                q=(cur[0]+dx,cur[1]+dy)
                if not self.in_bounds(q) or self._blocked(cur,q):
                    break
                victim=self.board.get(q)
                if victim is None:
                    break
                if victim.owner==p.owner:
                    if victim.kind!="reversi":
                        break
                    if ray:
                        for r in ray:
                            flipped=self.board[r]
                            if flipped.general:
                                self.board.pop(r)
                                self.result=GameResult(p.owner,False,"大将駒がリバーシ能力で裏返された")
                                self.events.append("大将駒が裏返され、対局終了")
                            else:
                                flipped.owner=p.owner
                        if ray:
                            self.events.append(f"{len(ray)}個を裏返し")
                    break
                ray.append(q); cur=q

    def _go_groups(self) -> list[set[Coord]]:
        unseen={p for p,v in self.board.items() if v.kind=="go_stone"}
        groups=[]
        while unseen:
            root=min(unseen,key=lambda q:(q[1],q[0]))
            owner=self.board[root].owner
            group={root}; queue=deque([root]); unseen.remove(root)
            while queue:
                cur=queue.popleft()
                for n in self._neighbors(cur):
                    if self._blocked(cur,n):
                        continue
                    if n in unseen and self.board[n].owner==owner:
                        unseen.remove(n); group.add(n); queue.append(n)
            groups.append(group)
        return groups

    def _owned_piece_groups(self, owner: int) -> list[set[Coord]]:
        unseen={pos for pos,piece in self.board.items() if piece.owner==owner}
        groups=[]
        while unseen:
            root=min(unseen,key=lambda q:(q[1],q[0]))
            group={root}; queue=deque([root]); unseen.remove(root)
            while queue:
                cur=queue.popleft()
                for neighbor in self._neighbors(cur):
                    if self._blocked(cur,neighbor):
                        continue
                    if neighbor in unseen:
                        unseen.remove(neighbor); group.add(neighbor); queue.append(neighbor)
            groups.append(group)
        return groups

    def _surrounded_by_go(self, group: set[Coord], captor: int) -> bool:
        boundary=set()
        for pos in group:
            for neighbor in self._neighbors(pos):
                if not self._blocked(pos,neighbor) and neighbor not in group:
                    boundary.add(neighbor)
        return bool(boundary) and all(
            neighbor in self.board
            and self.board[neighbor].owner==captor
            and self.board[neighbor].kind=="go_stone"
            for neighbor in boundary
        )

    def _go_captured_groups(self, captor: int) -> list[set[Coord]]:
        return [
            group for group in self._owned_piece_groups(1-captor)
            if self._surrounded_by_go(group,captor)
        ]

    def _go_drop_is_self_atari(self, piece: Piece, pos: Coord, owner: int) -> bool:
        """Check a Go drop after removing opponent groups it would capture."""
        self.board[pos] = piece
        removed: dict[Coord, Piece] = {}
        try:
            # Preserve ordinary Go captures when an opponent Go group has no
            # empty liberties, even when that group is not enclosed solely by
            # this player's Go stones.
            for group in self._go_groups():
                anchor = min(group, key=lambda q:(q[1],q[0]))
                if self.board[anchor].owner != owner and not self.go_liberties(group):
                    for q in group:
                        removed[q] = self.board.pop(q)
            for group in self._go_captured_groups(owner):
                for q in group:
                    removed[q] = self.board.pop(q)
            own_group = next(g for g in self._go_groups() if pos in g)
            return not self.go_liberties(own_group)
        finally:
            self.board.pop(pos, None)
            self.board.update(removed)

    def go_liberties(self, group: set[Coord]) -> set[Coord]:
        libs=set()
        for p in group:
            for q in self._neighbors(p):
                if not self._blocked(p,q) and q not in self.board:
                    libs.add(q)
        return libs

    def _resolve_go(self, actor: int) -> None:
        # Preserve ordinary Go captures and also capture any opponent-owned
        # piece group enclosed entirely by the mover's Go stones.
        while True:
            captured=set()
            for group in self._go_groups():
                anchor=min(group,key=lambda q:(q[1],q[0]))
                if (self.board[anchor].owner != actor
                        and not self.go_liberties(group)):
                    captured.update(group)
            for group in self._go_captured_groups(actor):
                captured.update(group)
            if not captured:
                break
            for pos in sorted(captured,key=lambda q:(q[1],q[0])):
                if pos in self.board:
                    self._capture(pos,actor)

        # A self-captured Go group leaves the board without entering a hand.
        while True:
            dead=[group for group in self._go_groups()
                  if not self.go_liberties(group)
                  and self.board[min(group,key=lambda q:(q[1],q[0]))].owner==actor]
            if not dead:
                break
            for group in sorted(dead,key=lambda g:min((q[1],q[0]) for q in g)):
                for pos in sorted(group,key=lambda q:(q[1],q[0])):
                    if pos in self.board:
                        self.board.pop(pos)
                        self.events.append("自軍の囲碁駒が自殺手で盤上から除去")

    def _resolve_after_action(self, actor: int, moved_piece: Optional[Piece],
                              pos: Coord, checker_capture: bool = False) -> None:
        if moved_piece and moved_piece.kind=="reversi":
            self._capture_reversi(moved_piece,pos)
        if not self.result:
            self._resolve_go(actor)
        if not self.result:
            lost=[owner for owner in (0,1) if not self._has_royal(owner)]
            if len(lost)==2:
                self.result=GameResult(None,True,"両陣営の王格が同時に失われた")
            elif len(lost)==1:
                self.result=GameResult(1-lost[0],False,"王格をすべて失った")
        if not self.result:
            for ppos,p in self.board.items():
                if p.general and p.spec.goal=="reach_center" and p.kind=="slipe_king":
                    if ppos in self._center_cells():
                        self.result=GameResult(p.owner,False,"SLIPE王が中央に到達")
                elif p.general and p.spec.goal=="reach_far_rank" and p.kind=="quoridor_runner":
                    if (p.owner==0 and ppos[1]==0) or (p.owner==1 and ppos[1]==self.size-1):
                        self.result=GameResult(p.owner,False,"コリドールの駒が最終行に到達")
        if self.result:
            return
        if (checker_capture and moved_piece and moved_piece.kind == "checker"
                and self.config.allow_checkers_chain):
            more=[m for m in self.pseudo_moves(pos) if m.special=="checker_capture"]
            if more:
                self.forced_checker=moved_piece.uid
                self.events.append("連続捕獲を続ける")
                return
        self.forced_checker=None
        self.turns+=1
        if self.turns>=self.config.max_turns:
            self.result=GameResult(None,True,"最大手数に到達")
        else:
            self.turn=1-actor

    def _has_royal(self, owner: int) -> bool:
        return any(p.owner==owner and (p.general or p.taishi)
                   for p in self.board.values())

    def _center_cells(self) -> set[Coord]:
        mid=self.size//2
        xs=[mid] if self.size%2 else [mid-1,mid]
        ys=[mid] if self.size%2 else [mid-1,mid]
        return {(x,y) for x in xs for y in ys}

    def legal_wall_edges(self, owner: int) -> list[WallPlacement]:
        if owner != self.turn or self.wall_hands[owner] <= 0 or self.result:
            return []
        candidates=[]
        for y in range(self.size - 1):
            for x in range(self.size - 1):
                for wall in (("horizontal", x, y), ("vertical", x, y)):
                    if self._wall_conflicts(wall):
                        continue
                    if self._path_remains_after_wall(wall):
                        candidates.append(wall)
        return candidates

    def _wall_conflicts(self, proposed: WallPlacement) -> bool:
        orientation, x, y = proposed
        for existing_orientation, existing_x, existing_y in self.walls:
            if orientation == existing_orientation:
                if orientation == "horizontal":
                    same_line = y == existing_y
                    overlaps = max(x, existing_x) < min(x + 2, existing_x + 2)
                else:
                    same_line = x == existing_x
                    overlaps = max(y, existing_y) < min(y + 2, existing_y + 2)
                if same_line and overlaps:
                    return True
                continue

            horizontal = proposed if orientation == "horizontal" else (
                existing_orientation, existing_x, existing_y
            )
            vertical = proposed if orientation == "vertical" else (
                existing_orientation, existing_x, existing_y
            )
            _, horizontal_x, horizontal_y = horizontal
            _, vertical_x, vertical_y = vertical
            if (horizontal_x < vertical_x + 1 < horizontal_x + 2
                    and vertical_y < horizontal_y + 1 < vertical_y + 2):
                return True
        return False

    def _path_remains_after_wall(self, proposed: WallPlacement) -> bool:
        walls=self.walls|{proposed}
        for owner in (0,1):
            runners=[p for p in self.board.values()
                     if p.owner==owner and p.kind=="quoridor_runner"]
            if not runners:
                continue
            start=next((q for q,p in self.board.items()
                        if p is runners[0]),None)
            if start is None: continue
            goal=0 if owner==0 else self.size-1
            seen={start}; queue=deque([start]); found=False
            while queue:
                cur=queue.popleft()
                if cur[1]==goal:
                    found=True; break
                for nxt in self._neighbors(cur):
                    if not self._movement_crosses_wall(cur,nxt,walls) and nxt not in seen:
                        seen.add(nxt); queue.append(nxt)
            if not found:
                return False
        return (
            self._board_connected_after_walls(walls)
            and self._wall_keeps_royals_safe(walls, self.turn)
        )

    def _wall_keeps_royals_safe(self, walls: set[WallPlacement], owner: int) -> bool:
        original_walls = self.walls
        original_board = self.board
        original_hands = self.hands
        original_events = self.events
        original_result = self.result
        self.walls = walls
        self.board = {pos: copy(piece) for pos, piece in original_board.items()}
        self.hands = [hand.copy() for hand in original_hands]
        self.events = original_events.copy()
        try:
            self._resolve_go(owner)
            return not self._side_in_check(owner)
        finally:
            self.walls = original_walls
            self.board = original_board
            self.hands = original_hands
            self.events = original_events
            self.result = original_result

    def _board_connected_after_walls(self, walls: set[WallPlacement]) -> bool:
        """Reject a wall if it divides any board squares into unreachable areas."""
        start=(0,0)
        seen={start}
        queue=deque([start])
        while queue:
            cur=queue.popleft()
            for nxt in self._neighbors(cur):
                if nxt in seen or self._movement_crosses_wall(cur,nxt,walls):
                    continue
                seen.add(nxt)
                queue.append(nxt)
        return len(seen)==self.size*self.size

    def place_wall(self, wall: WallPlacement) -> None:
        if self.result:
            raise ValueError("対局は終了しています")
        if wall not in self.legal_wall_edges(self.turn):
            raise ValueError("壁を配置できません")
        self.wall_hands[self.turn]-=1
        self.walls.add(wall)
        orient_label = "横" if wall[0] == "horizontal" else "縦"
        self.events.append(f"壁{orient_label} {_coord((wall[1], wall[2]), self.size)}")
        self._resolve_after_action(self.turn,None,(-1,-1))
