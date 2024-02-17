from copy import deepcopy
import random
import numpy as np
from game import Player, Move, Game

def count_max_aligned(state, player_id):
    count = 0
    for i in range(5):
        count = max(count, sum(state[i, :] == player_id))
        count = max(count, sum(state[:, i] == player_id))
    count = max(count, sum(state[x, x] == player_id for x in range(5))) # count on diagonal
    count = max(count, sum(state[x, 4-x] == player_id for x in range(5))) # count on anti-diagonal
    return count

def get_all_valid_moves(game: Game, player_id, with_simmetries=False):
    valid_moves = []
    moves= [Move.BOTTOM, Move.LEFT, Move.RIGHT, Move.TOP]
    random.shuffle(moves)
    for i in [0, 4]:
        for j in range(5):
            for m in moves:
                g = deepcopy(game)
                ok = g._Game__move((i, j), m, player_id)
                if ok :
                    board=g.get_board() 
                    free_cells= np.count_nonzero(board==-1)
                    one_cells = np.count_nonzero(board==1)
                    if not with_simmetries or not check_simmetries(valid_moves, board, free_cells, one_cells):
                        valid_moves.append((((i, j), m), g.get_board()))
    for j in [0, 4]:
        for i in range(1, 4):
            for m in moves:
                g = deepcopy(game)
                ok = g._Game__move((i, j), m, player_id)
                if ok :
                    board=g.get_board() 
                    free_cells= np.count_nonzero(board==-1)
                    one_cells = np.count_nonzero(board==1)
                    if not with_simmetries or not check_simmetries(valid_moves, board, free_cells, one_cells):
                        valid_moves.append((((i, j), m), g.get_board()))
    return valid_moves


def check_simmetries(list_states, new_state, free_cells_new_state, one_cells_new_state):  #move => ((i, j), slide)

    for s in list_states:
        free_cells = np.count_nonzero(s[1]==-1)
        one_cells = np.count_nonzero(s[1]==1)     

        if free_cells_new_state != free_cells or one_cells_new_state != one_cells or new_state[2][2] != s[1][2][2]:
            return False
    
        for k in range(1, 5): # k = 4 means 4 rotations so it's like not rotating it
            for flip in [1, -1]:  # 1 => not flipped, -1 => flipped
                key = k * flip  
                int_state = np.flip(s[1], axis=1) if key<0 else s[1]# axis=1 is to flip horizontally
                int_state = np.rot90(int_state, k=abs(k)%4, axes=(1, 0))
                if np.array_equal(new_state, int_state): # you found the simmetry, now the fun starts
                    return True     
    return False

def print_board(game:Game):
    print()
    print("    ", end="")
    for i in range(5):
        print('\033[0m', f"{i} ", '\033[0m',end='')
    print()
    print("   ", end="")
    print('\033[0m', "__________________", '\033[0m', end='')
    print()
    for i  in range(5):
        print(i," |", end="")
        for cell in game.get_board()[i]:
            if cell == -1:
                print('\033[90m', "-", '\033[0m', end=' ')  # Grey color for -1
            elif cell == 0:
                print('\033[91m', "X", '\033[0m', end=' ')  # Red color for 0
            elif cell == 1:
                print('\033[92m', "O", '\033[0m', end=' ')  # Green color for 1
            else:
                print(cell, end=' ')
        print()

class HumanPlayer(Player):
    def __init__(self) -> None:
        super().__init__()
    
    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        print_board(game)
        print()
        while True:
            from_pos = input("Enter the position of the piece you want to move (x,y): ").split(',')
            if from_pos[0]=="ESCAPE" or from_pos[0]=="escape" or from_pos[0]=="\033":
                exit()
            if not from_pos[0].isdigit() or not from_pos[1].isdigit():
                print("Insert numbers, try again")
                continue
            else:
                from_pos = tuple(map(int, from_pos))
                if from_pos[0]>=0 and from_pos[0]<=4 and from_pos[1]>=0 and from_pos[1]<=4:
                    break
                else:
                    print("Numbers too big, try again")
        move = input("Enter the direction you want to move the piece (TOP, BOTTOM, LEFT, RIGHT): ")
        if move == "TOP" or move=="top":
            move = Move.TOP
        elif move == "BOTTOM" or move=="bottom":
            move = Move.BOTTOM
        elif move == "LEFT" or move=="left":
            move = Move.LEFT
        elif move == "RIGHT" or move=="right":
            move = Move.RIGHT
        else:
            print("slide not exist, try again")
        print("YOU: ", from_pos, move)
        return (from_pos[1], from_pos[0]), move

    
class RandomPlayer(Player):
    
    def __init__(self) -> None:
        super().__init__()

    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        from_pos = (random.randint(0, 4), random.randint(0, 4))
        move = random.choice([Move.TOP, Move.BOTTOM, Move.LEFT, Move.RIGHT])
        return from_pos, move

class MyPlayer(Player):
    def __init__(self, player_id, max_depth=3, with_simmetries=False, against_human=False):
        self.max_depth = max_depth
        self.against_human = against_human
        self.with_simmetries = with_simmetries
        self.player_id = player_id

    def make_move(self, game: Game) -> tuple[tuple[int, int], Move]:
        if self.against_human:
            print_board(game)
            print()
        _, move = self.minimax(game, self.max_depth, float('-inf'), float('inf'), True)
        if self.against_human:
            print("OPPONENT: ", move[0], move[1])
        return move[0], move[1]
    
    def minimax(self, game:Game, depth, alpha, beta, isMaximizing):
        if depth == 0 or game.check_winner() != -1:
            return self.evaluate(game, self.player_id), None 
        if isMaximizing:
            best_move = None
            v = -float('inf')
            valid_moves = get_all_valid_moves(game, self.player_id, self.with_simmetries) # move is the player_id of the player currently performing the move, player_id is the id of MY player
            for vm in valid_moves:
                next_game = deepcopy(game)
                next_game._Game__move(vm[0][0], vm[0][1], self.player_id)
                eval,_ = self.minimax(next_game, depth-1 , alpha, beta, False)
                if eval > v:
                    v = eval
                    best_move = vm[0]
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return v, best_move 
        else:
            best_move = None
            v = float('inf')
            valid_moves = get_all_valid_moves(game, 1 - self.player_id, self.with_simmetries) # move is the player_id of the player currently performing the move, player_id is the id of MY player
            for vm in valid_moves:
                next_game = deepcopy(game)
                next_game._Game__move(vm[0][0], vm[0][1], 1 - self.player_id)
                eval, _ = self.minimax(next_game, depth - 1, alpha, beta, True)
                if eval < v:
                    v = eval
                    best_move = vm[0]
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return v, best_move 
    
    def evaluate(self, game: Game, player_id) -> int:
        winner = game.check_winner()
        if winner == player_id:
            return 1
        if winner != -1:
            return -1
        my_count = count_max_aligned(game.get_board(), player_id)
        opp_count = count_max_aligned(game.get_board(), 1 - player_id)
        return (my_count - opp_count) / 5
        # return 0