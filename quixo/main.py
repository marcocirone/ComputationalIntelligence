import random
from game import Game, Move, Player
import numpy as np
from tqdm.auto import tqdm
from colorama import Fore
from copy import deepcopy

MOVES = []
INIT_TRAIN = 1_000
N_EXPANSIONS =  1_000
TEST_MATCHES = 100


class Node():
    
    def __init__(self, move, state, parent:'Node'=None, terminal=False) -> None:
        self.parent = parent  # TO CLIMB THE TREE UPWARD
        self.children: list['Node'] = [] 
        self.move = move  #THE MOVE ASSIGNED TO THE NODE
        self.wins = 0  
        self.losses = 0
        self.depth = parent.depth + 1 if parent is not None else 0
        self.terminal = terminal
        self.state = state #state of the board on that move
        self.score = None # only used if you resort to minimax 

        if parent is not None:  # include the new node in the children list of the parent
            parent.append_child(self)

    def append_child(self, child:'Node'):  #add a child to the node
        self.children.append(child)

    def find_child(self, move):
        for c in self.children:
            if move == c.move:
                return c
        return None # if no child has the assigned move
    
    def print(self):
        print(f"move:{self.move}, wins:{self.wins}, losses:{self.losses}, depth:{self.depth}, #children: {len(self.children)}")


class Tree():
    def __init__(self) -> None:
        self.head = Node(None, np.ones((5, 5), dtype=np.uint8) * -1) # Tree head has no move associated to it
        # initialize all the valid starting moves for the tree
        # vm = get_all_valid_first_moves()
        # for valid_move in vm:
        #     Node(valid_move, self.head)
        self.depth = 0
    
    def set_depth(self, depth):
        if depth > self.depth:
            self.depth = depth

    def print(self):
        print(f"Number of sons:{len(self.head.children)}")

class TrainGame(Game):
    
    def __init__(self, board=np.ones((5, 5), dtype=np.uint8) * -1, current_player=1) -> None:  #possibility to start a game from a given intermediate state
        self._board = board
        self.current_player_idx = current_player

    def print(self):
        for i in range(5):
            for j in range(5):
                v = self._board[i][j]
                print(f"{Fore.BLUE}O{Fore.RESET} " if v == 0 else f"{Fore.RED}X{Fore.RESET} " if v == 1 else f"{Fore.GREEN}E{Fore.RESET} ", end="")
            print()
        print()

    def set_board(self, board) -> None:
        self._board = board

    def move(self, from_pos: tuple[int, int], slide: Move, player_id: int) -> bool:
        return self._Game__move(from_pos, slide, player_id)


class RandomPlayer(Player):
    
    def __init__(self, player_id) -> None:
        super().__init__()
        self.player_id = player_id

    def make_move(self, game: 'TrainGame') -> tuple[tuple[int, int], Move]:
        # init_board = game.get_board()
        # ok = False
        # while not ok:
        #     from_pos = (random.randint(0, 4), random.randint(0, 4))
        #     move = random.choice([Move.TOP, Move.BOTTOM, Move.LEFT, Move.RIGHT])
        #     ok = game.move(from_pos, move, self.player_id)  #THIS METHOD CHANGES THE BOARD, I NEED TO RESTORE THE PREVIOUS ONE
        # MOVES.append(((from_pos, move), deepcopy(game.get_board())))
        # game.set_board(init_board)
        # return from_pos, move
    
        vm = get_all_valid_moves(deepcopy(game.get_board()), self.player_id)
        chosen_move = random.choice(vm)
        # print(chosen_move)
        MOVES.append(((chosen_move[0][0], chosen_move[0][1]), chosen_move[1]))
        return chosen_move[0][0], chosen_move[0][1]


class Opponent(Player):
    def __init__(self, player_id) -> None:
        super().__init__()
        self.player_id = player_id
    
    def make_move(self, game: Game) -> tuple[tuple[int, int], Move]:
        from_pos = (random.randint(0, 4), random.randint(0, 4))
        move = random.choice([Move.TOP, Move.BOTTOM, Move.LEFT, Move.RIGHT])
        if len(MOVES) % 2 == self.player_id: # if it's your turn than add a new element to the list
            MOVES.append((from_pos, move))
        else: # your previous move was not valid, try again
            MOVES[-1] = (from_pos, move)
        return from_pos, move

class MyPlayer(Player):

    def __init__(self, tree:Tree, player_id) -> None:
        super().__init__()
        self.tree:Tree = tree
        self.player_id = player_id
        self.current_state:Node = self.tree.head
        self.not_found = False
        self.switch_turn = None
        self.switch_cause = None

    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        if not self.not_found:
            if len(MOVES) == 0: #First move of the game
                best_move = max(self.current_state.children, key=lambda e: e.wins / (e.wins + e.losses))
                from_pos, move = best_move.move[0], best_move.move[1]
                next_state = self.current_state.find_child(best_move.move)
                if next_state == None:
                    self.not_found = True
                    self.switch_turn = len(MOVES) + 1
                else:
                    self.current_state = next_state
                    MOVES.append(best_move.move)
            # LOOK FOR THE NODE IN THE TREE USING THE MOVES LIST
            else:
                opponent_move = self.current_state.find_child(MOVES[-1]) # find the opponent last move in the tree
                if opponent_move is not None:
                    best_move = max(opponent_move.children, key=lambda e: e.wins / (e.wins + e.losses), default=None)
                    if best_move is not None:
                        from_pos, move = best_move.move[0], best_move.move[1]
                        self.current_state = best_move
                        MOVES.append(best_move.move)
                    else:
                        # print("Best move not found")
                        self.not_found = True
                        self.switch_cause = "Best move not found"
                else:
                    # print("Opponent move not found")
                    self.not_found = True
                    self.switch_cause = "Opponent move not found"
        # IF YOU DON'T FIND THE NODE, PLAY RANDOMLY
        if self.not_found:
            if self.switch_turn is None:
            #     print(f"Switch strategy at turn {len(MOVES) + 1}")
                self.switch_turn = len(MOVES) + 1
                print(MOVES)
                # now try to print the entire steps until now
                f_node = self.tree.head
                for m in MOVES:
                    child = f_node.find_child(m)
                    child.print() if child is not None else print("None")
                    if child is None:
                        print("LIST OF CHILDREN:")
                        for c in f_node.children:
                            print(c.move)
                    f_node = child
            
            # RANDOM
            # from_pos = (random.randint(0, 4), random.randint(0, 4))
            # move = random.choice([Move.TOP, Move.BOTTOM, Move.LEFT, Move.RIGHT])

            # MINIMAX
            valid_moves = get_all_valid_moves(game.get_board(), self.player_id)
            scores_list = []
            for vm in valid_moves:
                score = minimax(vm[1], self.player_id, (self.player_id + 1) % 2, -float('inf'), float('inf'), 5, True, vm[2])
                scores_list.append((vm[0], score))
            chosen_move = max(scores_list, key=lambda e: e[1])
            from_pos = chosen_move[0][0]
            move = chosen_move[0][1]

            if len(MOVES) % 2 == self.player_id: # if it's your turn than add a new element to the list
                MOVES.append((from_pos, move))
            else: # your previous move was not valid, try again
                MOVES[-1] = (from_pos, move)
        return from_pos, move

    
def get_all_valid_moves(state, player_id):
    valid_moves = []
    for i in range(5):
        for j in range(5):
            for m in [Move.BOTTOM, Move.LEFT, Move.RIGHT, Move.TOP]:
                game = TrainGame(deepcopy(state))
                ok = game.move((i, j), m, player_id)
                if ok:
                    valid_moves.append((((i, j), m), game.get_board(), game.check_winner()))
    return valid_moves

def get_ancestors(node:Node):
    n = node
    l:list[Node] = [n]
    while n.parent is not None:
        l.append(n.parent)
        n=n.parent
    return sorted(l, key=lambda e: e.depth)

def minimax(state, player_id, move, alfa, beta, max_depth, isMaximizing, winner):
    if winner != -1: # terminal node
        return 1 if winner == player_id else -1
    if max_depth == 0:
        return 0 #counts as a draw
    valid_moves = get_all_valid_moves(state, move) # move is the player_id of the player currentòy performing the move, player_id is the id of MY player
    if isMaximizing:
        v = -float('inf')
        for vm in valid_moves:
            v = max([v, minimax(vm[1], player_id, (move + 1) % 2, alfa, beta, max_depth - 1, not isMaximizing, vm[2])])
            alfa = max([alfa, v])
            if beta <= alfa:
                break
    else:
        v = float('inf')
        for vm in valid_moves:
            v = min([v, minimax(vm[1], player_id, (move + 1) % 2, alfa, beta, max_depth - 1, not isMaximizing, vm[2])])
            beta = min([beta, v])
            if beta <= alfa:
                break
    return v
        

if __name__ == '__main__':
    # mc_tree, node_list = initialize_tree()
    cont_terminal = 0 

    mc_tree = Tree()
    node_list:list[Node] = []

    n_wins = 0
    n_losses = 0

    print("INITIALIZE THE TREE")

    for _ in tqdm(range(INIT_TRAIN)):
        g = TrainGame(np.ones((5, 5), dtype=np.uint8) * -1, 1)
        # g.print()
        player1 = RandomPlayer(0)
        player2 = RandomPlayer(1)
        winner = g.play(player1, player2)

        if winner == 0:
            n_wins += 1
        else:
            n_losses += 1
        mc_tree.set_depth(len(MOVES))

        parent = mc_tree.head
        for i in range(len(MOVES)):
            child = parent.find_child(MOVES[i][0])
            if child is None:
                child = Node(MOVES[i][0], MOVES[i][1], parent=parent, terminal=True if i == len(MOVES) - 1 else False)
                node_list.append(child)
                if child.terminal:
                    cont_terminal += 1
            if winner == 0:
                if child.depth % 2 == 0:
                    child.wins += 1
                else:
                    child.losses += 1
            else:
                if child.depth % 2 == 0:
                    child.losses += 1
                else:
                    child.wins += 1
            parent = child
        MOVES = []


    nodes_to_expand = sorted(filter(lambda e: not e.terminal, node_list), key=lambda e: (e.depth), reverse=False)
    print(f"Nodes to expand: {len(nodes_to_expand)}")
    num_expansion = 0 # How many nodes I have expanded already
    
    expansions = len(nodes_to_expand) if N_EXPANSIONS >= len(nodes_to_expand) else N_EXPANSIONS

    print(f"# of nodes = {len(node_list)}")
    
    print("\nEXPANSION")
    for j in tqdm(range(expansions)):
        node = nodes_to_expand[j]
        for _ in range(10):
            MOVES = []
            g = TrainGame(node.state, (node.depth + 1) % 2)
            player1 = RandomPlayer(0)
            player2 = RandomPlayer(1)
            winner = g.play(player1, player2)
            mc_tree.set_depth(node.depth + len(MOVES))
            ancestors = get_ancestors(node)
            for a in ancestors:
                if a.depth % 2 == 0: #moves of player 1
                    if winner == 1:
                        a.wins += 1
                    else:
                        a.losses += 1
                else: #moves of player 0
                    if winner == 1:
                        a.losses += 1
                    else:
                        a.wins += 1
            parent = node
            for i in range(len(MOVES)):
                child = parent.find_child(MOVES[i][0])
                if child is None:
                    child = Node(MOVES[i][0], MOVES[i][1], parent=parent, terminal=True if i == len(MOVES) - 1 else False)
                    node_list.append(child)
                    if child.terminal:
                        cont_terminal += 1
                if winner == 0:
                    if child.depth % 2 == 0:
                        child.wins += 1
                    else:
                        child.losses += 1
                else:
                    if child.depth % 2 == 0:
                        child.losses += 1
                    else:
                        child.wins += 1
                parent = child
            MOVES = []   
        
    wins = 0
    losses = 0

    print(f"# of nodes = {len(node_list)}")

    print("\nTEST GAMES")

    switch_turns = []
        
    for _ in tqdm(range(TEST_MATCHES)):
        g = Game()
        player1 = MyPlayer(mc_tree, 0)
        player2 = Opponent(1)
        winner = g.play(player1, player2)
        switch_turns.append((player1.switch_turn, player1.switch_cause))
        if winner == 0:
            wins +=1
        else:
            losses += 1
        MOVES = []
    print(f"wins: {wins}, losses: {losses}")

    print(switch_turns)
    