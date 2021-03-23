import random


class Position:
    def __init__(self, coordinate, player):
        self.coordinate = coordinate
        self.player = player

    def __repr__(self):
        return f"Player{self.player}@{self.coordinate}"


class Board:
    def __init__(self, n_pieces, n_players, len_myway):
        self.starts = [n_pieces for _ in range(n_players)]
        self.positions = []
        self.goals = [[] for _ in range(n_players)]
        self.len_myway = len_myway
        self.len_total = len_myway*n_players
        self.n_pieces = n_pieces
        self.n_players = n_players

    def depart(self, player):
        if self.starts[player] <= 0:
            raise Exception(f"No piece remain in respawn of player {player}")
        self.starts[player] -= 1
        self.positions.append(self.create(player, 0))

    def respawn(self, position):
        self.positions.remove(position)
        self.starts[position.player] += 1

    def create(self, player, step):
        return Position(self.len_myway * player+step, player)

    def move(self, coordinate, step):
        searched_pos_list = self.search_by_coordinate(coordinate)
        if not searched_pos_list:
            raise Exception(
                f"Specified coordinate {coordinate} does not exist.")

        position = searched_pos_list[0]
        temp_coordinate = position.coordinate+step
        goal_coordinate = position.player*self.len_myway
        goal_coordinate = goal_coordinate if goal_coordinate > 0 else self.len_total

        if position.coordinate < goal_coordinate <= temp_coordinate:
            # ゴールゾーンにはいる
            available_goals = set(range(self.n_pieces)) - \
                set(self.goals[position.player])
            cands = [
                goal for goal in available_goals if temp_coordinate-goal_coordinate >= goal]
            if cands:
                dest = max(cands)
                self.goals[position.player].append(dest)
            else:
                print("Cannot enter goals.")
                return
        else:
            # publicゾーンを移動
            new_coordinate = temp_coordinate % self.len_total
            result = self.search_by_coordinate(new_coordinate)
            if result and result[0].player != position.player:
                # 衝突
                for opponent in result:
                    self.respawn(opponent)

            new_position = Position(new_coordinate, position.player)
            self.positions.append(new_position)

        # 前のを削除
        self.positions.remove(position)

    def search_by_coordinate(self, coordinate):
        result = []
        for position in self.positions:
            if position.coordinate == coordinate:
                result.append(position)
        return result

    def search_by_player(self, player):
        return [position for position in self.positions if position.player == player]

    def move_piece_in_goal(self, position, player, roll):
        if position not in self.goals[player]:
            raise Exception(
                f"{position} does not exist in Player {player}'s goal.")

        available_goals = set(range(self.n_pieces))-set(self.goals[player])
        cands = [goal for goal in available_goals if position+roll >= goal]
        if cands:
            dest = max(cands)
            self.goals[player].append(dest)
            self.goals[player].remove(position)

    def print_board(self):
        a = [["" for i in range(self.len_myway + 1)]
             for j in range(self.len_myway + 1)]

        # public
        for coordinate in range(self.len_total):
            i, j = self.coordinate2ij(coordinate)
            a[i][j] = "x"

        # piece表示
        for position in self.positions:
            i, j = self.coordinate2ij(position.coordinate)
            if a[i][j] == "x":
                a[i][j] = str(position.player)
            else:
                a[i][j] += str(position.player)

        # goal
        for player in range(self.n_players):
            for goal_idx in range(self.n_pieces):
                i, j = self.goal2ij(player, goal_idx)
                a[i][j] = "g"

        # piece表示
        for player in range(self.n_players):
            for goal_idx in self.goals[player]:
                i, j = self.goal2ij(player, goal_idx)
                if a[i][j] == "g":
                    a[i][j] = str(player)
                else:
                    a[i][j] += str(player)
        # starts
        print(self.starts)

        # board
        for raw in a:
            print("\t".join(raw))

    def coordinate2ij(self, coordinate):
        edge = coordinate//self.len_myway
        mod = coordinate % self.len_myway
        if edge == 0:
            i, j = 0, mod
        elif edge == 1:
            i, j = mod, self.len_myway
        elif edge == 2:
            i, j = self.len_myway, self.len_myway-mod
        elif edge == 3:
            i, j = self.len_myway - mod, 0
        else:
            raise Exception("invalid coordinate")
        return i, j

    def goal2ij(self, player, goal_idx):
        if player == 0:
            i, j = 1, goal_idx+1
        elif player == 1:
            i, j = goal_idx+1, self.len_myway-1
        elif player == 2:
            i, j = self.len_myway-1, self.len_myway - goal_idx-1
        elif player == 3:
            i, j = self.len_myway-goal_idx-1, 1
        else:
            raise Exception("invalid player")
        return i, j

    def apply(self, action):
        """actionを適用する."""
        if action.target.__class__.__name__ == "Position":
            # 公道にいるコマがターゲットの場合
            self.move(action.target.coordinate, action.roll)
        elif type(action.target) == int:
            # goalにいるコマがターゲットの場合
            self.move_piece_in_goal(action.target, action.player, action.roll)
        elif action.target == "depart":
            # スタートする
            self.depart(action.player)
        else:
            raise Exception("Invalid action target.")


class Game:
    def __init__(self, board, agents_class_list, max_turn, max_roll=6, min_roll=1, depart_roll=6, shuffle_agent=True, verbose=False):
        if board.n_players != len(agents_class_list):
            raise Exception("The number of players does not match.")
        self.board = board
        if shuffle_agent:
            random.shuffle(agents_class_list)

        self.agents = [agent_cls(i)
                       for i, agent_cls in enumerate(agents_class_list)]
        self.max_roll = max_roll
        self.min_roll = min_roll
        self.max_turn = max_turn
        self.depart_roll = depart_roll
        self.verbose = verbose

    def play(self):
        for turn in range(self.max_turn):
            print(f"[Turn {turn+1}]")
            turn_agent = 0
            while (turn_agent < len(self.agents)):
                roll = self.roll()
                agent = self.agents[turn_agent]
                action = agent.choose_action(
                    self.board, roll, self.depart_roll)
                if not action:
                    print(f"Player {agent.player_idx} passed.")
                else:
                    print(action)
                    self.board.apply(action)

                if self.verbose:
                    self.board.print_board()

                if len(set(self.board.goals[agent.player_idx])) == self.board.n_pieces:
                    print(f"Player {agent.player_idx} finished!!")
                    return {"status": "finished", "turn": turn+1, "winner_idx": agent.player_idx, "winner_agent": agent.__class__.__name__}
                if roll != self.depart_roll:
                    turn_agent += 1

        return {"status": "ongoing", "turn": turn+1, "winner_idx": None, "winner_agent": None}

    def roll(self):
        return random.randint(self.min_roll, self.max_roll)

    def validate_action(self, action):
        if action.roll != self.depart_roll:
            raise Exception(
                f"If you want to depart, you need roll {self.max_roll}.")
