# -*- coding: utf-8 -*-
'''
Created on Feb 10, 2013

@author: Vlad
'''
import guiobjects, wx


    
def start_module():
    f = open(guiobjects.app_log_filename, mode='w')
    f.close()
    app = wx.App(redirect=True, filename=guiobjects.app_log_filename)
    frame = guiobjects.GuiFrame(None, -1)
    frame.Maximize()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    start_module()
