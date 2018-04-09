# -*- coding: utf-8 -*-
'''
Created on Mar 3, 2013
    Here we define all the graphic objects to be used by the application (first of all the Nodes)
    TODO: also define the dotted lines that connect the nodes
@author: Vlad
'''
import wx.aui, wx.lib.agw.aui
from wx.lib import platebtn
import wx.lib.scrolledpanel as spanel
import xml.etree.ElementTree as xtree
import sys, os, decorators, time
from xml import etree
from copy import deepcopy
from domain import SchemaRuntimeError
from math import sqrt, tan, atan, pi, copysign


try:
    from agw import aui
    from agw.aui import aui_switcherdialog as ASD
except ImportError:  # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.aui as aui
    from wx.lib.agw.aui import aui_switcherdialog as ASD
#
newid = wx.NewId
# Place for declaring the used IDs
ID_exit_app = newid()  # Exit the app
ID_save_schema = newid()
ID_new_schema = newid()
# import wx.lib.platebtn as platebtn

app_log_filename = 'vwh_wx_log.txt'

_USER_FUNCTIONS = "./user_functions"
if __name__ == "__main__":
    _WORKING_DIRECTORY = os.getcwd()
else:
    _WORKING_DIRECTORY = __file__[0:__file__.rindex(__name__)].rstrip('\\').rstrip('/')
    
class LogDevice(object):
    def log(self, formattedMessage):
        pass

def log(message, source=(None, None, None), level=0):
    tl = time.localtime()
    string = "[%s/%s/%s-%s:%s:%s] %s\t||\t\tSchema:%s\tNode:%s\tPort:%s\n" % \
            (tl.tm_mday, tl.tm_mon, tl.tm_year, tl.tm_hour, tl.tm_min, tl.tm_sec, message, source[0], source[1], source[2])
    try:
        log._device.log(string)
    except:
        print string
    
    
    

class ElementDiscoverer(object):
    """Discovers the functions made available to the user.
        ATM, it searches a directory "./user_functions" for all the .py (and ONLY .py currently) files (including in subfolders).
        without executing any code (TODO), it provides a list of functions to the Application (or whoever instantiates this) for each one 
        of the categories: Input, Output, Processing, Other.
        
        Input functions are those that don't have Input ports (_guiInfo.input ==0).
        Output functions are those that don't have Output ports (_guiInfo.output ==0)
        Processing functions are those that have both input and output ports.
        Other - undefined category.
        
        At present, while this loads all the .py modules, malicious code from inside them might get executed.
        TODO: should find a way to parse the .py modules to eliminate anything that is not a decorated function definition WHILE keeping the 
                "safe" imports. <-SECURITY HOLE
    """
    def __init__(self):
        if not os.path.isdir(_USER_FUNCTIONS): raise RuntimeError("No subdirectory './user_functions' exists inside the current directory. See documentation of gui.ElementDiscoverer")
        self.input_functions = {}
        self.output_functions = {}
        self.processing_functions = {}
        self.other_functions = {}
#        scan for decorated function definitions  
        for func in self.discoverFunctions():
            self._tryAppend(func)
    
    def _tryAppend(self, func):
        """Appends the found function to the proper list
        @param func: a function"""
        if func._guiInfo.input == 0 and func._guiInfo.output != 0:
            self.input_functions[func.__name__] = func
        elif func._guiInfo.input != 0 and func._guiInfo.output == 0:
            self.output_functions[func.__name__] = func
        elif func._guiInfo.input != 0 and func._guiInfo.output != 0:
            self.processing_functions[func.__name__] = func
        else:
            self.other_functions[func.__name__] = func
    @classmethod
    def discoverFunctions(cls, dirname=_USER_FUNCTIONS):
        """Returns a list of properly decorated function objects, loaded from the provided directory
            @param dirname: string -  the directory where to look for functions
            @return: a list of the found functions (all subdirs included)
        A properly decorated function a function decorated with @decorators.guiInfo
        """
        funcs = []
        temp_wd = os.getcwd()
        os.chdir(_WORKING_DIRECTORY)
        for dirdesc in os.walk(dirname):  # (<abs_dir_name>,<subdir_list>,<file_list>)
            sys.path.append(dirdesc[0])
            for filename in [d[0:-3] for d in dirdesc[2] if d.endswith(".py")]:
                try:
                    custom_module = __import__(filename)
                    for member_name in dir(custom_module):
                        member = getattr(custom_module, member_name)
                        if hasattr(member, '__call__') and hasattr(member, decorators.GUI_PROPERTY_NAME):
                            funcs.append(member)
                except ImportError:
                    pass
            sys.path.remove(dirdesc[0])
        os.chdir(temp_wd)
        return funcs


class GuiFrame(wx.Frame):
    """Represents the GUI window of the application."""
    def __init__(self, parent, id_, title='OVIDIS', pos=wx.DefaultPosition, size=wx.Size(800, 800), style=wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER | wx.CLIP_CHILDREN):
        wx.Frame.__init__(self, parent, id_, title, pos, size, style)
        if not _WORKING_DIRECTORY:
            raise RuntimeError("The application can't start because it hasn't been properly called or initialized."\
                               " No working directory has been set.")
        self.schema = None
        self._mgr = wx.aui.AuiManager(self)
        self._elemdisco = ElementDiscoverer()
        self._createMenuBar()
        self._sizer = wx.BoxSizer()
        self._createToolBar()
        self.editMode = False 
#        Add the 3 panels
        self._createTreePanel()
        self.mainPanel = GuiScrolledPanel(parent=self, id=newid(), size=(2000, 2000), style=wx.BG_STYLE_CUSTOM, name="mainPanel")
        self._createStatusPanel()
        
#        tx = wx.TextCtrl(mainPanel, -1, 'asdf', style=wx.TE_CENTER | wx.TE_READONLY)
#        cursor = wx.StockCursor(wx.CURSOR_HAND)
#        tx.SetCursor(cursor)
        # Add the panels to the window (actually the service manager)
        
        self.mainPanel.info = wx.aui.AuiPaneInfo().Name(self.mainPanel.GetName()).Caption(self.mainPanel.caption).Center().MinSize(wx.Size(400, 400))
        self._mgr.AddPane(self.mainPanel, self.mainPanel.info)
        self._mgr.Update()
        
    def _createStatusPanel(self):
        self.statusPanel = wx.Panel(self, name="statusPanel")
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.statusPanel.text = wx.TextCtrl(self.statusPanel, wx.ID_ANY, size=self.statusPanel.GetSize(), style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.statusPanel.text, 1, wx.EXPAND)
        self.statusPanel.SetSizer(sizer)
        
        
        class StatusDevice(LogDevice):
            def __init__(self, textctrl):
                self._textctrl = textctrl
            def log(self, message):
                self._textctrl.AppendText(message)
        log._device = StatusDevice(self.statusPanel.text)
        self.statusPanel.info = wx.aui.AuiPaneInfo().Name(self.statusPanel.GetName()).Caption('Status view').Bottom().Floatable(False).MinSize(wx.Size(200, 200))
        self._mgr.AddPane(self.statusPanel, self.statusPanel.info)
        
    def _createToolBar(self):
        """Creates the toolbar.
        Buttons:
            New schema
            Load schema
            Save schema
            ____________
            Check schema
            Run schema
            Disconnect all nodes """ 
        self.toolbar = aui.AuiToolBar(self, -1, pos=wx.DefaultPosition, size=wx.DefaultSize, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.toolbar.texts = ["New schema", "Load schema", "Save schema", "Run schema", "Check schema", "Disconnect all nodes"]
        self.toolbar.textMappings = {self.toolbar.texts[0]:self._newSchema, self.toolbar.texts[1]:self._loadSchema, self.toolbar.texts[2]:self._saveSchema, self.toolbar.texts[3]:self._runSchema, self.toolbar.texts[4]:self._checkSchema, self.toolbar.texts[5]:self._disconnectSchema}
        def addToolbarButton(frame, wxart, caption):
            bmp = wx.ArtProvider.GetBitmap(wxart, wx.ART_OTHER, wx.Size(16, 16))
            frame.toolbar.AddSimpleTool(wx.ID_ANY, "Check 1", bmp, caption, aui.ITEM_CHECK)
        
        addToolbarButton(self, wx.ART_NEW, self.toolbar.texts[0])
        addToolbarButton(self, wx.ART_FILE_OPEN, self.toolbar.texts[1])
        addToolbarButton(self, wx.ART_FILE_SAVE, self.toolbar.texts[2])
        self.toolbar.AddSeparator()
        addToolbarButton(self, wx.ART_EXECUTABLE_FILE, self.toolbar.texts[3])
        addToolbarButton(self, wx.ART_TIP, self.toolbar.texts[4])
        addToolbarButton(self, wx.ART_ERROR, self.toolbar.texts[5])
        self.toolbar.Realize()
        self._mgr.AddPane(self.toolbar, wx.aui.AuiPaneInfo().Name('test123').Caption("test123 caption").ToolbarPane().Top())
        self.Bind(wx.lib.agw.aui.EVT_AUITOOLBAR_TOOL_DROPDOWN, self._onToolbarClick)
    
    def _createMenuBar(self):    
        mb = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(ID_exit_app, 'Exit')
        mb.Append(file_menu, 'File')
        self.SetMenuBar(mb)
    
    def _createTreePanel(self):
        def buildTreeControl(panel):
            """Creates the wx.TreeCtrl and populates it"""
            def appendSubitems(item, func_list, tree):
                """Appends the individual functions to their corresponding nodes"""
                for name in func_list:
                    tree.AppendItem(item, name, 1)
            tree = wx.TreeCtrl(panel, -1, wx.Point(0, 0), wx.DefaultSize, wx.NO_BORDER | wx.TR_DEFAULT_STYLE)
            root = tree.AddRoot("Elements")
            tree.SetPyData(root, None)
            imglist = wx.ImageList(16, 16, True, 2)
            imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, wx.Size(16, 16)))
            imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, wx.Size(16, 16)))
            tree.AssignImageList(imglist)
        # #        Create the element Tree (the left hand side panel). Places in it all the found functions 
            appendSubitems(tree.AppendItem(root, "Input functions", 0), self._elemdisco.input_functions, tree) 
            appendSubitems(tree.AppendItem(root, "Processing functions", 0), self._elemdisco.processing_functions, tree)
            appendSubitems(tree.AppendItem(root, "Output functions", 0), self._elemdisco.output_functions, tree)
            appendSubitems(tree.AppendItem(root, "Other functions", 0), self._elemdisco.other_functions, tree)
            tree.ExpandAll()
            return tree
        
        self.treePanel = wx.Panel(self)
        self.treePanel.tree = buildTreeControl(self.treePanel)
        self.treePanel.SetSizer(wx.BoxSizer())
        self.treePanel.GetSizer().Add(self.treePanel.tree, 1, wx.EXPAND)
        self.treePanel.info = wx.aui.AuiPaneInfo().Name('Element Tree').Caption('Element Tree').Left().MinSize(wx.Size(300, 200))
        self._mgr.AddPane(self.treePanel, self.treePanel.info)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._addNodeToSchema, self.treePanel.tree)  # , id, id2)
        
    def _dummy(self, event):
        print "the tooltip", event.GetEventObject().GetToolTip().GetTip()

    def _onToolbarClick(self, event):
        """Calls the actual handler specified in the toolbar Mappings""" 
        try:
            self.toolbar.textMappings[event.GetEventObject().GetToolTip().GetTip()](event)
        except NotImplementedError:
            wx.MessageBox("This functionality is not yet implemented", "error") 

    def _newSchema(self, event):
        log("Creating new schema")
        userDialog = wx.TextEntryDialog(self, "Schema name")
        value = None
        if userDialog.ShowModal() == wx.ID_OK:
            value = userDialog.GetValue()
        if self.schema:
            GuiPort.clearRegisteredPorts()
            self.mainPanel.DestroyChildren()
        self.schema = GuiSchema(name=value, panel=self.mainPanel)
        self.editMode = True
        self._refreshMainPanel()
        
    def _refreshMainPanel(self):
        self.mainPanel.updateCaption(self.schema.name)
        paneinfo = self._mgr.GetPane(self.mainPanel.GetName())
        paneinfo.Caption(self.mainPanel.caption)
        self._mgr.Update()
        
    def _loadSchema(self, event):
        log("Loading schema")
        wildcard = "XML Calculation Schema(*.xcs)|*.xcs|"     \
                    "All files (*.*)|*.*"
        loadDialog = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN)

        if loadDialog.ShowModal() == wx.ID_OK:
            paths = loadDialog.GetPaths()
            if len(paths) == 1:
                xfile = open(paths[0], "r")
                try:
                    self.schema = GuiSchema(panel=self.mainPanel, filename=xfile)
                    self._refreshMainPanel()
                    self.editMode = True
                except:
                    log("An error occured by loading the schema. Check the log")
                    raise
                
    def _saveSchema(self, event):
        """Saves the schema to an XML file
            TODO: should pass a file parameter to the schema, to fill the file line by line. Currently the
            whole schema gets turned into a string, which could cause problems for HUGE schemas"""
        log("Saving schema")
        if self.schema:
            wildcard = "XML Calculation Schema (*.xcs)|*.xcs|"     \
                        "All files (*.*)|*.*"
            dlg = wx.FileDialog(self, message="Save the calculation schema as XML file",
                                defaultDir=os.getcwd(),
                                defaultFile="",
                                wildcard=wildcard,
                                style=wx.SAVE | wx.OVERWRITE_PROMPT)
            dlg.SetFilename(self.schema.name)
            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()        
                xschema = self.schema.toXml()
                for path in paths:
                    xfile = open(path, "w")
                    xfile.write(xschema)
                    xfile.close()
                wx.MessageBox(xschema, "the schema as _xtree representation")
            dlg.Destroy()
        else:
            wx.MessageBox("No schema active")
    
    def _promptForModuleName(self):
        if not (hasattr(self.schema, "pyfile") and hasattr(self.schema, "pydir") and hasattr(self.schema, 'moduleName')):
            moduleAsText = self.schema.toPy()
            wildcard = "Python script(*.py)|*.py|"     \
                        "All files (*.*)|*.*"
            dlg = wx.FileDialog(self, message="Save the Python script as...",
                                defaultDir=os.getcwd(),
                                defaultFile="",
                                wildcard=wildcard,
                                style=wx.SAVE | wx.OVERWRITE_PROMPT)
            dlg.SetFilename(self.schema.name)
            if dlg.ShowModal() == wx.ID_OK:
                self.schema.pyfile = dlg.GetPaths()[0]      
                self.schema.pydir = dlg.GetDirectory()  
            fil = open(self.schema.pyfile, "w")
            fil.write(moduleAsText)
            fil.close()
            moduleName = self.schema.pyfile.replace(self.schema.pydir, '')
            moduleName = moduleName[0:moduleName.rindex(".py")].replace('/', '').replace('\\', '')
            self.schema.moduleName = moduleName
            sys.path.append(self.schema.pydir)
        return self.schema.moduleName

    def _runSchema(self, event):
        if self.schema:
            moduleName = self._promptForModuleName()
            try:
                generatedModule = __import__(moduleName)
                self.schema._generatedModule = generatedModule
                generatedModule.Schema.run()
                if generatedModule.Schema.successful:
                    log('Schema executed successfully', source=(self.schema, None, None))
                else:
                    log('Schema failed to execute correctly. Check log file %s for details' % (gui.app_log_filename))
                    raise ImportError(generatedModule.Schema.errors)
            except ImportError, err:
                log('Failed to load the dynamic module' + str(err), source=(self.schema, None, None))
                wx.MessageBox("Something went wrong. Couldn't import the generated module+\n" + str(err))
            except Exception, err:
                log('Schema failed to execute correctly. After closing the application, check log file %s for details' % (app_log_filename))
                raise err 
            
    def _checkSchema(self, event):
        if self.schema and hasattr(self.schema, '_generatedModule'):
            if self.schema._generatedModule.Schema.is_runnable():
                log('The schema seems prepared to run', source=(self.schema, None, None))
            else:
                log('The schema doesn\'t seem ready to run yet. After closing the application, check the %s file for details' % (app_log_filename), source=(self.schema, None, None))
        else:
            moduleName = self._promptForModuleName()
            try:
                generatedModule = __import__(moduleName)
                runnable = generatedModule.Schema.is_runnable()
                if runnable:
                    log('The schema seems prepared to run', source=(self.schema, None, None))
                else:
                    log('The schema doesn\'t seem ready to run yet. After closing the application, check the file %s for details.' % (app_log_filename), source=(self.schema, None, None))
            except ImportError:
                log('The module %s can\'t be generated' % (moduleName), source=(self.schema, None, None))
        
                
    def _disconnectSchema(self, event):
        if self.schema:
            for port in [port for node in self.schema.nodes for port in node.ports ]: 
                port.disconnect()
        
    def _addNodeToSchema(self, event):
        """Fires when the functions in the left hand side panel get double clicked.
            Tries to add the selected function to the GuiSchema (right hand side panel)"""
        if self.editMode:
            pt = event.GetPoint()
            item, _ = self.treePanel.tree.HitTest(pt)
            if item: 
                entire_function_set = {}
                entire_function_set.update(self._elemdisco.input_functions)
                entire_function_set.update(self._elemdisco.other_functions)
                entire_function_set.update(self._elemdisco.output_functions)
                entire_function_set.update(self._elemdisco.processing_functions)
                itemtext = self.treePanel.tree.GetItemText(item)
                self.schema.create_and_add_node(function=entire_function_set[itemtext])
        else:
            wx.MessageBox("Create or load a schema before adding nodes")
        event.Skip()
    def log(self, message, node=None, port=None, level=0):
        raise NotImplementedError("logging not implemented")
        


class GuiPort(object):
    """Represents a GuiPort which belongs to a GuiNode, and can be connected to another node's 
    GuiPort with different iotype"""
    _ports = []  # class property for finding the nodes easier when building the visual links
    def __init__(self, schema, node, label, iotype, linkedPort=None, container=None):
        """  @param schema : GuiSchema
             @param node: GuiNode
             @param label: This port's identifier
             @param iotype: GuiIOObject.INPUT or GuiIOObject.OUTPUT
             @param linkedPort: GuiPort"""
        GuiPort._ports.append(self)
        self.schema = schema
        self.node = node
        self.iotype = iotype
        self.linkedPort = linkedPort
        self.label = label
        self.container = container
        if linkedPort is None:
            self.connected = False
        else:
            self.connected = True
    def __str__(self):
        return self.label
    
    @classmethod
    def clearRegisteredPorts(cls, port=None):
        if port is None:
            cls._ports = []
        else:
            cls._ports.remove(port)
    
    @classmethod
    def createPortName(cls, iotype, number):
        """Returns a port name, created for the specified iotype and number.
        @param iotype: GuiIOObject.INPUT or GuiIOObject.OUTPUT
        @param number: The sequence number of the port"""
        return "%s %i" % (iotype, number + 1)
    
    def connect(self, port):
        """Connects current port to the target port
            @param port: the port with which to make a connection"""
        log("Connecting to node %s, port %s" % (port.node, port), (self.schema, self.node, self))
        self.linkedPort = port
        self.connected = True
        port.linkedPort = self
        port.connected = True
#        GuiPort.createVisualLinks(self.schema)
        self.schema.panel.Refresh()
        self.schema.dirty()
        
    def disconnect(self):
        """Disconnects the current port from its target"""
        if self.is_used():
            log("Disconnecting from %s" % (self.linkedPort), (self.schema, self.node, self))
            self.linkedPort.connected = False
            self.linkedPort.linkedPort = None
            self.linkedPort = None
            self.connected = False
#        GuiPort.createVisualLinks(self.schema)
        self.schema.panel.Refresh()
        self.schema.dirty()
        
    def is_used(self):
        if self.linkedPort is not None:
            return True
        else:
            return False

    @classmethod
    def getTypeNumberTuple(cls, name):
        """Returns a tuple (iotype,number).
        
        @type iotype: GuiIOObject.IOPUT or GuiIOObject.OUTPUT
        @type number: int - the number of the port"""
        try:
            if name.startswith(GuiIOObject.INPUT):
                return (GuiIOObject.INPUT, int(name[name.rindex(' '):]))
            elif name.startswith(GuiIOObject.OUTPUT):
                return (GuiIOObject.OUTPUT, int(name[name.rindex(' '):]))
            else:
                raise RuntimeError("The specified name doesn't specify if the node is of iotype INPUT or OUTPUT")
        except Exception, err:
            raise RuntimeError("Can't parse the given name into a port type and number", err)
    @classmethod
    def createVisualLinks(cls, dc, parentPosition):
        """After all the nodes with all the ports have been created, this creates visual links between the 
        nodes. 
        This method is called on the wx.EVT_PAINT for the schema's container.
        """
        output_ports = [port for port in cls._ports if port.iotype == GuiIOObject.OUTPUT and port.is_used()]
        for port in output_ports:
            x1, y1 = [(abs_pos - par_pos + out_correct) for abs_pos, par_pos, out_correct in zip(port.container.GetScreenPosition().Get(), parentPosition.Get(), port.container.GetSize().Get())]
            x2, y2 = [(abs_pos - par_pos) for abs_pos, par_pos in zip(port.linkedPort.container.GetScreenPosition().Get(), parentPosition.Get())]
            dc.DrawLine(x1, y1, x2, y2)
            try:
                xmid, ymid = (x1 + x2) / 2, (y1 + y2) / 2
                tangent = (y2 - y1) / (x2 - x1)
                angle = 30 * pi / 180 
                xsup = xmid - 20 / sqrt(1 + tan(atan(tangent) + angle) ** 2)
                ysup = ymid + (xsup - xmid) * tan(atan(tangent) + angle)
                xinf = xmid - 20 / sqrt(1 + tan(atan(tangent) - angle) ** 2)
                yinf = ymid + (xinf - xmid) * tan(atan(tangent) - angle)
                dc.DrawLine(xsup, ysup, xmid, ymid)
                dc.DrawLine(xinf, yinf, xmid, ymid)
            except ArithmeticError:
                pass
            except ValueError:
                pass

class GuiPortContainer(platebtn.PlateButton):
    """A container for either one GuiPort, or a collection of GuiPorts (in which case param multiplicity > 1"""
    STYLE_DROPDOWN = platebtn.PB_STYLE_NOBG | platebtn.PB_STYLE_DROPARROW
    STYLE_NO_PORTS = platebtn.PB_STYLE_NOBG | platebtn.PB_STYLE_DEFAULT
    def __init__(self, schema, parent=None, label=None, iotype=None, multiplicity=1, id_=wx.ID_ANY, style=None, *args, **kwargs):
        """@param iotype :GuiIOObject.INPUT or GuiIOObject.OUTPUT
            @param multiplicity: int - Used for MultiInput, to specify how many ports are included in this one control"""
        if iotype != GuiIOObject.INPUT  and iotype != GuiIOObject.OUTPUT:
            raise RuntimeError("The GuiPortContainer must have an iotype specified: Either GuiPortContainer.IOTYPE_IO or GuiPortContainer.IOTYPE_OUT")
        if style is None:  
            style = GuiPortContainer.STYLE_DROPDOWN
        platebtn.PlateButton.__init__(self, parent=parent, id_=id_, label=label, style=style, *args, **kwargs)
        self.schema = schema
        self.iotype = iotype
        self.node = self.GetGrandParent()
        self.multiplicity = multiplicity
        self.ports = []
        for number in xrange(multiplicity):
            if label is None or multiplicity > 1:
                label = GuiPort.createPortName(iotype, number)
            port = GuiPort(schema, self.node, label, iotype, container=self)
            self.ports.append(port)
            self.node.ports.append(port)
        
        self.Bind(wx.EVT_MENU, self._onMenu)
        self.Bind(wx.EVT_ENTER_WINDOW, self._createMenu, self)
        
    def _onMenu(self, event):
        """Forwards the work to ._connect or ._disconnect, depending on what handler is registered in .idMappings for this event ID"""
        try:
            func, args = self.idMappings[event.Id]
            func(*args)
        except KeyError:
            pass
        
    def _connect(self, port, tnode, tport):
        """Connects the current port 'port' with the port 'tport' of node 'tnode'"""
        port.connect(tport)
    
    def _disconnect(self, port):
        """Disconnects the current port from its connection to the target port"""
        port.disconnect()
    
    def _dummy(self, event):
        print "entered GuiPortContainer._dummy"
        event.Skip()
        
    def Destroy(self, *args, **kwargs):
        improbable_result = platebtn.PlateButton.Destroy(self, *args, **kwargs)
        for port in self.ports:
            GuiPort.clearRegisteredPorts(port) 
        return improbable_result
        
    def _createMenu(self, event):
        """Creates a creates a wx.Menu for this object that will enable connecting one of its disconnected ports to another compatible 
        (with differing iotype) disconnected port belonging to a different node.
        If this object has disconnected ports, the submenu "Connect..." will appear. 
        If it has connected ports, the submenu "Disconnct..." will appear. In both cases, if no targets can be 
        found "no available ports" option will appear"""
        def getConnectionTargets():
            """Returns a dictionary of structure {port : { t_node : [t_port]}} where
                port represents own disconnected ports
                t_node - nodes which have compatible disconnected ports
                t_port - the compatible disconnected ports of those particular nodes (t_node)"""
            # The following pieces of code are magic!
            targets = {port : {t_node: [t_port for t_port in t_node.ports if t_port.connected == False and t_port.iotype != port.iotype] for t_node in self.schema.nodes if t_node != port.node} for port in self.ports if port.connected == False}
            return targets
        connectionTargets = getConnectionTargets()
        
        self.idMappings = {}
            
        menu = wx.Menu() 
        portSubmenu = wx.Menu()
        if len(connectionTargets) > 0:
            for port in connectionTargets:
                t_nodeSubmenu = wx.Menu()
                if len(connectionTargets[port]) > 0:
                    for t_node in connectionTargets[port]:
                        t_portSubmenu = wx.Menu()
                        if len(connectionTargets[port][t_node]) > 0:
                            for t_port in connectionTargets[port][t_node]:
                                new_id = wx.NewId()
                                self.idMappings[new_id] = (self._connect, (port, t_node, t_port))
                                t_portSubmenu.Append(new_id, t_port.label)
                        else:
                            t_portSubmenu.Append(wx.ID_ANY, "no available ports")
                        t_nodeSubmenu.AppendSubMenu(t_portSubmenu, t_node.GetName())
                else:
                    t_nodeSubmenu.Append(wx.ID_ANY, "no available nodes")
                portSubmenu.AppendSubMenu(t_nodeSubmenu, port.label)
        else:
            portSubmenu.Append(wx.ID_ANY, "current ports connected")
        menu.AppendSubMenu(portSubmenu, "Connect..")
        
        portSubmenu = wx.Menu()
        ownConnectedPorts = [port for port in self.ports if port.connected]
        if len(ownConnectedPorts) > 0:
            for port in ownConnectedPorts:
                new_id = wx.NewId()
                self.idMappings[new_id] = (self._disconnect, (port,))
                portSubmenu.Append(new_id, port.label)
        else:
            portSubmenu.Append(wx.ID_ANY, "current ports disconnected")
        menu.AppendSubMenu(portSubmenu, "Disconnect..") 
        
        self.SetMenu(menu)
        event.Skip()

class GuiIOObject(wx.Panel):
    INPUT = 'Input'
    OUTPUT = 'Output'
    NONE = ''
    _DEFAULT_STYLE = wx.TE_READONLY | wx.TE_CENTER
    def __init__(self, schema, parent, id_, nrports=0, iotype='', *args, **kwargs):
            wx.Panel.__init__(self, parent, id_, *args, **kwargs)
            self._sizer = wx.BoxSizer(wx.VERTICAL)
            self.iotype = iotype
            self.nrports = nrports
            self.connected = False
            if nrports > 3:
                multiInput = GuiPortContainer(schema, self, "%s :%i ports" % (iotype , nrports), iotype, multiplicity=nrports)  # wx.TextCtrl(self, wx.NewId(), iotype + ': multiple', style=GuiIOObject._DEFAULT_STYLE | wx.TE_RICH2, * args, **kwargs)
                self._sizer.Add(multiInput)
            elif nrports == 0:
                noinput = GuiPortContainer(schema, self, 'No %s ports' % iotype, iotype, style=GuiPortContainer.STYLE_NO_PORTS, multiplicity=nrports)
                noinput.Enable(False)
                self._sizer.Add(noinput)
            else:
                for counter in xrange (nrports):
#                    ioCtrl = wx.TextCtrl(self, wx.NewId(), iotype + str(counter), style=GuiIOObject._DEFAULT_STYLE)
                    ioCtrl = GuiPortContainer(schema, self, "%s %i" % (iotype, counter + 1), iotype)
                    flag = (wx.ALIGN_LEFT if iotype == GuiIOObject.INPUT else wx.ALIGN_RIGHT) | wx.ALL
                    self._sizer.Add(ioCtrl, flag=flag)
            self.SetSizer(self._sizer)
            self.Layout()
                    
                    
class GuiInputObject(GuiIOObject):
    def __init__(self, schema, parent, id_, nrports=0, name=None, *args, **kwargs):
        GuiIOObject.__init__(self, schema, parent, id_, nrports, GuiIOObject.INPUT, name)
        
class GuiOutputObject(GuiIOObject):
    def __init__(self, schema, parent, id_, nrports=0, name=None, *args, **kwargs):
        GuiIOObject.__init__(self, schema, parent, id_, nrports, GuiIOObject.OUTPUT, name)
        
class GuiScrolledPanel(spanel.ScrolledPanel):
    def __init__(self, *args, **kwargs):
        spanel.ScrolledPanel.__init__(self, *args, **kwargs)
        self.SetSizer(GuiSchemaSizer())   
        self.SetupScrolling()         
        self.caption = "No active schema - Create a new schema or load one "
#        wx.FutureCall(2000, self.DrawLine)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
#        self.DrawLine()

#        self.Centre()
#        self.Show()

    def DrawLine(self):
        dc = wx.ClientDC(self)
        dc.DrawLine(50, 60, 190, 160)
#        self.
    def OnChildFocus(self, *args, **kwargs):
        self.Layout()
        self.AdjustScrollbars()
        return spanel.ScrolledPanel.OnChildFocus(self, *args, **kwargs)

    def updateCaption(self, caption):
        self.caption = caption
        
    def OnPaint(self, event):
        some_result = spanel.ScrolledPanel.OnPaint(self, event)
        dc = wx.PaintDC(self)
        
        dc.BeginDrawing()
        GuiPort.createVisualLinks(dc, self.GetScreenPosition())
        dc.EndDrawing()
        return some_result 
        
        
class GuiNode(wx.Panel):
    '''This represents the Gui correspondent of the Schema Node.
    The default representation of this object is:
     ___
    |___\    <-Header - contains the name of the node AND a dropdown for Pausing, (Starting?), Stopping, Resuming a node.
    |___\    <-Input Object frame (where the input ports are shown)
    |___\    <-ID/Info frame (where the name and other info is shown
    |___\    <-Parameter Object - where the parameters can be put in by the users
    |___\    <-Output Object frame (for the output ports)
    '''
    _current_number = 1
    def __init__(self, schema, id_, function, name=None, current_number= -1, *args, **kwargs):
        """ @param schema: GuiSchema
            @param nrInPorts: int - number of input ports
            @param nrOutPorts: int -output ports
            @param function: a callable, previously properly decorated with decorators.guiInfo
        """
        if name is None:
            name = "N%i: %s" % (GuiNode._current_number, function.__name__)
            GuiNode._current_number += 1
        elif current_number < 0:
            raise InitializationException("When providing a name for the node, the current number must also be provided")
        else:
            GuiNode._current_number = current_number + 1
        
        wx.Panel.__init__(self, schema.panel, id_, name=name, style=wx.BORDER_DOUBLE, *args, **kwargs)
        self.ports = []
        self.schema = schema
        self.function = function
        if self.function._guiInfo.params is not None:
            if hasattr(self.function._guiInfo.params, '__iter__'):
                self.params = {pname:None for pname in self.function._guiInfo.params.keys() }
            else:
                self.params = {self.function._guiInfo.params : None}
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._createHeader(name)
        self._createInObj(function._guiInfo.input)
        self._createParameterObj()
        self._createOutPbject(function._guiInfo.output)
        self.SetSizer(self._sizer)
        self._sizer.Fit(self)
        self.SetBackgroundColour('#DDDDDD')
        
    @classmethod
    def getCurrentNumber(cls, nodeName=None):
        """Returns the current node number, if no parameter is provided, or the number of that node, if param is provided.
        
        Implementation must be changed if the numbering system changes"""
        if nodeName:
            return int(nodeName.lstrip('N').split(':')[0])
        
    def _createInObj(self, nrports):
        self.inobj = GuiInputObject(self.schema, self, wx.NewId(), nrports)
        self._sizer.Add(self.inobj, 0, wx.ALL | wx.ALIGN_LEFT, 5)
    
    def _createHeader(self, name):
        self.header = platebtn.PlateButton(self, wx.NewId(), name, style=platebtn.PB_STYLE_SQUARE)  # | platebtn.PB_STYLE_DROPARROW)
        self.header._tooltip = wx.ToolTip(name + '\nYou can drag and drop this item.')
        self.header._emptytooltip = wx.ToolTip('')
        self.header.SetToolTip(self.header._tooltip)
        self.header.SetBackgroundColour('#999999')
        self._sizer.Add(self.header)
#        Set cursor
#        cursor = wx.StockCursor(wx.CURSOR_HAND)
#        self.header.SetCursor(cursor)
#        Add Menu to the Header
        menu = wx.Menu()
        id_remove = wx.NewId()
        menu.Append(id_remove, "Remove node")
        self.header.SetMenu(menu)
#        Define events
        self.header.GetEventHandler().Bind(wx.EVT_LEFT_DOWN, self._onMoveBegin, self.header)
        self.header.GetEventHandler().Bind(wx.EVT_LEFT_UP, self._onMoveEnd, self.header)
        self.header.GetEventHandler().Bind(wx.EVT_MOTION, self._onMotion)
        self.header.GetEventHandler().Bind(wx.EVT_LEAVE_WINDOW, self._onMoveEnd)
#        Events
        self.Bind(wx.EVT_MENU, self._remove, id=id_remove)
        
    def _createParameterObj(self):
        '''If the node.function._guiInfo.parameters has parameters specified, this method creates a control through which they can be provided.
        This has to set a dummy menu, so t hat the dropdown arrow appears.
        '''
        if self.params:
            if len(self.params) > 1:
                label = 'parameters...'
            else:
                label = self.params.keys()[0]
            self.paramobj = platebtn.PlateButton(self, wx.NewId(), label=label, style=platebtn.PB_STYLE_DEFAULT)
            self.paramobj.SetMenu(wx.Menu())  
            self._sizer.Add(self.paramobj)
            self.paramobj.Bind(wx.EVT_ENTER_WINDOW, self._createParamsMenu, self.paramobj)
            self.paramobj.Bind(wx.EVT_MENU, self._onParamMenu)
            
    def _supplyParam(self, param):
        param_type = self.function._guiInfo.params[param]
        def getUserInput():
            dlg = wx.TextEntryDialog(self, 'Provide a value for the parameter "%s":' % param)
            if dlg.ShowModal() == wx.ID_OK:
                return dlg.GetValue()
        try:
            value = None
            if param_type == decorators.PARAM_FILE:
                loadDialog = wx.FileDialog(self, message="Choose a file", defaultDir=os.getcwd(),
                                           wildcard="All files (*.*)|*.*", style=wx.OPEN)
                if loadDialog.ShowModal() == wx.ID_OK:
                    paths = loadDialog.GetPaths()
                    if len(paths) == 1:
                        self.params[param] = value = paths[0].replace('\\', '/')
            elif param_type == decorators.PARAM_STRING:
                self.params[param] = value = getUserInput()
            elif param_type == decorators.PARAM_INT:
                self.params[param] = value = int(getUserInput())
            log('Value set for parameter "%s" to "%s".' % (param, value), (self.schema, self, None))
        except:
            wx.MessageBox("Error. Incorrect input? Value was not set.")
    
    def _clearParam(self, param):
        self.params[param] = None
    
    def _onParamMenu(self, event):
        method, param = self.paramobj.idMappings[event.GetId()]
        method(param)
        event.Skip()
        
    def _createParamsMenu(self, event):
        '''Creates the menu for the params object.
        
        This has to be created each time on the event wx.EVT_ENTER_WINDOW because it can look different if parameters were already supplied.
        In order to handle the events, this creates a mapping between the ids of the menu items and (the parameter keys - self.params.keys(), the handler method (to supply, or discard value))
        '''
        self.paramobj.idMappings = {}
        menu = wx.Menu()
        if len(self.params) == 1:
            if not any(self.params.values()):
                id_supply_1 = wx.NewId()
                menu.Append(id_supply_1, "supply value")
                self.paramobj.idMappings[id_supply_1] = (self._supplyParam, self.params.keys()[0])
            else:
                id_clear_1 = wx.NewId()
                menu.Append(id_clear_1, 'clear value')
                menu.Append(wx.NewId(), self.params.keys()[0])
                self.paramobj.idMappings[id_clear_1] = (self._clearParam, self.params.keys()[0])
        else:
            for param in self.params.keys():
                subMenu = wx.Menu()
                if self.params[param] is None:
                    id_supply_1 = wx.NewId()
                    subMenu.Append(id_supply_1, "supply value")
                    self.paramobj.idMappings[id_supply_1] = (self._supplyParam, param)
                else:
                    id_clear_1 = wx.NewId()
                    subMenu.Append(wx.NewId(), str(self.params[param]))
                    subMenu.Append(id_clear_1, "clear value")
                menu.AppendSubMenu(subMenu, str(param))
        self.paramobj.SetMenu(menu)
        event.Skip()
                    
            
        
    
    def _createOutPbject(self, nrports):
        self.outobj = GuiOutputObject(self.schema, self, wx.NewId(), nrports)
        self._sizer.Add(self.outobj, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

    def _onMoveBegin(self, event):
        # deactivate tooltip when move has started
        self.header._tooltip.Enable(False)
        x, y = self.ClientToScreen(event.GetPosition())
        originx, originy = self.GetPosition()
        dx = x - originx
        dy = y - originy
        self.delta = ((dx, dy))
        self._isMoving = True
        event.Skip()
    
    def _onMoveEnd(self, event):
        # Reactivate the tooltip once move has ended
        self.header._tooltip.Enable(True)
        self._isMoving = False
        self.Refresh()
        self.schema.dirty()
        self.GetParent().FitInside()
#        GuiPort.createVisualLinks(self.schema)
        self.schema.panel.Refresh()
        event.Skip()
        

    def _onMotion(self, event):
        if hasattr(self, '_isMoving') and self._isMoving:
            x, y = self.ClientToScreen(event.GetPosition())
            fp = (x - self.delta[0], y - self.delta[1])
            self.Move(fp)
        event.Skip()
    
    def discard(self):
        self.schema.remove_node(self, False)
        self.Destroy()
            
    def _remove(self, event):
        self.discard()
                    
    def _dummy(self, event):
        print "dummy"
        event.Skip()
    
    def __str__(self):
        return self.GetName()
        
    def Destroy(self, *args, **kwargs):
        for port in self.ports:
            port.disconnect()
        return wx.Panel.Destroy(self, *args, **kwargs)
    
    def setParam(self, name, value):
        log('Setting parameter \'%s\' to \'%s\' ' % (name, value), source=(self.schema, self, None))
        self.params[name] = value
    
        
class GuiDirection(object):
    def __init__(self, down=None, right=None):
        if down is None and right is None:
            raise ValueError("A direction must point to either up, down, left or right, or any of the diagonals.")
        self.down = down
        if down is not None:
            self.up = not down
        else:
            self.up = down
        self.right = right
        if right is not None:
            self.left = not right
        else:
            self.left = right
            
DIRECTION_UP = GuiDirection(False)
DIRECTION_DOWN = GuiDirection(True)
DIRECTION_LEFT = GuiDirection(right=False)
DIRECTION_RIGHT = GuiDirection(right=True)

class GuiLinkingLine(wx.Panel):
    """This class represents the line that will connect an output port of a node with an input port of another node.
    
    Technical: a wx.Panel in which multiple GuiArrowLine are drawn, united head to bottom.
    """
    def __init__(self, parent, id_, origin, destination, *args, **kwargs):
        wx.Panel.__init__(self, parent, id_, *args, **kwargs)

class GuiArrowLine(wx.StaticLine):
    """Represents a line (horizontal or vertical, with an arrow in the middle, indicating a direction
    @param direction: GuiDirection
    """
    def __init__(self, parent, id_, pos, size, direction , *args, **kwargs):
        wx.StaticLine.__init__(self, parent, id_, pos=pos, size=size, *args, **kwargs)
        self.direction = direction
        if self.Size.x == self.Size.y:
                raise ValueError('Width and height components of the size must be different.')
        if self.IsVertical():
            if self.direction.up:
                self.bmap = wx.Bitmap("./icons/arrow_up.bmp", wx.BITMAP_TYPE_ANY)
            else:
                self.bmap = wx.Bitmap("./icons/arrow_down.bmp", wx.BITMAP_TYPE_ANY)
        else:
            if self.direction.right:
                self.bmap = wx.Bitmap("./icons/arrow_right.bmp", wx.BITMAP_TYPE_ANY)
            else:
                self.bmap = wx.Bitmap("./icons/arrow_left.bmp", wx.BITMAP_TYPE_ANY)
        self.staticbmap = wx.StaticBitmap(parent, wx.NewId(), self.bmap, pos=self._getImagePos())
    
    def _getImagePos(self):
        posx, posy = self.GetPositionTuple()
        sizex, sizey = self.GetSizeTuple()
        bmapsizex, bmapsizey = self.bmap.GetSize().Get()
        self.bmap.GetSize().Get()
        
        return (posx + sizex / 2 - bmapsizex / 2, posy + sizey / 2 - bmapsizey / 2)
            
    
    def IsVertical(self):
        if self.Size.y > self.Size.x:
            return True
        else:
            return False

class GuiSchemaSizer(wx.PySizer):
    """ This is a Sizer especially created for ScrolledPanel's. It allows the children of the panel to be placed freely inside it,
    and only sets the size of the panel to be large enough to accomodate all children.
    """
    def __init__(self, *args, **kwargs):
        wx.PySizer.__init__(self, *args, **kwargs)
    def CalcMin(self):
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
    
class GuiSchema(object):
    """The GUI object that corresponds to the actual calculation schema"""
    def __init__(self, name=None, panel=None, filename=None):
        if name in ("", None):
            name = "Untitled"
        if panel is None:
            raise RuntimeError("The GuiSchema needs to have a panel attributed to it, so that it can add the")
        else:
            self.panel = panel
        self.nodes = []
        if not filename:
            self.name = name
        else:
            self._fromXML(filename)
        self._dirty = False
        
    
    def create_and_add_node(self, function=None, name=None, current_number= -1):
        """Creates a node with the specified properties and adds it to the Schema's node list
        @param function: a function argument (function properly decorated with decorators.guiInfo
        @param name: [optional] the name of the node to be created. If not given, it's constructed from the function name
        @param current_number: [optional][depends on: param name] If name is given, this must also be given. It's used when creating new nodes (so there can be more nodes with the same function) 
        """
        if function:
            log("Adding a new node of type %s" % (function.__name__), (self, None, None))
            node = GuiNode(self, wx.NewId(), function, name, current_number)
            self.nodes.append(node)
            self.dirty()
#            GuiPort.createVisualLinks(self)
            self.panel.Refresh()
            return node
        else:
            raise InitializationException("Can't create a node with no corresponding function")
    
    def _fromXML(self, xmlfile):
        """loads the schema from the XML file.
        Don't use this directly, use the constructor, specifying the filename
        Doesn't return anything, it just loads the properties from the _xtree file to the current object, 
        destroying all previous information the schema used to have 
        @param xmlfile: the _xtree file"""
        for node in list(self.nodes):
            self.remove_node(node)
        xschema = xtree.parse(xmlfile)
        user_functions = ElementDiscoverer.discoverFunctions()
        try:
            for elem in xschema.getiterator():
                if elem.tag == 'schema':
                    self.name = elem.attrib['name']
                if elem.tag == 'node':
                    matching_functions = [func for func in user_functions   if func.__name__ == elem.attrib['function'] \
                                                                            and func.__module__ == elem.attrib['module'] \
                                                                            and func.func_code.co_filename.replace('\\', '/') == elem.attrib['file']]
                    if len(matching_functions) == 1:
                        current_name = elem.attrib['name']
                        current_number = GuiNode.getCurrentNumber(current_name)
                        currentNode = self.create_and_add_node(matching_functions[0], current_name, current_number)
                        currentNode.SetPosition((int(elem.attrib['posx']), int(elem.attrib['posy'])))
                    else:
                        raise InitializationException("The functions required for creating a node don't match the loaded file."\
                                                  "\nRequired function : %s\nRequired module : %s\nRequired file : %s"\
                                                  "\nFound %i functions matching." % (elem.attrib['function'], \
                                                    elem.attrib['module'], elem.attrib['file'], len(matching_functions)))
                if elem.tag == 'param':
                    paramVal = None
                    try:
                        paramVal = elem.attrib['value']
                    except KeyError:
                        pass
#                    currentNode.params[elem.attrib['name']] = paramVal
                    currentNode.setParam(elem.attrib['name'], paramVal)
                    if currentNode.function._guiInfo.params[elem.attrib['name']] == decorators.PARAM_INT:
                        currentNode.params[elem.attrib['name']] = None if paramVal is None else int(paramVal)
                        
            for elem in xschema.getiterator():  # better to do the iteration 2  times in case the of the nodes and conections changes
                if elem.tag == 'conn':
                    source_node_ports = [(node, port)for node in self.nodes for port in node.ports if node.GetName() == elem.attrib['node1'] and port.label == elem.attrib['port1']]
                    dest_node_ports = [(node, port) for node in self.nodes for port in node.ports if node.GetName() == elem.attrib['node2'] and port.label == elem.attrib['port2']]
                    if len(source_node_ports) == len(dest_node_ports) == 1:
                        _, port1 = source_node_ports[0]
                        _, port2 = dest_node_ports[0]
                        port1.connect(port2)
                    else:
                        raise InitializationException("The connection between 2 ports couldn't be created."\
                                                   "\nSource node: %s \nSource port: %s"\
                                                   "\nTarget node: %s\nTarget port: %s"\
                                                   "\nMatching source(node,port) found: %i"\
                                                   "\nMatching destination(node,port) found: %i"\
                                                   % (elem.attrib['node1'], elem.attrib['port1'], \
                                                     elem.attrib['node2'], elem.attrib['port2'], \
                                                     len(source_node_ports), len(dest_node_ports)))
                    
#            GuiPort.createVisualLinks(self)
            self.panel.Refresh()
        except Exception, exc:
            raise InitializationException("The schema couldn't be loaded", exc)
                
        
        
        
    
    def remove_node(self, node, discard=True):
        """ONLY use this when removing nodes """
        log("Removing node", (self, node, None))
        self.nodes.remove(node)
        if discard:
            node.discard()
        self.dirty()
    
    def dirty(self):
        """Dirties the schema - marks it as having been changed"""
        self._xtree = None
        self._pyscript = None
        self._dirty = True
        
    def __str__(self):
        return self.name
    
    def toXml(self):
        """ Serializes the Schema to an XML representation 
        Example: 
        <schema name="Name">
            <nodes>
                <node name="Name" posx="32" posy="43" file="File" module="Name" function="Name" input="1" output="0">
                    <param name="name" value="value" />
                </node>
                ...
            </nodes>
            <connections>
                <connection node1="Name" port1="name" node2="Name" port2="Name"/>
                ...
            </connections>
        </schema>
        
        TODO:
            -should perhaps include the hash of the function in the node xml representation (not the input and output ports) 
        """
        xschema = xtree.Element("schema", {'name':self.name})
        xnodes = xtree.Element("nodes")
        for node in self.nodes:
            xnode = xtree.Element('node', {'name':      node.GetName(), \
                                           'posx':      str(node.GetPosition().Get()[0]), \
                                           'posy':      str(node.GetPosition().Get()[1]), \
                                           'file':      str(node.function.func_code.co_filename).replace('\\', '/'), \
                                           'module':    str(node.function.__module__), \
                                           'function':  str(node.function.__name__), \
                                           'input':     str((len([p for p in node.ports if p.iotype == GuiIOObject.INPUT]))), \
                                           'output':    str(len([p for p in node.ports if p.iotype == GuiIOObject.OUTPUT]))})
            if hasattr(node, 'params'):
                for key in node.params.keys():
                    xparam = xtree.Element("param", {'name':key})
                    paramVal = node.params[key]
                    if paramVal is not None:
                        xparam.attrib['value'] = str(paramVal)  
                    xnode.append(xparam)
            xnodes.append(xnode)
        xschema.append(xnodes)
        # create the dict of tuples {(node1,port1) :(node2,port2),...} that only counts a connection once
        connections = {}
        xconnections = xtree.Element("connections")
        for node, port in [(port.node, port) for node in self.nodes for port in node.ports if port.connected]:
            key = (str(node), str(port))
            if not (key in connections.keys() + connections.values()):
                connections[key] = (str(port.linkedPort.node), str(port.linkedPort))
        for conn in connections.keys():
            xconn = xtree.Element("conn", {"node1":conn[0], "port1":conn[1], \
                                          "node2":connections[conn][0], \
                                          "port2":connections[conn][1]})
            xconnections.append(xconn)
        xschema.append(xconnections)
        #
        self._xtree = etree.ElementTree.ElementTree(xschema)
        import StringIO as sio
        filebuffer = sio.StringIO()
        self._xtree.write(filebuffer, encoding=sys.getdefaultencoding(), xml_declaration=True)
        result = filebuffer.getvalue()
        filebuffer.close()
        self._dirty = False
        return result
    
    def toPy(self):
        """Creates a .py script that when run or loaded will create the Object Model for the current Schema
        @return: str. The string to be written to the .py file"""
        try:
            if not self._xtree:
                self.toXml()
            os.chdir(_WORKING_DIRECTORY)
            pystr = "# -*- coding: utf-8 -*-\n"\
                    "\'\'\'Generated code - isn't it wonderful?\n\n"\
                    "Please don't modify this file. It will be generated each time\n"\
                    "from the %s.xcs file, created with the graphical tool\n\n" % (self.name)
            pystr += "Please note that in order for this file to be executed from outside of the visual tool,\n"\
                     "the paths of domain.py and lib.py will have to be included the list sys.path\n\n"
            pystr += "USAGE:\nimport %s\n" % (self.name)
            pystr += "%s.Schema.run()\'\'\'\n\n" % (self.name)
                    
            pystr += "import domain,lib\n"\
                    "reload(domain)\n\n"
            for elem in self._xtree.getiterator():
                if elem.tag == 'schema':
                    pystr += "Schema = domain.Schema('%s',%s)\n\n" % (self.name, id(self))
                if elem.tag == 'nodes':
                    pystr += "#Defining the Schema structure\n"
                if elem.tag == 'node':
                    pystr += "newNode = Schema.create_and_add_node(name='''%s''',function=lib.importFunc('''%s''','''%s''','''%s'''))\n"\
                            % (elem.attrib['name'], elem.attrib['function'], elem.attrib['module'], elem.attrib['file'])
                    for portNr in range(int(elem.attrib['input'])):
                        pystr += "newNode.create_and_add_port(name='''%s''',ptype=domain.Port.IN)\n" % (GuiPort.createPortName(GuiIOObject.INPUT, portNr))
                    for portNr in range(int(elem.attrib['output'])):
                        pystr += "newNode.create_and_add_port(name='''%s''',ptype=domain.Port.OUT)\n" % (GuiPort.createPortName(GuiIOObject.OUTPUT, portNr))
                if elem.tag == 'param':
                    try:
                        paramValue = elem.attrib['value']
                    except KeyError:
                        paramValue = None
                    pystr += "newNode.setParam(name='''%s''',value='''%s''')\n" % (elem.attrib['name'], paramValue)
                if elem.tag == 'connections':
                    pystr += "\n#Defining a connection\n"
                if elem.tag == 'conn':
                        pystr += "node1 = Schema.findNodeByName('''%s''')\n" % (elem.attrib['node1'])
                        pystr += "port1 = node1.findPortByName('''%s''')\n" % (elem.attrib['port1'])
                        pystr += "node2 = Schema.findNodeByName('''%s''')\n" % (elem.attrib['node2'])
                        pystr += "port2 = node2.findPortByName('''%s''')\n" % (elem.attrib['port2'])
                        pystr += "if port1 != None and port2 != None:\n"\
                                 "    port1.connect(port2)\n\n"
            pystr += "try:\n"\
                    "    del node1,node2,port1,port2\n"\
                    "except NameError:\n"\
                    "    pass"
            return pystr
        except Exception, err:
            raise RuntimeError("Error generating the .py script", err)
        
        
class InitializationException(Exception):
    pass
    
if __name__ == '__main__':
    import gui
    gui.start_module()
