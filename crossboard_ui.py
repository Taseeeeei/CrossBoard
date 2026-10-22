"""Tkinter local UI for CROSSBOARD (Tkinter is included with standard Python)."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

from crossboard import DraftSession, GameConfig, GameState, Move, sample_draft_pool


class CrossboardUI:
    CELL = 72
    COLORS = ("#b94949", "#3974aa")
    SIDE_NAMES = ("白", "黒")
    PIECE_IMAGE_SIZE = 58
    HAND_IMAGE_SIZE = 44
    HAND_TILE_SIZE = 58
    HAND_TRAY_WIDTH = 154
    CONTROL_PANEL_WIDTH = 286
    PIECE_SOURCE_NAMES = {
        "Shogi": "将棋",
        "Chess": "チェス",
        "Othello": "オセロ",
        "Go": "囲碁",
        "Quoridor": "コリドール",
        "Xiangqi": "シャンチー",
        "Taikyoku Shogi": "大局将棋",
        "Checkers": "チェッカー",
        "Chaturanga": "チャトランガ",
        "SLIPE": "スライプ",
    }
    CHESS_PROMOTION_OPTIONS = (
        ("クイーン", "chess_queen"),
        ("ビショップ", "chess_bishop"),
        ("ナイト", "chess_knight"),
        ("ルーク", "chess_rook"),
    )
    PIECE_IMAGE_FILES = {
        "shogi_king": ("Shogi/king.png", "Shogi/king.png"),
        "shogi_pawn": ("Shogi/pawn.png", "Shogi/pawn.png"),
        "shogi_knight": ("Shogi/knight.png", "Shogi/knight.png"),
        "shogi_silver": ("Shogi/silver.png", "Shogi/silver.png"),
        "shogi_gold": ("Shogi/gold.png", "Shogi/gold.png"),
        "shogi_rook": ("Shogi/rook.png", "Shogi/rook.png"),
        "shogi_bishop": ("Shogi/bishop.png", "Shogi/bishop.png"),
        "chess_king": ("chess/king_White.png", "chess/king_Black.png"),
        "chess_pawn": ("chess/pawn_White.png", "chess/pawn_Black.png"),
        "chess_rook": ("chess/rook_White.png", "chess/rook_Black.png"),
        "chess_bishop": ("chess/bishop_White.png", "chess/bishop_Black.png"),
        "chess_knight": ("chess/knight_White.png", "chess/knight_Black.png"),
        "chess_queen": ("chess/queen_White.png", "chess/queen_Black.png"),
        "reversi": ("Reversi/Reversi_White.png", "Reversi/Reversi_Black.png"),
        "go_stone": ("Go/Go_White.png", "Go/Go_Black.png"),
        "quoridor_runner": ("Quoridor/Quoridor_White.png", "Quoridor/Quoridor_Black.png"),
        "xiangqi_general": ("Xiangqi/帥_White.png", "Xiangqi/將_Black.png"),
        "xiangqi_cannon": ("Xiangqi/炮_White.png", "Xiangqi/砲_Black.png"),
        "xiangqi_horse": ("Xiangqi/馬_White.png", "Xiangqi/馬_Black.png"),
        "xiangqi_elephant": ("Xiangqi/相_White.png", "Xiangqi/象_Black.png"),
        "xiangqi_rook": ("Xiangqi/車_White.png", "Xiangqi/車_Black.png"),
        "taikyoku_dog": ("Taikyoku-Shogi/inu.png", "Taikyoku-Shogi/inu.png"),
        "taikyoku_nakoudo": ("Taikyoku-Shogi/chunin.png", "Taikyoku-Shogi/chunin.png"),
        "taikyoku_left_chariot": ("Taikyoku-Shogi/shuba.png", "Taikyoku-Shogi/shuba.png"),
        "taikyoku_side_monkey": ("Taikyoku-Shogi/sasha.png", "Taikyoku-Shogi/sasha.png"),
        "taikyoku_vertical_mover": ("Taikyoku-Shogi/shugyo,png.png", "Taikyoku-Shogi/shugyo,png.png"),
        "taikyoku_flying_ox": ("Taikyoku-Shogi/higyu.png", "Taikyoku-Shogi/higyu.png"),
        "taikyoku_crossbow_soldier": ("Taikyoku-Shogi/dohei.png", "Taikyoku-Shogi/dohei.png"),
        "taikyoku_vertical_dog": ("Taikyoku-Shogi/inu.png", "Taikyoku-Shogi/inu.png"),
        "taikyoku_vertical_horse": ("Taikyoku-Shogi/hiju.png", "Taikyoku-Shogi/hiju.png"),
        "taikyoku_cannon_soldier": ("Taikyoku-Shogi/hohei.png", "Taikyoku-Shogi/hohei.png"),
        "taikyoku_sword_soldier": ("Taikyoku-Shogi/tohei.png", "Taikyoku-Shogi/tohei.png"),
        "taikyoku_angle_hawk": ("Taikyoku-Shogi/kakuo.png", "Taikyoku-Shogi/kakuo.png"),
        "taikyoku_flying_eagle": ("Taikyoku-Shogi/oen.png", "Taikyoku-Shogi/oen.png"),
        "taikyoku_spear_soldier": ("Taikyoku-Shogi/sohei.png", "Taikyoku-Shogi/sohei.png"),
        "taikyoku_vertical_leopard": ("Taikyoku-Shogi/shuhyo.png", "Taikyoku-Shogi/shuhyo.png"),
        "taikyoku_fierce_tiger": ("Taikyoku-Shogi/moko.png", "Taikyoku-Shogi/moko.png"),
        "taikyoku_archer": ("Taikyoku-Shogi/kyuhei.png", "Taikyoku-Shogi/kyuhei.png"),
        "taikyoku_komainu": ("Taikyoku-Shogi/komainu.png", "Taikyoku-Shogi/komainu.png"),
        "taikyoku_roaring_dog": ("Taikyoku-Shogi/koken.png", "Taikyoku-Shogi/koken.png"),
        "taikyoku_right_chariot": ("Taikyoku-Shogi/shuku.png", "Taikyoku-Shogi/shuku.png"),
        "checker": ("Checkers/Checkers_White.png", "Checkers/Checkers_Black.png"),
        "chaturanga_king": ("Chaturanga/Raja_White.png", "Chaturanga/Raja_Black.png"),
        "chaturanga_rook": ("Chaturanga/Ratha_White.png", "Chaturanga/Ratha_Black.png"),
        "chaturanga_pawn": ("Chaturanga/Padati_White.png", "Chaturanga/Padati_Black.png"),
        "chaturanga_knight": ("Chaturanga/Ashva_White.png", "Chaturanga/Ashva_Black.png"),
        "chaturanga_elephant": ("Chaturanga/Gaja_White.png", "Chaturanga/Gaja_Black.png"),
        "slipe_king": ("SLIPE/SLIPE_White.png", "SLIPE/SLIPE_Black.png"),
        "slipe_slider": ("SLIPE/SLIPE_White.png", "SLIPE/SLIPE_Black.png"),
    }
    PROMOTED_PIECE_IMAGE_FILES = {
        "shogi_pawn": ("Shogi/prom_pawn.png", "Shogi/prom_pawn.png"),
        "shogi_knight": ("Shogi/prom_knight.png", "Shogi/prom_knight.png"),
        "shogi_silver": ("Shogi/prom_silver.png", "Shogi/prom_silver.png"),
        "shogi_rook": ("Shogi/dragon.png", "Shogi/dragon.png"),
        "shogi_bishop": ("Shogi/horse.png", "Shogi/horse.png"),
        "checker": ("Checkers/CheckersKing_White.png", "Checkers/CheckersKing_Black.png"),
    }
    PIECE_MOVEMENT_TEXT = {
        "shogi_king": "縦・横・斜めのいずれかへ1マス。",
        "chaturanga_king": "縦・横・斜めのいずれかへ1マス。",
        "xiangqi_general": "縦または横へ1マス。宮の中だけ移動できます。",
        "quoridor_runner": "縦または横へ1マス。",
        "slipe_king": "縦または横に何マスでも進めます。",
        "slipe_slider": "縦または横に何マスでも進めます。",
        "shogi_pawn": "前へ1マス。",
        "shogi_knight": "前方へ2マス進み、左右どちらかへ1マス跳びます。",
        "shogi_silver": "前へ1マス、または前後斜めへ1マス。",
        "shogi_gold": "前・左右・後ろへ1マス、または前斜めへ1マス。",
        "promoted_shogi_pawn": "前・左右・後ろへ1マス、または前斜めへ1マス。",
        "shogi_rook": "縦または横に何マスでも進めます。",
        "promoted_shogi_rook": "縦横に何マスでも進め、斜めへ1マス動けます。",
        "shogi_bishop": "斜めに何マスでも進めます。",
        "promoted_shogi_bishop": "斜めに何マスでも進め、縦横へ1マス動けます。",
        "chess_king": "縦・横・斜めのいずれかへ1マス。",
        "chess_pawn": "前へ1マス。初期位置では条件を満たせば2マス進めます。捕獲は前斜めです。",
        "chess_rook": "縦または横に何マスでも進めます。",
        "chess_bishop": "斜めに何マスでも進めます。",
        "chess_knight": "縦横に2マスと1マスのL字に跳びます。途中の駒は飛び越せます。",
        "chess_queen": "縦・横・斜めに何マスでも進めます。",
        "reversi": "盤上を移動しません。手駒から空きマスに置きます。",
        "go_stone": "盤上を移動しません。手駒から交点に置きます。",
        "xiangqi_cannon": "縦または横に進みます。捕獲時は間に駒を1枚挟みます。",
        "xiangqi_horse": "縦横に2マスと1マスのL字に進みます。途中の足が塞がると進めません。",
        "xiangqi_elephant": "斜めに2マス進みます。途中の目が塞がると進めず、川を越えられません。",
        "xiangqi_rook": "縦または横に何マスでも進めます。",
        "taikyoku_dog": "前または前斜めへ1マス。",
        "taikyoku_nakoudo": "前後へ1マス。",
        "taikyoku_left_chariot": "左へ1マス。前へ何マスでも、前斜め右・後ろ斜め左へ何マスでも進めます。",
        "taikyoku_side_monkey": "後ろまたは前斜めへ1マス。横へ何マスでも進めます。",
        "taikyoku_vertical_mover": "横へ1マス、または縦に何マスでも進めます。",
        "taikyoku_flying_ox": "縦または斜めに何マスでも進めます。",
        "taikyoku_crossbow_soldier": "後ろへ1マス。横は2マスまで、前斜めは5マスまで、前は何マスでも進めます。",
        "taikyoku_vertical_dog": "後ろ斜めまたは真後ろへ1マス、または前へ何マスでも進めます。",
        "taikyoku_vertical_horse": "後ろへ1マス、または前斜めへ1マス。前へ何マスでも進めます。",
        "taikyoku_cannon_soldier": "後ろへ1マス。横は3マスまで、前斜めは5マスまで、前は7マスまで進めます。",
        "taikyoku_sword_soldier": "後ろまたは前斜めへ1マス。",
        "taikyoku_angle_hawk": "縦・横・斜めに何マスでも進み、さらに前へ2マス跳べます。",
        "taikyoku_flying_eagle": "縦・横・斜めに何マスでも進み、さらに前斜めへ2マス跳べます。",
        "taikyoku_spear_soldier": "後ろまたは横へ1マス、または前へ何マスでも進めます。",
        "taikyoku_vertical_leopard": "後ろ・横・前斜めへ1マス、または前へ何マスでも進めます。",
        "taikyoku_fierce_tiger": "前へ何マスでも進めます。",
        "taikyoku_archer": "後ろへ1マス。横と前斜めは3マスまで、前は5マスまで進めます。",
        "taikyoku_komainu": "縦・横・斜めに何マスでも進み、さらに全方向へ3マス跳べます。",
        "taikyoku_roaring_dog": "縦横と前斜めに何マスでも、後ろ斜めは3マスまで進めます。縦横と前斜めへ3マス跳べます。",
        "taikyoku_right_chariot": "右へ1マス。前へ何マスでも、前斜め左・後ろ斜め右へ何マスでも進めます。",
        "checker": "前斜めへ1マス。捕獲は敵駒を前斜めに1枚飛び越えます。キング後は後ろ斜めにも動けます。",
        "chaturanga_rook": "縦または横に何マスでも進めます。",
        "chaturanga_pawn": "前へ1マス。捕獲は前斜めです。",
        "chaturanga_knight": "縦横に2マスと1マスのL字に跳びます。途中の駒は飛び越せます。",
        "chaturanga_elephant": "斜めに2マス跳びます。",
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CROSSBOARD")
        self.root.minsize(880, 660)
        self.container = tk.Frame(root, padx=12, pady=12)
        self.container.pack(fill="both", expand=True)
        self.draft: DraftSession | None = None
        self.game: GameState | None = None
        self.selected: tuple[int, int] | None = None
        self.selected_hand: int | None = None
        self.inspected_piece_uid: int | None = None
        self.pictures_dir = Path(__file__).resolve().parent / "Pictures"
        if not self.pictures_dir.is_dir():
            self.pictures_dir = Path(r"C:\InterBoardGame\Pictures")
        self.piece_image_cache: dict[tuple[str, bool, int], object] = {}
        self.drag_wall_orientation: str | None = None
        self.drag_preview_edge = None
        self.root.bind_all("<B1-Motion>", self.wall_drag_motion)
        self.root.bind_all("<ButtonRelease-1>", self.wall_drag_release)
        self.setup_menu()

    def clear(self) -> None:
        for child in self.container.winfo_children():
            child.destroy()

    def setup_menu(self) -> None:
        self.clear()
        tk.Label(self.container, text="CROSSBOARD", font=("Segoe UI", 26, "bold")).pack(pady=30)
        tk.Label(self.container, text="10種類のゲーム由来の駒を使うローカル対戦").pack(pady=8)
        tk.Button(self.container, text="新しい対局", font=("Segoe UI", 16),
                  command=self.start_draft, width=20).pack(pady=20)
        tk.Label(self.container, text="設定値は crossboard.py の GameConfig で変更できます。",
                 fg="#555").pack()

    def start_draft(self) -> None:
        self.draft = DraftSession.new(config=GameConfig(size=9))
        self.show_draft()

    def show_draft(self) -> None:
        assert self.draft is not None
        self.clear()
        d = self.draft
        player = d.active
        tk.Label(self.container, text=f"駒ドラフト — {self.SIDE_NAMES[player]}側の選択",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        pick_summary = " / ".join(
            f"{self.SIDE_NAMES[i]}側: {len(d.rosters[i])}/10セット"
            for i in (0, 1)
        )
        tk.Label(
            self.container,
            text=f"残り候補: {len(d.cards)}/20セット　｜　{pick_summary}",
        ).pack(anchor="w", pady=(4, 6))
        draft_hint = (
            "白側と黒側が大将駒を1つずつ選んでください。"
            if not all(d.leader_selected)
            else "交互に1セットずつ取ります。候補がなくなると対局を開始します。"
        )
        tk.Label(self.container, text=draft_hint, fg="#555").pack(
            anchor="w", pady=(0, 8)
        )
        roster_summary = "　｜　".join(
            f"{self.SIDE_NAMES[i]}側: " + ("、".join(
                s.name + (f"×{s.quantity}" if s.quantity > 1 else "")
                for s in d.rosters[i]
            ) or "未選択")
            for i in (0, 1)
        )
        tk.Label(self.container, text=roster_summary, wraplength=840,
                 justify="left", fg="#444").pack(anchor="w", pady=(0, 8))

        body = tk.Frame(self.container)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        self.card_list = tk.Listbox(left, height=22, font=("Segoe UI", 10))
        self.card_list.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(left, command=self.card_list.yview)
        scroll.pack(side="right", fill="y")
        self.card_list.configure(yscrollcommand=scroll.set)
        self.visible_cards = []
        for card in d.available_cards():
            marker = "【大将】" if card.spec.general else ""
            qty = f" ×{card.spec.quantity}枚セット" if card.spec.quantity > 1 else ""
            label = f"{marker}{card.spec.name}{qty} [{card.spec.source}]"
            if card.spec.provisional:
                label += "  (仮仕様)"
            self.card_list.insert("end", label)
            self.visible_cards.append(card.card_id)
        self.card_list.bind("<<ListboxSelect>>", self.show_card_info)
        right = tk.Frame(body, padx=14)
        right.pack(side="left", fill="y")
        self.detail = tk.Label(right, text="候補を選択すると説明が表示されます",
                               wraplength=260, justify="left", anchor="nw")
        self.detail.pack(fill="x", pady=(0, 14))
        tk.Button(right, text="選択したセットを取る", command=self.choose_card).pack(fill="x", pady=3)

    def show_card_info(self, _event=None) -> None:
        if not self.card_list.curselection():
            return
        card = next(c for c in self.draft.cards
                    if c.card_id == self.visible_cards[self.card_list.curselection()[0]])
        s = card.spec
        desc = s.description or f"{s.source}由来。駒の種類: {s.kind}"
        if s.goal:
            desc += f"\n勝利条件: {s.goal}"
        self.detail.configure(text=f"{s.name}{'（大将駒）' if s.general else ''}\n"
                                   f"由来: {s.source}\nセット枚数: {s.quantity}枚\n{desc}")

    def choose_card(self) -> None:
        if not self.card_list.curselection():
            messagebox.showinfo("ドラフト", "取得する候補を選んでください")
            return
        card_id = self.visible_cards[self.card_list.curselection()[0]]
        try:
            self.draft.choose(card_id)
        except ValueError as exc:
            messagebox.showerror("選択できません", str(exc))
            return
        if self.draft.started:
            self.start_game()
        else:
            self.show_draft()

    def start_game(self) -> None:
        d = self.draft
        # Drafting second grants the first turn in the game.
        self.game = GameState(d.config, first_player=1 - d.starting_player)
        self.game.setup_rosters(d.rosters)
        self.selected = None
        self.selected_hand = None
        self.inspected_piece_uid = None
        self.drag_wall_orientation = None
        self.drag_preview_edge = None
        self.show_game()

    def show_game(self) -> None:
        assert self.game is not None
        self.clear()
        g = self.game
        screen_width = self.root.winfo_screenwidth()
        fixed_width = (
            self.HAND_TRAY_WIDTH * 2 + self.CONTROL_PANEL_WIDTH
            + 3 * 8 + 2 * 12
        )
        self.CELL = max(64, min(76, (screen_width - fixed_width) // g.size))
        extent = self.CELL * g.size

        left = tk.Frame(self.container)
        self.canvas = tk.Canvas(left, width=extent, height=extent,
                                highlightthickness=1, highlightbackground="#444")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.board_click)

        player2_side = tk.Frame(
            self.container, width=self.HAND_TRAY_WIDTH, height=extent
        )
        player2_side.pack(side="left", padx=(0, 8), fill="y")
        player2_side.pack_propagate(False)
        self._build_hand_tray(
            player2_side, owner=1, height=max(260, int(extent * 0.54)), anchor="bottom"
        )

        left.pack(side="left", padx=(0, 8))

        player1_side = tk.Frame(
            self.container, width=self.HAND_TRAY_WIDTH, height=extent
        )
        player1_side.pack(side="left", padx=(0, 8), fill="y")
        player1_side.pack_propagate(False)
        self._build_hand_tray(
            player1_side, owner=0, height=max(260, int(extent * 0.54)), anchor="top"
        )

        right = tk.Frame(
            self.container, width=self.CONTROL_PANEL_WIDTH, height=extent
        )
        right.pack(side="left", fill="y", expand=True)
        right.pack_propagate(False)
        tk.Label(right, text="CROSSBOARD", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        if g.result:
            result = "引き分け" if g.result.draw else f"{self.SIDE_NAMES[g.result.winner]}の勝ち"
            tk.Label(right, text=f"{result}\n{g.result.reason}",
                     font=("Segoe UI", 15, "bold"), fg="#a22").pack(anchor="w", pady=8)
        else:
            tk.Label(right, text=f"手番: {self.SIDE_NAMES[g.turn]}  /  手数: {g.turns}",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=6)
        tk.Button(right, text="選択解除", command=self.clear_selection).pack(anchor="w", pady=4)
        self._build_piece_info(right)
        tk.Label(right, text="コリドールの壁（マークを盤にドラッグ）").pack(
            anchor="w", pady=(8, 2)
        )
        wall_marks = tk.Frame(right)
        wall_marks.pack(fill="x")
        wall_count = g.wall_hands[g.turn]
        for orientation, label in (("horizontal", "横向き"), ("vertical", "縦向き")):
            marker = tk.Canvas(
                wall_marks,
                width=260,
                height=34,
                highlightthickness=1,
                highlightbackground="#aaa",
                cursor="hand2" if wall_count and not g.result else "arrow",
                state=tk.NORMAL if wall_count and not g.result else tk.DISABLED,
            )
            marker.pack(anchor="w", pady=1)
            if orientation == "horizontal":
                marker.create_line(12, 17, 48, 17, fill="#333", width=7)
            else:
                marker.create_line(30, 4, 30, 30, fill="#333", width=7)
            marker.create_text(62, 17, anchor="w", text=f"{label}の壁 ({wall_count})")
            marker.bind(
                "<ButtonPress-1>",
                lambda event, direction=orientation: self.start_wall_drag(direction),
            )
        tk.Label(right, text=f"壁の手持ち: 白 {g.wall_hands[0]}枚 / 黒 {g.wall_hands[1]}枚").pack(anchor="w")
        tk.Label(right, text="ログ", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 0))
        log = tk.Text(right, height=3, width=34, state="normal")
        log.pack(fill="both", expand=True)
        for event in g.events[-14:]:
            log.insert("end", event + "\n")
        log.configure(state="disabled")
        tk.Button(right, text="再戦", command=self.start_draft).pack(anchor="e", pady=8)
        self._update_piece_info()
        self.draw_board()

    def _build_hand_tray(
        self, parent, owner: int, height: int, anchor: str
    ) -> None:
        g = self.game
        tray = tk.LabelFrame(
            parent,
            text=f"{self.SIDE_NAMES[owner]}の持ち駒",
            width=self.HAND_TRAY_WIDTH,
            height=height,
            bg="#d9c18e",
            padx=3,
            pady=3,
        )
        tray.pack(side=anchor, fill="x", anchor="n" if anchor == "top" else "s")
        tray.pack_propagate(False)
        tray.rowconfigure(0, weight=1)
        tray.columnconfigure(0, weight=1)
        canvas = tk.Canvas(
            tray, bg="#d9c18e", highlightthickness=0,
            width=self.HAND_TRAY_WIDTH - 24, height=height - 30,
        )
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tray, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        contents = tk.Frame(canvas, bg="#d9c18e")
        window_id = canvas.create_window((0, 0), window=contents, anchor="nw")
        contents.bind(
            "<Configure>",
            lambda _event, target=canvas: target.configure(
                scrollregion=target.bbox("all")
            ),
        )
        canvas.bind(
            "<Configure>",
            lambda event, target=canvas, item=window_id: target.itemconfigure(
                item, width=event.width
            ),
        )

        groups = {}
        for index, piece in enumerate(g.hands[owner]):
            key = (
                piece.spec,
                piece.kind,
                piece.promoted,
                piece.base_kind,
                piece.promotion_kind,
            )
            groups.setdefault(key, []).append(index)

        for tile_index, indices in enumerate(groups.values()):
            piece = g.hands[owner][indices[0]]
            photo = self._piece_image(piece, size=self.HAND_IMAGE_SIZE)
            is_selected = owner == g.turn and self.selected_hand in indices
            border = "#45824a" if is_selected else "#a88d5a"
            tile = tk.Canvas(
                contents,
                width=self.HAND_TILE_SIZE,
                height=self.HAND_TILE_SIZE,
                bg="#e7d2a5",
                highlightthickness=3 if is_selected else 1,
                highlightbackground=border,
                highlightcolor=border,
            )
            if photo is not None:
                tile.create_image(
                    self.HAND_TILE_SIZE // 2,
                    self.HAND_TILE_SIZE // 2 - 3,
                    image=photo,
                )
            else:
                tile.create_text(
                    self.HAND_TILE_SIZE // 2,
                    self.HAND_TILE_SIZE // 2 - 3,
                    text="?",
                    font=("Segoe UI", 12, "bold"),
                )
            if len(indices) > 1:
                tile.create_rectangle(
                    self.HAND_TILE_SIZE - 29,
                    self.HAND_TILE_SIZE - 16,
                    self.HAND_TILE_SIZE - 2,
                    self.HAND_TILE_SIZE - 2,
                    fill="#f7ebd4",
                    outline="#a88d5a",
                )
                tile.create_text(
                    self.HAND_TILE_SIZE - 15,
                    self.HAND_TILE_SIZE - 9,
                    text=f"×{len(indices)}",
                    font=("Segoe UI", 8, "bold"),
                    fill="#493b25",
                )
            tile.bind(
                "<Button-1>",
                lambda _event, hand_index=indices[0], player=owner:
                    self.select_hand(hand_index, owner=player),
            )
            tile.grid(
                row=tile_index // 2,
                column=tile_index % 2,
                padx=2,
                pady=2,
                sticky="nsew",
            )

        wall_count = g.wall_hands[owner]
        if wall_count > 0:
            tile_index = len(groups)
            wall_tile = tk.Canvas(
                contents,
                width=self.HAND_TILE_SIZE,
                height=self.HAND_TILE_SIZE,
                bg="#e7d2a5",
                highlightthickness=1,
                highlightbackground="#a88d5a",
                cursor=(
                    "hand2"
                    if owner == g.turn and not g.result
                    else "arrow"
                ),
            )
            wall_color = "#4b2e1b"
            wall_tile.create_rectangle(
                13, 11, 45, 19, fill=wall_color, outline="#321b10", width=1
            )
            wall_tile.create_rectangle(
                25, 23, 33, 39, fill=wall_color, outline="#321b10", width=1
            )
            wall_tile.create_rectangle(
                self.HAND_TILE_SIZE - 29,
                self.HAND_TILE_SIZE - 16,
                self.HAND_TILE_SIZE - 2,
                self.HAND_TILE_SIZE - 2,
                fill="#f7ebd4",
                outline="#a88d5a",
            )
            wall_tile.create_text(
                self.HAND_TILE_SIZE - 15,
                self.HAND_TILE_SIZE - 9,
                text=f"×{wall_count}",
                font=("Segoe UI", 8, "bold"),
                fill="#493b25",
            )
            wall_tile.bind(
                "<ButtonPress-1>",
                lambda event, player=owner:
                    self.start_hand_wall_drag(event, player),
            )
            wall_tile.grid(
                row=tile_index // 2,
                column=tile_index % 2,
                padx=2,
                pady=2,
                sticky="nsew",
            )
        contents.columnconfigure(0, weight=1)
        contents.columnconfigure(1, weight=1)

    def _piece_image_path(self, piece) -> tuple[Path, bool] | None:
        owner = 0 if piece.owner == 0 else 1
        is_promoted_chess_pawn = piece.base_kind == "chess_pawn" and piece.promoted
        image_kind = piece.kind if is_promoted_chess_pawn else piece.spec.kind
        files = self.PIECE_IMAGE_FILES.get(image_kind)
        if files is None:
            return None
        if piece.promoted and not is_promoted_chess_pawn:
            files = self.PROMOTED_PIECE_IMAGE_FILES.get(piece.spec.kind, files)
        path = self.pictures_dir / files[owner]
        if not path.is_file():
            return None
        rotate = piece.spec.source in ("Shogi", "Taikyoku Shogi") and owner == 1
        return path, rotate

    def _piece_image(
        self,
        piece,
        size: int | None = None,
        orient_for_owner: bool = True,
    ):
        size = self.PIECE_IMAGE_SIZE if size is None else size
        image_info = self._piece_image_path(piece)
        if image_info is None:
            return None
        path, rotate = image_info
        if not orient_for_owner:
            rotate = False
        key = (str(path), rotate, size)
        if key in self.piece_image_cache:
            return self.piece_image_cache[key]

        try:
            if Image is not None and ImageTk is not None:
                with Image.open(path) as source:
                    image = source.convert("RGBA")
                resampling = getattr(Image, "Resampling", Image).LANCZOS
                image.thumbnail((size, size), resampling)
                if rotate:
                    image = image.rotate(180)
                photo = ImageTk.PhotoImage(image, master=self.canvas)
            else:
                photo = tk.PhotoImage(file=str(path), master=self.canvas)
                scale = max(
                    1,
                    (max(photo.width(), photo.height()) + size - 1)
                    // size,
                )
                if scale > 1:
                    photo = photo.subsample(scale, scale)
        except (OSError, tk.TclError, ValueError):
            return None

        self.piece_image_cache[key] = photo
        return photo

    def _build_piece_info(self, parent) -> None:
        self.piece_info = tk.LabelFrame(parent, text="駒の説明", padx=6, pady=4)
        self.piece_info.pack(fill="x", pady=(6, 2))
        summary = tk.Frame(self.piece_info)
        summary.pack(fill="x")
        self.piece_info_image = tk.Label(summary, width=66, height=66, relief="groove")
        self.piece_info_image.pack(side="left", padx=(0, 6))
        self.piece_info_name = tk.Label(
            summary, text="駒をクリックしてください", justify="left", anchor="w",
            wraplength=185, font=("Segoe UI", 10, "bold"),
        )
        self.piece_info_name.pack(side="left", fill="x", expand=True)
        self.piece_info_movement = tk.Label(
            self.piece_info, text="動き方：—", justify="left", anchor="w",
            wraplength=265, font=("Segoe UI", 9),
        )
        self.piece_info_movement.pack(fill="x", pady=(4, 0))
        self.piece_info_effect = tk.Label(
            self.piece_info, text="効果：—", justify="left", anchor="w",
            wraplength=265, font=("Segoe UI", 9),
        )
        self.piece_info_effect.pack(fill="x", pady=(2, 0))

    def _find_piece(self, uid: int):
        g = self.game
        if g is None:
            return None
        for piece in g.board.values():
            if piece.uid == uid:
                return piece
        for hand in g.hands:
            for piece in hand:
                if piece.uid == uid:
                    return piece
        return None

    def _piece_display_name(self, piece) -> str:
        g = self.game
        if piece.kind == "reversi":
            return "リバーシの駒"
        if piece.kind == "go_stone":
            return "囲碁の駒"
        if piece.promoted:
            promoted_name = g.promotion_target_name(piece)
            if promoted_name:
                return promoted_name
            if piece.kind == "checker":
                return "チェッカーキング"
        return piece.spec.name

    def _piece_effect_text(self, piece) -> str:
        effects = []
        if piece.general:
            effects.append("大将駒です。取られると敗北します。")
        if piece.spec.goal == "reach_far_rank":
            effects.append("相手側の最終段に到達すると勝利します。")
        elif piece.spec.goal == "reach_center":
            effects.append("盤の中央に到達すると勝利します。")
        if piece.spec.provisional and piece.spec.description:
            effects.append(f"暫定ルール：{piece.spec.description}")
        elif piece.spec.description:
            effects.append(piece.spec.description)

        if piece.kind not in ("reversi", "go_stone"):
            effects.append("敵駒を取ると、大将を除き自分の持ち駒になり、後で空きマスへ打てます。")
        if piece.kind == "chess_pawn":
            effects.append("最終段でクイーン・ビショップ・ナイト・ルークに昇格できます。アンパッサンがあり、打ったポーンは初手に2マス進めません。")
        elif piece.spec.source == "Shogi" and piece.kind != "shogi_king":
            effects.append("二歩は禁止です。歩・桂馬は行き所のない段に打てません。成れる駒は敵陣で成れます。")
        elif piece.kind == "chess_king":
            effects.append("条件を満たすとルークとキャスリングできます。")
        elif piece.kind == "checker":
            effects.append("飛び越えて取れるときは捕獲が必須です。連続捕獲は相手の手番後に続けます。")
        elif piece.kind == "reversi":
            effects.append("挟んだ敵駒を裏返します。挟まれる駒は種類不問、両端は味方のリバーシ駒に限ります。")
        elif piece.kind == "go_stone":
            effects.append("置いた石は動きません。呼吸点がなくなる手はできません（相手を取る場合を除く）。")
        if piece.promoted and piece.spec.source == "Shogi":
            effects.append("成駒です。取られると元の駒の種類に戻ります。")
        return "\n".join(effects) if effects else "追加効果はありません。"

    def _piece_movement_text(self, piece) -> str:
        if piece.spec.source == "Taikyoku Shogi" and piece.spec.provisional:
            return piece.spec.description or "暫定ルールで移動します。"
        return self.PIECE_MOVEMENT_TEXT.get(
            piece.kind, "移動方法の説明はありません。"
        )

    def _update_piece_info(self) -> None:
        piece = (
            self._find_piece(self.inspected_piece_uid)
            if self.inspected_piece_uid is not None else None
        )
        if piece is None:
            self.piece_info_image.configure(image="", text="")
            self.piece_info_image.image = None
            self.piece_info_name.configure(text="駒をクリックしてください")
            self.piece_info_movement.configure(text="動き方：—")
            self.piece_info_effect.configure(text="効果：—")
            return

        image = self._piece_image(piece, size=66, orient_for_owner=False)
        self.piece_info_image.configure(
            image=image or "", text="" if image else "画像なし",
        )
        self.piece_info_image.image = image
        title = f"{self._piece_display_name(piece)}"
        if piece.general:
            title += "（大将）"
        self.piece_info_name.configure(
            text=(
                f"{title}\nゲームの種類：{self.PIECE_SOURCE_NAMES.get(piece.spec.source, piece.spec.source)}"
            )
        )
        movement = self._piece_movement_text(piece)
        self.piece_info_movement.configure(text=f"動き方：{movement}")
        self.piece_info_effect.configure(text=f"効果：{self._piece_effect_text(piece)}")

    def draw_board(self) -> None:
        g = self.game
        self.canvas.delete("all")
        moves = []
        move_targets = set()
        if self.selected and self.selected in g.board and not g.result:
            moves = g.legal_moves(self.selected)
            move_targets = {move.target for move in moves}
        drop_targets = set()
        highlight_all = False
        if self.selected_hand is not None and not g.result:
            if 0 <= self.selected_hand < len(g.hands[g.turn]):
                selected_piece = g.hands[g.turn][self.selected_hand]
                if selected_piece.kind == "go_stone":
                    drop_targets = set(g.legal_drops(self.selected_hand))
                elif selected_piece.kind == "reversi":
                    if g.is_in_check(g.turn):
                        drop_targets = set(g.legal_drops(self.selected_hand))
                    else:
                        highlight_all = True
                else:
                    drop_targets = set(g.legal_drops(self.selected_hand))
        for y in range(g.size):
            for x in range(g.size):
                x0, y0 = x*self.CELL, y*self.CELL
                piece=g.board.get((x,y))
                is_general = bool(piece and piece.general)
                color = "#efc6c6" if is_general else (
                    "#e6ce9e" if (x+y)%2==0 else "#d4b984"
                )
                outline = "#c77c7c" if is_general else "#806942"
                self.canvas.create_rectangle(x0,y0,x0+self.CELL,y0+self.CELL,
                                             fill=color,outline=outline)
                if ((highlight_all and piece is None)
                        or (x, y) in move_targets or (x, y) in drop_targets):
                    self.canvas.create_rectangle(
                        x0+2, y0+2, x0+self.CELL-2, y0+self.CELL-2,
                        fill="#9bd49b", outline="#63a76b", width=2,
                    )
                if is_general:
                    self.canvas.create_rectangle(
                        x0+1, y0+1, x0+self.CELL-1, y0+self.CELL-1,
                        fill="", outline="#bd4c4c", width=3,
                    )
                if piece:
                    image = self._piece_image(piece)
                    if image is not None:
                        self.canvas.create_image(
                            x0 + self.CELL / 2, y0 + self.CELL / 2, image=image
                        )
                    else:
                        fill=self.COLORS[piece.owner]
                        self.canvas.create_oval(x0+7,y0+7,x0+self.CELL-7,y0+self.CELL-7,
                                                fill=fill,outline="#222",width=2)
                        promotion_name=g.promotion_target_name(piece)
                        label="太子" if piece.taishi else (
                            promotion_name[:2] if piece.promoted and promotion_name
                            else piece.spec.name[:2]
                        )
                        if piece.promoted and not promotion_name:
                            label="成"+label[:1]
                        self.canvas.create_text(x0+self.CELL/2,y0+self.CELL/2,text=label,
                                                fill="white",font=("Segoe UI",10,"bold"))
                if self.selected==(x,y):
                    self.canvas.create_rectangle(x0+2,y0+2,x0+self.CELL-2,y0+self.CELL-2,
                                                 outline="#17a34a",width=3)
        for wall in g.walls:
            self.canvas.create_line(
                *self._wall_pixel_segment(wall),
                fill="#333",
                width=8,
                capstyle="butt",
            )
        if self.drag_preview_edge:
            preview_color = (
                "#22863a"
                if self.drag_preview_edge in g.legal_wall_edges(g.turn)
                else "#d12f2f"
            )
            self.canvas.create_line(
                *self._wall_pixel_segment(self.drag_preview_edge),
                fill=preview_color,
                width=9,
                capstyle="butt",
            )

    def _choose_chess_promotion(self) -> str | None:
        dialog = tk.Toplevel(self.root)
        dialog.title("ポーンの昇格先")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        selected = {"kind": None}

        tk.Label(dialog, text="昇格する駒を選んでください").grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 8)
        )
        for index, (name, kind) in enumerate(self.CHESS_PROMOTION_OPTIONS):
            tk.Button(
                dialog,
                text=name,
                width=14,
                command=lambda choice=kind: (selected.update(kind=choice), dialog.destroy()),
            ).grid(row=1 + index // 2, column=index % 2, padx=6, pady=6)
        tk.Button(dialog, text="キャンセル", command=dialog.destroy).grid(
            row=3, column=0, columnspan=2, pady=(4, 12)
        )
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.grab_set()
        dialog.focus_set()
        self.root.wait_window(dialog)
        return selected["kind"]

    def board_click(self, event) -> None:
        g=self.game
        pos=(event.x//self.CELL,event.y//self.CELL)
        if not g.in_bounds(pos): return
        if g.result:
            piece = g.board.get(pos)
            self.inspected_piece_uid = piece.uid if piece else None
            self.selected = None
            self.selected_hand = None
            self.show_game()
            return
        if self.selected_hand is not None:
            piece_on_square = g.board.get(pos)
            if piece_on_square is not None:
                self.selected_hand = None
                self.inspected_piece_uid = piece_on_square.uid
                forced_pos = next(
                    (square for square, piece in g.board.items()
                     if g.forced_checker is not None
                     and piece.uid == g.forced_checker),
                    None,
                )
                self.selected = forced_pos or (
                    pos if piece_on_square.owner == g.turn else None
                )
                self.show_game()
                return
            held_piece = g.hands[g.turn][self.selected_hand]
            try:
                g.apply_drop(self.selected_hand,pos)
            except ValueError as exc:
                messagebox.showinfo("配置できません",str(exc))
                self.show_game()
                return
            self.selected_hand=None
            self.inspected_piece_uid = held_piece.uid
            self.show_game()
            return
        if self.selected:
            moves=g.legal_moves(self.selected)
            move=next((m for m in moves if m.target==pos),None)
            if move:
                moving_piece_uid = g.board[move.origin].uid
                try:
                    promote=False
                    promotion_kind=None
                    if g.can_promote(move):
                        piece=g.board[move.origin]
                        if (piece.base_kind or piece.spec.kind) == "chess_pawn":
                            promotion_kind=self._choose_chess_promotion()
                            if promotion_kind is None:
                                return
                        else:
                            target_name=g.promotion_target_name(piece)
                            suffix=f"（成ると{target_name}）" if target_name else ""
                            promote=messagebox.askyesno(
                                "成りの選択",
                                f"{piece.spec.name}{suffix}。成りますか？",
                            )
                    g.apply_move(move,promote=promote,promotion_kind=promotion_kind)
                except ValueError as exc:
                    messagebox.showinfo("移動できません",str(exc))
                self.selected = next(
                    (square for square, piece in g.board.items()
                     if g.forced_checker is not None
                     and piece.uid == g.forced_checker),
                    None,
                )
                self.inspected_piece_uid = moving_piece_uid
                self.show_game()
                return
        piece=g.board.get(pos)
        self.inspected_piece_uid = piece.uid if piece else None
        forced_pos = next(
            (square for square, board_piece in g.board.items()
             if g.forced_checker is not None
             and board_piece.uid == g.forced_checker),
            None,
        )
        if forced_pos is not None:
            self.selected = forced_pos
        elif piece and piece.owner==g.turn:
            self.selected=pos
        else:
            self.selected=None
        self.show_game()

    def select_hand(self, hand_index: int, owner: int | None = None) -> None:
        g = self.game
        if owner is None:
            owner = g.turn
        if not 0 <= hand_index < len(g.hands[owner]):
            return

        self.inspected_piece_uid = g.hands[owner][hand_index].uid
        if owner != g.turn:
            self.show_game()
            return
        if not self._can_select_hand(hand_index):
            self.selected_hand = None
            self.selected = None
            self.show_game()
            return
        self.selected_hand = hand_index
        self.selected = None
        self.drag_wall_orientation = None
        self.drag_preview_edge = None
        self.show_game()

    def _can_select_hand(self, hand_index: int) -> bool:
        g = self.game
        return (
            not g.result
            and 0 <= hand_index < len(g.hands[g.turn])
            and (not g.is_in_check(g.turn) or bool(g.legal_drops(hand_index)))
        )

    def select_reserve_kind(self, kind: str) -> None:
        if self.game.result:
            return
        hand=self.game.hands[self.game.turn]
        hand_index = next(
            (idx for idx, piece in enumerate(hand) if piece.kind == kind),
            None,
        )
        if hand_index is not None:
            self.inspected_piece_uid = hand[hand_index].uid
        current_kind=(hand[self.selected_hand].kind
                      if self.selected_hand is not None
                      and 0 <= self.selected_hand < len(hand) else None)
        if current_kind == kind:
            self.selected_hand=None
        elif hand_index is None or not self._can_select_hand(hand_index):
            self.selected_hand = None
        else:
            self.selected_hand = hand_index
        self.selected = None
        self.drag_wall_orientation = None
        self.drag_preview_edge = None
        self.show_game()

    def clear_selection(self) -> None:
        self.selected=None; self.selected_hand=None
        self.inspected_piece_uid=None
        self.drag_wall_orientation = None; self.drag_preview_edge = None
        self.show_game()

    @staticmethod
    def _wall_orientation(wall) -> str:
        return wall[0]

    def _wall_pixel_segment(self, wall) -> tuple[float, float, float, float]:
        orientation, x, y = wall
        inset = max(3, self.CELL * 0.06)
        if orientation == "horizontal":
            return (
                x*self.CELL + inset, (y+1)*self.CELL,
                (x+2)*self.CELL - inset, (y+1)*self.CELL,
            )
        return (
            (x+1)*self.CELL, y*self.CELL + inset,
            (x+1)*self.CELL, (y+2)*self.CELL - inset,
        )

    def start_wall_drag(self, orientation: str) -> None:
        if self.game.result or self.game.wall_hands[self.game.turn] <= 0:
            return
        self.selected = None
        self.selected_hand = None
        self.drag_wall_orientation = orientation
        self.drag_preview_edge = None
        self.draw_board()

    def start_hand_wall_drag(self, event, owner: int) -> str:
        if owner != self.game.turn or self.game.result:
            return "break"
        if 11 <= event.y <= 20:
            orientation = "horizontal"
        elif 22 <= event.y <= 40:
            orientation = "vertical"
        else:
            orientation = (
                "horizontal"
                if event.x < self.HAND_TILE_SIZE // 2
                else "vertical"
            )
        self.start_wall_drag(orientation)
        return "break"

    def _nearest_wall_edge(self, x: float, y: float, orientation: str):
        candidates = [
            (orientation, anchor_x, anchor_y)
            for anchor_y in range(self.game.size - 1)
            for anchor_x in range(self.game.size - 1)
        ]
        if not candidates:
            return None

        def distance_squared(wall) -> float:
            _orientation, anchor_x, anchor_y = wall
            midpoint_x = (anchor_x + 1) * self.CELL
            midpoint_y = (anchor_y + 1) * self.CELL
            return (x-midpoint_x) ** 2 + (y-midpoint_y) ** 2

        nearest = min(candidates, key=distance_squared)
        if distance_squared(nearest) > (self.CELL * 0.75) ** 2:
            return None
        return nearest

    def wall_drag_motion(self, event) -> None:
        if self.drag_wall_orientation is None or not hasattr(self, "canvas"):
            return
        x = event.x_root - self.canvas.winfo_rootx()
        y = event.y_root - self.canvas.winfo_rooty()
        if not (0 <= x < self.CELL*self.game.size and 0 <= y < self.CELL*self.game.size):
            edge = None
        else:
            edge = self._nearest_wall_edge(x, y, self.drag_wall_orientation)
        if edge != self.drag_preview_edge:
            self.drag_preview_edge = edge
            self.draw_board()

    def wall_drag_release(self, event) -> None:
        if self.drag_wall_orientation is None or not hasattr(self, "canvas"):
            return
        x = event.x_root - self.canvas.winfo_rootx()
        y = event.y_root - self.canvas.winfo_rooty()
        orientation = self.drag_wall_orientation
        self.drag_wall_orientation = None
        self.drag_preview_edge = None
        if 0 <= x < self.CELL*self.game.size and 0 <= y < self.CELL*self.game.size:
            wall_edge = self._nearest_wall_edge(x, y, orientation)
            if wall_edge is not None:
                try:
                    self.game.place_wall(wall_edge)
                except ValueError as exc:
                    messagebox.showinfo("壁", str(exc))
            else:
                messagebox.showinfo("壁", "この位置にはその向きの壁を置けません")
        self.show_game()


def run_gui() -> None:
    root=tk.Tk()
    CrossboardUI(root)
    root.mainloop()
