import wx
import wx.aui
import wx.lib.scrolledpanel

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, size=(303, 300), *args, **kwargs)
        self.mgr = wx.aui.AuiManager(self)
        
#        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self)
#        self.panel.sizer = GUISchemaSizer()  # wx.FlexGridSizer(vgap=4, hgap=4)
#        self.panel.SetSizer(self.panel.sizer)
#        sitem1 = self.panel.sizer.Add(wx.Button(self.panel, -1, "lol1", pos=(50, 200), name="lol1"))
#        sitem2 = self.panel.sizer.Add(wx.Button(self.panel, -1, "lol2", name="lol2"))
#        button = wx.Button(self.panel, -1, "lol3", pos=(1200, 300), name="lol3")
#        sitem2 = self.panel.sizer.Add(button )
#        button.SetPosition((100,200))
#        
#        self.panel.SetupScrolling()
#        self.Layout()
        panel = wx.Panel(self,wx.NewId(),name='Panel1',size = self.GetSize())
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        text = wx.TextCtrl(panel,wx.NewId(),"mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm",\
                           size=panel.GetSize(),style=wx.TE_MULTILINE| wx.TE_READONLY)
        text.write("lkjh\n")
        text.AppendText("ppp\n\rpppppppppppppkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
#        text.
        text.write("123123123")
        sizer.Add(text)
        panel.FitInside()
#        text.Enable(False)
        
        self.mgr.AddPane(panel, wx.aui.AuiPaneInfo().Caption(panel.GetName()))
        self.mgr.Update()


class MyApp(wx.App):
    def __init__(self, *args, **kwargs):
        f = 'testing_py.txt'
        filename = open(f, "w")
#        f.open()
        filename.close()
        wx.App.__init__(self, redirect=True, filename=f)
    def OnInit(self):
        frame = MyFrame(None, -1, '07_wxaui.py')
        frame.Show()
        self.SetTopWindow(frame)
        return 1

class GUISchemaSizer(wx.PySizer):
    def __init__(self, *args, **kwargs):
        wx.PySizer.__init__(self, *args, **kwargs)
    def CalcMin(self):
        print "calcmin"
#        return self.GetContainingWindow().getSize()
#        I know this thing can be coded in 1 line, but let's not kid ourselves... someone has to understand it later too...maybe not
        maxx, maxy = minx, miny = maxw, maxh = minw, minh = (0, 0)
        for item in self.GetContainingWindow().GetChildren():
            actw, acth = item.GetSize().Get()
            if maxw < actw: maxw = actw
            if maxh < acth: maxh = acth
            if minw > actw: minw = actw
            if minh > acth: minh = acth
            actx, acty = item.GetPosition().Get()
            if maxx < actx: maxx = actx
            if maxy < acty: maxy = acty
            if minx > actx :minx = actx
            if miny > acty: miny = acty 
        retsize = wx.Size((maxx - minx + maxw - minw), (maxy - miny + maxh - minh))
        return retsize 
    
#    def RecalcSizes(self):    #This might be needed?

def getdirs(currentDir):
    """ returns the names of all the directories under the given currentDir, where the user has access"""
    import os
    try:
        currentDir = currentDir.replace('\\','/')
        if not currentDir.endswith('/'): currentDir += '/'
        dirs = [ (currentDir + d) for d in os.listdir(currentDir) if os.path.isdir(currentDir + d)]
        if len(dirs) != 0:
            subdirs = []
            for d in dirs:
                subdirs.extend(getdirs(d))
            dirs.extend(subdirs)
        return dirs
    except:
        return []



import xml.etree.ElementTree as et

root = et.Element('root')

root.append(et.Element("child"))

et.ElementTree(root)













if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
