'''
Created on Apr 3, 2013

@author: Vlad
'''
import decorators, csv

@decorators.guiInfo(1, 0)
def dummy_output(x):
    pass

@decorators.guiInfo(6, 1)
def multiinput_returns_1(x1, x2, x3, x4, x5, x6):
    return 1

@decorators.guiInfo(0, 1, {'filename':decorators.PARAM_FILE})
def file_to_string_list(filename=None):
    '''@deprecated: 
    Reads the lines of text from a file and returns them as strings.
    
    Each line in the text file is a string inside the returned list.'''
    f = open(filename, 'r')
    result = f.readlines()
    f.close()
    return result

@decorators.guiInfo(0, 1, {'filename':decorators.PARAM_FILE})
def float_matrix_from_csv(filename):
    '''Reads the given .csv file and returns a 2D array of floats corresponding to its structure'''
    f = open(filename)
    result = list(csv.reader(f))
    result = [[float(elem) for elem in strings] for strings in result]
    f.close()
    return result
    