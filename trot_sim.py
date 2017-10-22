'''
Created on Sept 25, 2017

@author: ckw017

Purpose: Simulate and find the expected win rate for two strategies in the game of Hog, with the modified rule set
         Create an optimal counter strategy by selecting the best rolls for each set of scores when playing against a given strategy
'''
from hog_sim import memoize, get_frequencies, is_swap, roll_dice
import sys
import pickle
import os

resources_path = os.path.join(os.path.dirname(__file__), 'resources/')

sys.setrecursionlimit(5000)

#strats
perf_table_old = pickle.load(open(resources_path + 'strategies/perf_table_old.p', 'rb'))
perf_strat_old = lambda a, b: perf_table_old[a][b]
a0 = lambda x, y: 0
a1 = lambda x, y: 1
a7 = lambda x, y: 7
a8 = lambda x, y: 8

def hybrid(x, y):
    if x or y: return 4
    return 0

@memoize
def expected_frequency(strat1, strat2, score1, score2, turn, can_trot):
    '''Calculates the expected frequency that a combination of scores, turn number, and time trot ability
       Takes place in a game between strat1 and strat2
       
       Args:
          strat1 (strategy function): Player 1's strategy
          strat2 (strategy function): Player 2's strategy
          score1 (int): Player 1's score
          score2 (int): Player 2's score
          turn (int): The number of the current turn
          can_trot (bool): True if the Player 1 can use time trot, otherwise False
        
        Returns:
            float: The expected frequency of appearance of the turn defined by the arguments in a match between Player 1 and Player 2
    '''
    if score1 == 0: #If you score is 0, then you have yet to move
        if score2 == 0 and turn == 0 and can_trot: return 0.5 #Checks if you have the first turn (Occurs 50% of the time)
        return second_move_base_case(strat2, score2, turn, can_trot) #Checks if you had the second move
    if is_swap(score1, score2): score1, score2 = score2, score1
    total_freq, prev_turn = 0, (turn + 7) % 8
    for i in range(1, 61):
        if can_trot:
            prev_score2 = score2 - i
            if prev_score2 >= 0:
                prev_dice2 = strat2(prev_score2, score1)
                freqs = get_frequencies(prev_dice2, score1)
                if i in freqs: 
                    total_freq += expected_frequency(strat2, strat1, prev_score2, score1, prev_turn, False) * freqs[i]
                    if prev_dice2 != prev_turn: total_freq += expected_frequency(strat2, strat1, prev_score2, score1, prev_turn, True) * freqs[i]
        else:
            prev_score1 = score1 - i
            if prev_score1 >= 0:
                prev_dice1 = strat1(prev_score1, score2)
                if prev_dice1 == prev_turn:
                    freqs = get_frequencies(prev_dice1, score2)
                    if i in freqs: total_freq += expected_frequency(strat1, strat2, prev_score1, score2, prev_turn, True) * freqs[i]
    return total_freq

@memoize   
def second_move_base_case(strat2, score2, turn, can_trot):
    '''Base case for expected_expected frequency to determine if you had the second move.
    
       Args:
          strat2 (strategy function): The Player 2's strategy function
          score2 (int): Player 2's current score
          turn (int): The current turn number
          can_trot (bool): True if Player 1 can use time trot, False otherwise
          
       Returns:
           float: The expected frequency of appearance of the turn defined by the arguments in a match between Player 1 and Player 2
    '''
    if (turn != 1 and turn != 2) or not can_trot: return 0 #strat1's first move can only take place on turns 1 or 2, and you should be able to trot
    num_dice = strat2(0, 0) #strat1's roll on the first turn
    if num_dice and turn == 1: #Opponent didn't time trot
        freqs = get_frequencies(num_dice)
        if score2 in freqs: return 0.5 * freqs[score2] #Probability that strat1 had the first turn and rolled enough to reach current score
    elif not num_dice and turn == 2: #The opponent has time trotted
        num_dice = strat2(1, 0) #strat1's roll on the second turn. Score will always be 1-0
        freqs = get_frequencies(num_dice, 0)
        if score2 - 1 in freqs: return 0.5 * freqs[score2 - 1] #Probability that strat1 had the first turn and rolled enough to reach current score
        return 0
    return 0 #Impossible situation -> 0 frequency

@memoize
def sim_counter_sets(tutor, strat, score1, score2, turn, can_trot):
    '''Determines the win rates of all possible number of dice for a set of scores for a given turn and ability to trot
       Predicts using the win rate of tutor against strat.
       Args:
           tutor (strategy function): Strategy used to determine win rates for given rolls
           strat (strategy function): The opponent of tutor used to determine win rates
           score1 (int): The tutor strategy's score
           score2 (int): The opponent's score
           turn (int): Current turn number
           can_trot (bool): True if tutor can use time trot, False otherwise
       
       Returns:
           tuple: A tuple containing the win rate of all possible number of dice. Index of rate in the tuple corresponds to the number of dice/
    
    '''
    roll_set = ()
    for num_rolls in range(11):
        freqs = get_frequencies(num_rolls, score2)
        if (num_rolls == turn) and can_trot: 
            roll_set += (sum([apply_rules_counter(tutor, strat, score1 + points, score2, turn, can_trot, sim_counter, True)
                        * freqs[points] for points in freqs]),)
        else: 
            roll_set += (sum([apply_rules_counter(tutor, strat, score1 + points, score2, turn, can_trot, sim_opponent, False) 
                        * freqs[points] for points in freqs]),)
    return roll_set

@memoize
def sim_counter(tutor, strat, score1 = 0, score2 = 0, turn = 0, can_trot = True):
    '''Simulates a match between tutor and strat, and uses that information to develop a counter strategy to strat.
       Will NOT create a perfect counter strategy, since the expected turn frequencies used to calculate the ideal
       roll is based on a match between the tutor and strat, instead of this strategy and strat.
    
       Args:
           tutor (strategy function): Strategy used to determine the win rates of possible rolls across all possible scenarios
           strat (strategy function): The opponent of tutor used to determine win rates of possible rolls all possible scenarios
           score1 (int): The tutor strategy's score
           score2 (int): The opponent's score
           turn (int): Current turn number
           can_trot (bool): True if tutor can use time trot, False otherwise
           
       Returns:
           tuple: tuple containing the best roll with the best win rate and that rate
    '''
    best_roll, best_rate = 0, 0
    roll_sets = ([sim_counter_sets(tutor, strat, score1, score2, turn, True ) for turn in range(8)] +
                 [sim_counter_sets(tutor, strat, score1, score2, turn, False) for turn in range(8)])
    total_frequency = sum([expected_frequency(tutor, strat, score1, score2, turn, True ) for turn in range(8)] +
                          [expected_frequency(tutor, strat, score1, score2, turn, False) for turn in range(8)])
    if total_frequency:
        for num_rolls in range(11):
            total_rate = 0
            for i in range(16):
                if i < 8: total_rate += roll_sets[i][num_rolls] * (expected_frequency(tutor, strat, score1, score2, i, True) / total_frequency)
                else: total_rate += roll_sets[i][num_rolls] * (expected_frequency(tutor, strat, score1, score2, i % 8, False) / total_frequency)
            if total_rate > 1: total_rate = 1
            if total_rate > best_rate: best_rate, best_roll = total_rate, num_rolls
    return best_rate, best_roll

@memoize
def sim_opponent(tutor, strat, score1, score2, turn, can_trot):
    '''Simulates strat when playing against tutor. Returns strat's win rate for the given scores and turn number'''
    num_rolls = strat(score1, score2)
    freqs = get_frequencies(num_rolls, score2)
    if (num_rolls == turn) and can_trot:
        return sum([apply_rules_counter(tutor, strat, score1 + points, score2, turn, can_trot, sim_opponent, True) * freqs[points] for points in freqs]), num_rolls
    return sum([apply_rules_counter(tutor, strat, score1 + points, score2, turn, can_trot, sim_counter, False) * freqs[points] for points in freqs]), num_rolls

@memoize
def apply_rules_counter(tutor, strat, score1, score2, turn, can_trot, sim_next, trotted):
    '''Applies the rules of the game, and then returns the win rate of the player whose turn is next'''
    if score1 > 99: return 1
    if is_swap(score1, score2): score1, score2 = score2, score1
    next_turn = (turn + 1) % 8
    if trotted: return sim_next(tutor, strat, score1, score2, next_turn, False)[0]
    return 1 - sim_next(tutor, strat, score2, score1, next_turn, True)[0]

def create_mock_counter(tutor, strat):
    '''Creates a counter strategy, based on the expected frequencies of turns in a match between tutor and strat.
       The strategy created will NOT be the perfect counter to strat.
       Returns a tuple of the strategy, it's lookup table, and its rate against strat.
    
    '''
    counter_table = []
    for y in range(100):
        counter_table.append([0] * 100)
        for x in range(100):
            counter_table[y][x] = sim_counter(tutor, strat, y, x)[1]
    
    
    def mock_counter(score1, score2):
        '''Mock counter strategy against strat, relying on turn frequencies of the tutor's gameplay'''
        return counter_table[score1][score2]
    
    return mock_counter, counter_table, sim_counter(tutor, strat, 0, 0)[0]

def learn(tutor, seed, iterations = 1):
    '''Create's mock counter strategies in sequence, using previous outputs as tutors for the next iteration.
       Returns a list of all mock counter strategies created.
    '''
    print("Iterations Left: ", iterations)
    mock = create_mock_counter(tutor, seed)
    print("Mock Rate: ", mock[2])
    print("Rate: ", expected_win_rate(mock[0], seed))
    pickle.dump(mock[1:], open('iter' + str(iterations) + ".p", 'wb'))
    if iterations > 1:
        clear_memos()
        return [mock] + learn(mock[0], seed, iterations - 1)
    return [mock]

def compete(strategies):
    '''Returns of a dict strategies and the number of matches won.'''
    strat_wins = {strat : 0 for strat in strategies}
    for strat1 in reversed(strategies):
        for strat2 in strategies[:-1]:
            if expected_win_rate(strat1, strat2) > 0.5: strat_wins[strat1] += 1
            else: strat_wins[strat2] += 1
        clear_memos()
        strategies.pop()
    return strat_wins

@memoize
def sim_game(strat1 = a0, strat2 = a0, score1 = 0, score2 = 0, turn = 0, can_trot = True):
    '''Plays a simulated game between two strategies from a given set of scores.
       Returns the expected probability of strat1 winning against strat2.

       Args:
           score1 (int): Player 1's score
           score2 (int): Player 2's score
           strat1 (strategy function): Player 1's strategy
           strat2 (strategy function): Player 2's strategy
        
        Returns:
            float: The expected probability of strat1 winning against strat2 for the situation defined by the parameters
            
    '''
    assert 0 <= turn <= 7, "Invalid turn"
    num_dice = strat1(score1, score2)
    trotted = num_dice == turn and can_trot
    freqs = get_frequencies(num_dice, score2)
    return sum([apply_rules(strat1, strat2, score1 + points, score2, turn, trotted) * freqs[points] for points in freqs])

@memoize
def apply_rules(strat1, strat2, score1, score2, turn, trotted):
    '''Applies the rules of Hog, then simulates strat2's turn to predict the win rate of strat1.
       See https://cs61a.org/proj/hog/ for more details on the rules.
       
       Args:
           strat1 (strategy function): Player 1's strategy
           strat2 (strategy function): Player 2's strategy
           score1 (int): Player 1's score
           score2 (int): Player 2's score
           turn (int): The current turn
           trotted(bool): True if Player 1 trotted in the previous turn, otherwise false
        
        Returns:
            float: The expected probability of strat1 winning against strat2
            
    '''
    assert 0 <= turn <= 7, "Invalid turn"
    if score1 > 99: return 1
    if is_swap(score1, score2): score1, score2 = score2, score1
    if trotted: return sim_game(strat1, strat2, score1, score2, (turn + 1) % 8, False)
    return 1 - sim_game(strat2, strat1, score2, score1, (turn + 1) % 8, True)


def clear_memos():
    '''Clears the memos of methods used in learn'''
    expected_frequency.memo = {}
    sim_counter_sets.memo = {}
    sim_counter.memo = {}
    sim_opponent.memo = {}
    apply_rules_counter.memo = {}
    apply_rules.memo = {}
    sim_game.memo = {}

def play(strat1, strat2, score1 = 0, score2 = 0, turn = 0, can_trot = True):
    '''Plays an actual game using random, fair dice'''
    assert 0 <= turn <= 7, "Invalid turn"
    num_dice = strat1(score1, score2)
    score1 += roll_dice(num_dice, score2)
    if score1 > 99: return 1
    if is_swap(score1, score2): score1, score2 = score2, score1
    if num_dice == turn and can_trot: return play(strat1, strat2, score1, score2, (turn + 1) % 8, False)
    return 1 - play(strat2, strat1, score2, score1, (turn + 1) % 8, True)

def expected_win_rate(strat1, strat2):
    '''Calculates the expected win rate of a given strategy'''
    return (sim_game(strat1, strat2) + 1 - sim_game(strat2, strat1))/2

def average_win_rate(strat1, strat2, num_matches = 1000):
    '''Calculates the average win rate of strat1 for num_matches amount of games between strat1 and strat2'''
    first_turn  = sum([play(strat1, strat2) for _ in range(num_matches//2)])
    second_turn = num_matches/2 - sum([play(strat2, strat1) for _ in range(num_matches//2)])
    return (first_turn + second_turn)/num_matches