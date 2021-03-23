"""Agent."""
import random


class Action:
    def __init__(self, player, target, roll):
        self.player = player
        self.target = target
        self.roll = roll

    def __repr__(self):
        return f"Player {self.player} acts on {self.target} with {self.roll}"


class Agent:
    def __init__(self, player_idx):
        self.player_idx = player_idx

    def choose_action(self, board, roll, depart_roll):
        raise Exception("Not implemeted error.")


class RandomAgent(Agent):
    """実行できるものの中からランダムに実行する."""

    def choose_action(self, board, roll, depart_roll):
        choices = []
        # positionを追加
        choices += board.search_by_player(self.player_idx)

        # goalのうち、もう動かせないものを除外して残りを追加
        goals = board.goals[self.player_idx]
        temp = board.n_pieces
        while True:
            if temp in goals:
                goals.remove(temp)
                temp -= 1
            else:
                break

        choices += goals
        if (roll == depart_roll and board) and board.starts[self.player_idx] > 0:
            choices.append("depart")

        if not choices:
            # パス
            return None
        chosen_target = random.choice(choices)
        return Action(player=self.player_idx, target=chosen_target, roll=roll)


class SimpleLogicAgent(Agent):
    """以下の優先順位で実行する.

    :6がでてスタートできるならスタートさせる
    :相手を踏めるなら踏む.
    :ゴールできるならゴールする.
    :公道にいるのをランダムに進める
    :ゴールにいて進めるものがあるなら進める
    """

    def choose_action(self, board, roll, depart_roll):
        # 6がでてスタートできるならスタートさせる
        if (roll == depart_roll) and (board.starts[self.player_idx] > 0):
            return Action(player=self.player_idx, target="depart", roll=roll)

        # 相手を踏めるなら踏む
        my_pieces = board.search_by_player(self.player_idx)
        for piece in my_pieces:
            searched = board.search_by_coordinate(
                (piece.coordinate+roll) % board.len_total)
            for target in searched:
                if target.player != self.player_idx:
                    # 踏める相手がいる
                    return Action(player=self.player_idx, target=piece, roll=roll)

        # ゴールできるならゴールする.
        goal_entrance_coor = (
            board.len_total + self.player_idx*board.len_myway-1) % board.len_total
        for piece in my_pieces:
            if piece.coordinate+roll > goal_entrance_coor:
                return Action(player=self.player_idx, target=piece, roll=roll)

        # 公道にいるのをランダムに進める
        if my_pieces:
            return Action(player=self.player_idx, target=random.choice(my_pieces), roll=roll)

        # goalのうち、もう動かせないものを除外して残りのコマをランダムに選んで動かす
        goals = board.goals[self.player_idx]
        temp = board.n_pieces
        while True:
            if temp in goals:
                goals.remove(temp)
                temp -= 1
            else:
                break
        if goals:
            return Action(player=self.player_idx, target=random.choice(goals), roll=roll)

        # 全て該当しない場合はパスする
        return None
