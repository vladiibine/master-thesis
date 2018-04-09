'''
Created on Apr 3, 2013

@author: Vlad
'''
import decorators, numpy

@decorators.guiInfo(1,1)
def square_matrix(x):
    return (numpy.matrix(x)**2).tolist()

@decorators.guiInfo(2,1)
def sumsquares_dummy(x,y):
    return x*x + y*y

@decorators.guiInfo(2, 1)
def sum_matrix(x,y):
    return (numpy.matrix(x)+numpy.matrix(y)).tolist()