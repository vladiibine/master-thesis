'''
Created on Apr 3, 2013

@author: Vlad
'''
import decorators, csv

@decorators.guiInfo(1, 0, {'filename':decorators.PARAM_FILE})
def matrix_to_csv(filename, inputList):
    f = open(filename, 'w')
    writer = csv.writer(f)
    writer.writerows(inputList)
    f.close()
