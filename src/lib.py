'''
Created on Apr 14, 2013

@author: Vlad
'''
import sys,os

def importFunc(funcName,moduleName,fileName):
    '''Imports the function specified and returns it'''
    dirName = fileName[0:fileName.rindex(moduleName)].rstrip('/').rstrip('\\')
    moduleAbsolutePath = "%s/%s"%(os.getcwd(),dirName)
    sys.path.append(moduleAbsolutePath)
    try:
        cust_module = __import__(moduleName)
        return getattr(cust_module,funcName)
    finally:
        sys.path.remove(moduleAbsolutePath)
