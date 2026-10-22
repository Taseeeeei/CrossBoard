import unittest

from crossboard import (
    DraftCard, DraftSession, GameConfig, GameState, LEADERS, NORMAL_LOTS, Move, PieceSpec,
    sample_draft_pool,
)


def spec(name, kind, source="Chess", cost=1, quantity=1, general=False, goal=""):
    return PieceSpec(name, source, kind, cost, quantity, general, goal)


class DraftTests(unittest.TestCase):
    def test_pool_has_thirty_cards_and_two_general_cards(self):
        pool = sample_draft_pool(7)
        self.assertEqual(30, len(pool))
        self.assertEqual(2, sum(card.spec.general for card in pool))
        self.assertEqual(10, len({s.source for s in NORMAL_LOTS}))

    def test_budget_and_second_general_are_rejected(self):
        draft = DraftSession.new(seed=4, config=GameConfig(budget=20))
        leaders = [c for c in draft.cards if c.spec.general]
        chosen = leaders[0]
        draft.active = 0
        draft.choose(chosen.card_id)
        draft.active = 0
        remaining = next(c for c in draft.cards if c.spec.general)
        with self.assertRaises(ValueError):
            draft.choose(remaining.card_id)
        expensive = PieceSpec("高価駒", "Chess", "chess_queen", 99)
        draft.cards.append(type(remaining)("extra", expensive))
        with self.assertRaises(ValueError):
            draft.choose("extra")

    def test_draft_reserves_points_for_a_leader(self):
        leader = next(s for s in LEADERS if s.kind == "shogi_king")
        costly = PieceSpec("高価駒", "Chess", "chess_queen", 15)
        draft = DraftSession(
            [DraftCard("leader", leader), DraftCard("costly", costly)],
            GameConfig(budget=20),
        )
        with self.assertRaises(ValueError):
            draft.choose("costly")

    def test_each_player_must_take_a_leader_and_settings_rights(self):
        draft = DraftSession.new(seed=8)
        for player in (0, 1):
            draft.active = player
            leader = next(c for c in draft.cards if c.spec.general)
            draft.choose(leader.card_id)
        draft.active = 0
        draft.claim_size_right(7)
        draft.active = 1
        draft.claim_first_right()
        draft.ready = [True, True]
        draft.finish()
        self.assertTrue(draft.started)


class MovementTests(unittest.TestCase):
    def setUp(self):
        self.game = GameState(GameConfig(size=7, budget=20))
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))

    def test_chess_knight_jumps_piece_and_wall(self):
        knight = self.game.add_piece(spec("ナイト", "chess_knight"), 0, (1, 1))
        self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (2, 1))
        self.game.walls.add(frozenset(((1, 1), (2, 1))))
        self.assertIn((3, 2), [m.target for m in self.game.legal_moves((1, 1))])

    def test_illegal_move_is_rejected(self):
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 0))
        with self.assertRaises(ValueError):
            self.game.apply_move(Move((0, 0), (1, 1)))

    def test_capture_sends_nonleader_to_hand(self):
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 0))
        self.game.add_piece(spec("ビショップ", "chess_bishop"), 1, (0, 3))
        move = next(m for m in self.game.legal_moves((0, 0)) if m.target == (0, 3))
        self.game.apply_move(move)
        self.assertEqual(1, len(self.game.hands[0]))
        self.assertEqual("chess_bishop", self.game.hands[0][0].kind)

    def test_drop_consumes_the_turn(self):
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 0))
        self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (0, 3))
        self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (1, 1))
        move = next(m for m in self.game.legal_moves((0, 0)) if m.target == (0, 3))
        self.game.apply_move(move)
        self.assertEqual(1, self.game.turn)
        with self.assertRaises(ValueError):
            self.game.apply_drop(0, (2, 2))
        reply = next(m for m in self.game.legal_moves((1, 1)) if m.target == (1, 2))
        self.game.apply_move(reply)
        self.game.apply_drop(0, (2, 2))
        self.assertEqual(1, self.game.turn)
        with self.assertRaises(ValueError):
            self.game.apply_drop(0, (3, 3))

    def test_captured_promoted_chess_pawn_returns_as_pawn(self):
        pawn = self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (3, 3))
        pawn.promoted = True
        pawn.moved = True
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (3, 0))
        move = next(m for m in self.game.legal_moves((3, 0)) if m.target == (3, 3))
        self.game.apply_move(move)
        self.assertEqual("chess_pawn", self.game.hands[0][0].kind)

    def test_nifu_for_shogi_pawn_drop(self):
        pawn = spec("歩", "shogi_pawn", "Shogi")
        self.game.add_piece(pawn, 0, (2, 4))
        self.game.hands[0].append(self.game.make_piece(pawn, 0))
        self.assertNotIn((2, 3), self.game.legal_drops(0))
        self.assertIn((3, 3), self.game.legal_drops(0))

    def test_castling_moves_king_and_rook_as_one_action(self):
        game = GameState(GameConfig(size=8, budget=20))
        king = next(s for s in LEADERS if s.kind == "chess_king")
        enemy = next(s for s in LEADERS if s.kind == "shogi_king")
        game.add_piece(king, 0, (4, 7))
        game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 7))
        game.add_piece(enemy, 1, (7, 0))
        castle = next(m for m in game.legal_moves((4, 7))
                      if m.special == "castle" and m.target == (2, 7))
        game.apply_move(castle)
        self.assertEqual("chess_king", game.board[(2, 7)].kind)
        self.assertEqual("chess_rook", game.board[(3, 7)].kind)

    def test_checker_capture_is_mandatory(self):
        self.game.add_piece(spec("チェッカー駒", "checker", "Checkers"), 0, (2, 4))
        self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (3, 3))
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 0))
        self.assertEqual([], self.game.legal_moves((0, 0)))
        captures = self.game.legal_moves((2, 4))
        self.assertTrue(any(m.special == "checker_capture" and m.target == (4, 2)
                            for m in captures))

    def test_xiangqi_general_stays_inside_palace(self):
        game = GameState(GameConfig(size=7, budget=20))
        general = next(s for s in LEADERS if s.kind == "xiangqi_general")
        enemy = next(s for s in LEADERS if s.kind == "shogi_king")
        game.add_piece(general, 0, (3, 5))
        game.add_piece(enemy, 1, (6, 0))
        targets = [m.target for m in game.legal_moves((3, 5))]
        self.assertTrue(targets)
        self.assertTrue(all(2 <= x <= 4 and 4 <= y <= 6 for x, y in targets))

    def test_xiangqi_horse_is_blocked_by_its_leg_square(self):
        self.game.add_piece(spec("馬", "xiangqi_horse", "Xiangqi"), 0, (2, 2))
        self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (3, 2))
        targets = {m.target for m in self.game.legal_moves((2, 2))}
        self.assertNotIn((4, 3), targets)
        self.assertIn((0, 3), targets)

    def test_shogi_rook_promotes_to_dragon_movement(self):
        rook = self.game.add_piece(spec("飛車", "shogi_rook", "Shogi"), 0, (3, 3))
        rook.promoted = True
        targets = {m.target for m in self.game.legal_moves((3, 3))}
        self.assertIn((4, 4), targets)
        self.assertIn((3, 0), targets)


class SpecialRuleTests(unittest.TestCase):
    def setUp(self):
        self.game = GameState(GameConfig(size=7, budget=20))

    def test_capturing_general_ends_game(self):
        rook = spec("ルーク", "chess_rook")
        king = next(s for s in LEADERS if s.kind == "chess_king")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(rook, 0, (0, 0))
        self.game.add_piece(king, 1, (0, 3))
        move = next(m for m in self.game.legal_moves((0, 0)) if m.target == (0, 3))
        self.game.apply_move(move)
        self.assertEqual(0, self.game.result.winner)
        with self.assertRaises(ValueError):
            self.game.apply_drop(0, (3, 3))

    def test_slipe_player_can_win_by_capturing_other_general(self):
        slipe = next(s for s in LEADERS if s.kind == "slipe_king")
        chess = next(s for s in LEADERS if s.kind == "chess_king")
        self.game.add_piece(slipe, 0, (6, 6))
        self.game.add_piece(chess, 1, (0, 3))
        self.game.add_piece(spec("車", "xiangqi_rook", "Xiangqi"), 0, (0, 0))
        move = next(m for m in self.game.legal_moves((0, 0)) if m.target == (0, 3))
        self.game.apply_move(move)
        self.assertEqual(0, self.game.result.winner)

    def test_taishi_protects_captured_general(self):
        rook = spec("ルーク", "chess_rook")
        king = next(s for s in LEADERS if s.kind == "chess_king")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(rook, 0, (0, 0))
        self.game.add_piece(king, 1, (0, 3))
        self.game.add_piece(spec("太子", "taishi", "Taikyoku Shogi"), 1, (4, 4))
        move = next(m for m in self.game.legal_moves((0, 0)) if m.target == (0, 3))
        self.game.apply_move(move)
        self.assertIsNone(self.game.result)
        self.assertEqual(1, self.game.turn)

    def test_reversi_flips_multiple_rays(self):
        reversi = spec("リバーシ駒", "reversi", "Othello")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(reversi, 0, (2, 3))
        self.game.add_piece(reversi, 1, (4, 3))
        self.game.add_piece(reversi, 0, (5, 3))
        self.game.add_piece(reversi, 1, (3, 2))
        self.game.add_piece(reversi, 0, (3, 1))
        move = next(m for m in self.game.legal_moves((2, 3)) if m.target == (3, 3))
        self.game.apply_move(move)
        self.assertEqual(0, self.game.board[(4, 3)].owner)
        self.assertEqual(0, self.game.board[(3, 2)].owner)

    def test_reversi_cannot_move_without_bracketing_a_piece(self):
        reversi = spec("リバーシ駒", "reversi", "Othello")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(reversi, 0, (2, 3))
        self.assertNotIn((3, 3), {m.target for m in self.game.legal_moves((2, 3))})

    def test_reversi_flip_of_a_general_ends_the_game(self):
        reversi = spec("リバーシ駒", "reversi", "Othello")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        king = next(s for s in LEADERS if s.kind == "chess_king")
        self.game.add_piece(king, 1, (4, 3))
        self.game.add_piece(reversi, 0, (2, 3))
        self.game.add_piece(reversi, 0, (5, 3))
        move = next(m for m in self.game.legal_moves((2, 3)) if m.target == (3, 3))
        self.game.apply_move(move)
        self.assertEqual(0, self.game.result.winner)
        with self.assertRaises(ValueError):
            self.game.apply_move(move)

    def test_go_self_atari_is_rejected_when_configured(self):
        self.game = GameState(GameConfig(size=7, budget=20, prohibit_self_atari=True))
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        for q in ((2,3),(4,3),(3,2),(3,4)):
            self.game.add_piece(spec("駒", "chess_pawn"), 1, q)
        stone = spec("囲碁石", "go_stone", "Go")
        self.game.hands[0].append(self.game.make_piece(stone, 0))
        self.assertNotIn((3,3), self.game.legal_drops(0))
        with self.assertRaises(ValueError):
            self.game.apply_drop(0, (3,3))

    def test_go_group_and_non_go_occupants_close_liberties(self):
        stone = spec("囲碁石", "go_stone", "Go")
        blocker = spec("ブロッカー", "chess_pawn")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(stone, 1, (3, 3))
        for q in ((2,3),(4,3),(3,2),(3,4)):
            self.game.add_piece(blocker, 0, q)
        groups = self.game._go_groups()
        self.assertEqual(1, len(groups))
        self.assertEqual(set(), self.game.go_liberties(groups[0]))
        # A successful move runs the board-wide Go capture check.
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 0))
        move = next(m for m in self.game.legal_moves((0,0)) if m.target == (1,0))
        self.game.apply_move(move)
        self.assertNotIn((3,3), self.game.board)
        self.assertTrue(any(p.kind == "go_stone" for p in self.game.hands[0]))

    def test_non_go_piece_does_not_join_go_group(self):
        stone = spec("囲碁石", "go_stone", "Go")
        ordinary = spec("歩兵", "chess_pawn")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(stone, 0, (3, 3))
        self.game.add_piece(stone, 0, (4, 3))
        self.game.add_piece(ordinary, 0, (3, 4))
        groups = self.game._go_groups()
        self.assertEqual(1, len(groups))
        self.assertEqual({(3, 3), (4, 3)}, groups[0])
        self.assertNotIn((3, 4), groups[0])

    def test_slipe_slides_to_blocker_and_wins_at_center(self):
        leader = next(s for s in LEADERS if s.kind == "slipe_king")
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(leader, 0, (3, 5))
        self.game.add_piece(spec("歩兵", "chess_pawn"), 1, (3, 2))
        move = next(m for m in self.game.legal_moves((3,5)) if m.target == (3,3))
        self.game.apply_move(move)
        self.assertEqual(0, self.game.result.winner)
        self.assertEqual("reach_center", leader.goal)

    def test_wall_is_an_edge_and_can_be_crossed_by_leaper(self):
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(spec("ナイト", "chess_knight"), 0, (1,1))
        barrier=frozenset(((1,1),(2,1)))
        self.game.walls.add(barrier)
        self.assertNotIn((2,1), self.game.board)
        targets={m.target for m in self.game.legal_moves((1,1))}
        self.assertIn((3,2), targets)

    def test_en_passant(self):
        p0=spec("歩兵","chess_pawn")
        p1=spec("歩兵","chess_pawn")
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(p0,0,(2,5))
        self.game.add_piece(p1,1,(3,3))
        double=next(m for m in self.game.legal_moves((2,5)) if m.target==(2,3))
        self.game.apply_move(double)
        ep=next(m for m in self.game.legal_moves((3,3)) if m.special=="en_passant")
        self.game.apply_move(ep)
        self.assertNotIn((2,3),self.game.board)
        self.assertEqual("chess_pawn",self.game.board[(2,4)].kind)

    def test_turn_limit_is_a_configurable_draw(self):
        self.game = GameState(GameConfig(size=7, budget=20, max_turns=1))
        self.game.add_piece(LEADERS[0], 0, (6, 6))
        self.game.add_piece(LEADERS[1], 1, (6, 0))
        self.game.add_piece(spec("ルーク", "chess_rook"), 0, (0, 0))
        move = next(m for m in self.game.legal_moves((0,0)) if m.target == (1,0))
        self.game.apply_move(move)
        self.assertTrue(self.game.result.draw)


if __name__ == "__main__":
    unittest.main()
