from hog_sim import expected_frequency
from PIL import Image
import numpy
from math import pi, atan
import os

def visualize_rate(strat1, strat2, fn, fname):
    '''Creates a visualization of a function relating to a game of Hog, in the form of a 500x500 image.
       5x5 groups of pixels are used to represent a functions output for a given input of scores.
    '''
    fname = os.path.join(os.path.dirname(__file__), 'resources/visualizations/' + fname)
    image_arr = numpy.zeros((100, 100, 3), dtype=numpy.uint8)
    for y in range(100):
        for x in range(100):
            rate = fn(strat1, strat2, y, x)
            image_arr[99 - x][y] = [255 * (1 - rate), 255 * rate, 127]
    img = Image.fromarray(image_arr, 'RGB')
    img = img.resize((500, 500))
    img.save(fname)
    img.close()

def create_strat_wrapper(strat):
    '''Wraps a strategy into a four argument function so that it can be passed into visualize_rate.    
    '''
    def strat_wrapper(s1, s2, score1, score2):
        '''Returns the amount of dice rolled by strat divided by 10.
        '''
        return strat(score1, score2)/10
    return strat_wrapper

def create_adjusted_ef(strat1, strat2, contrast = 5000):
    '''Adjusts the expected_frequency method to display based on whether a turn has an above or below
       average frequency, scaled using atan to fit between 0.0 and 1.0. Larger contrast value makes
       deviation from the mean more pronounced in the visualization.
    '''
    average = 0 
    for x in range(100):
        for y in range(100):
            average += expected_frequency(strat1, strat2, x, y)/10000
    
    def adjusted_ef(ni1, ni2, score1, score2):
        '''Returns an adjusted frequency for a turns appearance for better visualization.'''
        return (atan((expected_frequency(strat1, strat2, score1, score2) - average) * contrast) + pi/2)/pi
    
    return adjusted_ef