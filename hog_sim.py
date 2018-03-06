'''
Created on Sept 10, 2017

@author: ckw017

Purpose: Simulate and find the expected win rate for two strategies in the game of Hog
         Create an optimal counter strategy by selecting the best rolls for each set of scores when playing against a given strategy
'''
from random import randint
import sys

sys.setrecursionlimit(100000)

max_score = 100
def memoize(fn):
    '''Memoization decorator'''
    def memoized_fn(*args):
        if args not in memoized_fn.memo:
            memoized_fn.memo[args]=fn(*args)
        return memoized_fn.memo[args]
    memoized_fn.memo = {}
    return memoized_fn

@memoize
def combinations(total, num_parts, parts = (2, 3, 4, 5, 6)):
    '''Gives the number of combinations by which exactly num_parts amount of parts
       can be used to sum to total
       
       Args:
           total (int): Total value attempting to sum to
           num_parts (int): The number of parts available to use to reach the total
           parts (tuple): The parts available for use. Defaults to the non "Pig Out" values for hog
        
        Returns:
            int: The number of possible combinations
            
    '''
    combos = 0
    if num_parts == 1:
        if total in parts:
            return 1
        return 0
    else:
        for i in parts:
            combos += combinations(total - i, num_parts - 1, parts)
    return combos

@memoize
def get_frequencies(num_dice, opp_score = None):
    '''Creates a dictionary of point frequency pairs for each possible point total outcome
       for the given number of dice
       
       Args:
           num_dice (int): The number of dice being rolled
        
        Returns:
            dict: Dictionary containing point : frequency pairs for the given number of dice rolled
            
    '''
    if num_dice == 0: return {free_bacon(opp_score): 1}
    total = pow(6, num_dice)
    freqs  = {1: 1 - pow(5, num_dice)/total}
    for i in range(2, 61):
        freq = combinations(i, num_dice)/total
        if freq:
            freqs[i] = freq
    return freqs

def is_swap(score1, score2):
    '''Gameplay rule. See https://cs61a.org/proj/hog/ for more details
       
       Args:
           score1 (int): The score of player1
           score2 (int): The score of player2
        
        Returns:
            bool: True if the pair of scores qualify for a Swine Swap, False otherwise
            
    '''
    return score1 > 1 and score2 > 1 and (score1 % score2 == 0 or score2 % score1 == 0) and score1 != score2

def free_bacon(other_score):
    '''Gameplay rule. See https://cs61a.org/proj/hog/ for more details
       
       Args:
           other_score (int): Score of the opposing player
        
        Returns:
            int: The max of the two digits of the opponents score, plus 1
            
    '''
    return max(other_score // 10, other_score % 10) + 1

@memoize
def sim_game(strat1, strat2, score1, score2):
    '''Plays a simulated game between two strategies from a given set of scores.
       Returns the expected probability of strat1 winning against strat2.

       Args:
           score1 (int): Player 1's score
           score2 (int): Player 2's score
           strat1 (strategy function): Player 1's strategy
           strat2 (strategy function): Player 2's strategy
        
        Returns:
            float: The expected probability of strat1 winning against strat2
            
    '''
    num_rolls = strat1(score1, score2)
    if num_rolls:
        freqs = get_frequencies(num_rolls)
        return sum([apply_rules(strat1, strat2, score1 + points, score2) * freqs[points] for points in freqs])
    return apply_rules(strat1, strat2, score1 + free_bacon(score2), score2)

@memoize
def apply_rules(strat1, strat2, score1, score2):
    '''Applies the rules of Hog, then simulates strat2's turn to predict the win rate of strat1.
       See https://cs61a.org/proj/hog/ for more details on the rules.
       
       Args:
           score1 (int): Player 1's score
           score2 (int): Player 2's score
           strat1 (strategy function): Player 1's strategy
           strat2 (strategy function): Player 2's strategy
        
        Returns:
            float: The expected probability of strat1 winning against strat2
            
    '''
    if score1 > max_score: return 1
    if is_swap(score1, score2):
        score1, score2 = score2, score1
    return 1 - sim_game(strat2, strat1, score2, score1)
           
@memoize
def sim_counter(score1, score2, strat):
    '''Determines the optimal number of dice to roll given a pair of scores and an opponent strategy.
       
       Args:
           score1 (int): The optimal strategy's score
           score2 (int): The opponent's score
           strat (strategy function): Opponent strategy
        
        Returns:
            (float, int): The best rate of winning and the best roll associated with it
    
    '''
    best_roll = 0
    best_rate = apply_rules_counter(score1 + free_bacon(score2), score2, strat, sim_opponent)
    for num_rolls in range(1, 11):
        freqs = get_frequencies(num_rolls)
        total_rate = sum([apply_rules_counter(score1 + points, score2, strat, sim_opponent) * freqs[points] for points in freqs])
        if total_rate > best_rate:
            best_rate = total_rate
            best_roll = num_rolls
    return best_rate, best_roll

@memoize          
def sim_opponent(score1, score2, strat):
    '''Determines the opponent strategy's win rate against an optimal strategy.
       
       Args:
           score1 (int): The opponent's score
           score2 (int): The optimal strategy's score
           strat (strategy function): Opponent strategy
        
        Returns:
            (float, int): The expected win rate and the number of dice rolled
            
    '''
    num_rolls = strat(score1, score2)
    freqs = get_frequencies(num_rolls, score2)
    return sum([apply_rules_counter(score1 + points, score2, strat, sim_counter) * freqs[points] for points in freqs]), num_rolls

@memoize
def apply_rules_counter(score1, score2, strat, next_sim):
    '''Applies the rules of Hog, then returns the expected win rate of Player 1
       See https://cs61a.org/proj/hog_contest/ for more details
       
       Args:
           score1 (int): Player 1's score (Can be either the optimal strategy, or the opponent strategy)
           score2 (int): Player 2's score (The other player)
           strat (strategy function): Opponent strategy
           next_sim (function): The simulation function of the other player
        
        Returns:
            (float, int): The expected win rate for a given pair of scores for Player 1
    
    '''
    if score1 > max_score: return 1
    if is_swap(score1, score2):
        score1, score2 = score2, score1
    return 1 - next_sim(score2, score1, strat)[0]

def clear_memos():
    '''Clears the memos of methods used in learn'''
    expected_frequency.memo = {}
    sim_counter.memo = {}
    sim_opponent.memo = {}
    apply_rules_counter.memo = {}
    apply_rules.memo = {}
    sim_game.memo = {}

def create_counter(strat):
    '''Creates the optimal counter strategy against strat
       
       Args:
           strat (function): The strategy to be countered
        
        Returns:
            function, list, float: The optimal counter strategy against strat, the lookup table used 
                                   by counter_strat, and the counter's win rate when it moves first
    
    '''
    counter_table = []
    for y in range(max_score + 1):
        counter_table.append([0] * (max_score + 1))
        for x in range(max_score + 1):
            counter_table[y][x] = sim_counter(y, x, strat)[1]
    
    def counter(score1, score2):
        '''Optimal counter strategy against strat'''
        return counter_table[score1][score2]
    
    return counter, counter_table, sim_counter(0, 0, strat)[0]

def learn(iterations = 12, seed = lambda x, y: 4):
    '''Creates progressively better strategies by creating counter strategies from previous strategies.
       
       Args:
            iterations (int): The number of counter strategies created
            seed (function): The initial strategy used to create the counter in the first iteration
        
        Returns:
            function, list, float: Function created
    
    '''
    counter = create_counter(seed)
    if iterations:
        print("Iterations Left: {:>2}, Rate: {}".format(iterations, counter[2]))
        clear_memos()
        return learn(iterations - 1, counter[0])
    return counter

def human_strat(score1, score2):
    '''A simple but effective Hog strategy'''
    if is_swap(score1 + free_bacon(score2), score2) and score1 < score2:
        return 0
    if is_swap(score1 + 1, score2) and score1 < score2:
        return 10
    if max_score + 1 - score1 <= free_bacon(score2):
        return 0
    return 8

def baseline(score1, score2):
    '''A basic strategy that always rolls 4'''
    return 4

def roll_dice(num_dice, opp_score):
    '''Rolls num_dice amount of dice and returns appropriate amount of points'''
    if num_dice:
        rolls = [randint(1, 6) for _ in range(num_dice)]
        if 1 in rolls:
            return 1
        return sum(rolls)
    return free_bacon(opp_score)


def play(strat1, strat2, score1 = 0, score2 = 0):
    '''Plays an actual game using random, fair dice'''
    if score1 > max_score: return 1
    score1 += roll_dice(strat1(score1, score2), score2)
    if is_swap(score1, score2): score1, score2 = score2, score1
    return 1 - play(strat2, strat1, score2, score1)

def average_win_rate(strat1, strat2, matches = 1000):
    '''Calculates the average win rate of strat1 for matches amount of games between strat1 and strat2'''
    first_turn  = sum([play(strat1, strat2) for _ in range(matches//2)])
    second_turn = matches//2 - sum([play(strat2, strat1) for _ in range(matches//2)])
    return (first_turn + second_turn)/matches

@memoize
def expected_frequency(strat1, strat2, score1, score2):
    '''Calculates the expected frequency of a turn taking place in a given game.'''
    if score1 == 0:
        if score2 == 0: return 0.5
    if is_swap(score1, score2): score1, score2 = score2, score1
    total_freq = 0
    for i in range(1, 61):
        prev_score2 = score2 - i
        if prev_score2 >= 0:
            num_rolls = strat2(prev_score2, score1)
            freqs = get_frequencies(num_rolls, score1)
            if i in freqs:
                total_freq += expected_frequency(strat2, strat1, prev_score2, score1) * freqs[i]
    return total_freq