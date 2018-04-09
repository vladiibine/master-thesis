'''
Created on Apr 3, 2013

@author: Vlad
'''
import decorators

@decorators.guiInfo(1,1)
def transpose_matrix(x):
    return zip(*x)
	
#1 2 3
#2 3 4
#4 4 3

#1 2 4
#2 3 4
#3 4 3