# -*- coding: utf-8 -*-
import pp, multiprocessing

#
registered_modules = ('decorators', 'csv', 'numpy','scipy')

# Generates a type
def enum(typename, **props):
    return type(typename, (object,), props)

class Schema(object):
    __idseed = 0
    def __init__(self, name=None, uid=None):
        
        self.nodes = []
        if uid is None:
            # Non thread-safe automatic ID generation
            self.name = Schema.__idseed
            Schema.__idseed += 1
        else:
            self.name = uid
        self.name = name
        self.result = None
        self.jobServer = pp.Server()
        self._lock = multiprocessing.Lock()
        self._event = multiprocessing.Event()
        self._jobsDone = 0
        self._errors = []
        self.successful = False
    
    def __repr__(self):
        return "Schema obj: %s;" % self.name
        
    def findNodeByName(self, nodeName):
        try:
            result = [node for node in self.nodes if node.name == nodeName]
            if len(result) == 1:
                return result[0]
            elif len(result) == 0:
                return None
            else:
                raise RuntimeError("The search for node name '%s' returned %i results." % (nodeName, len(result)))
        except Exception, err:
            raise RuntimeError("Node couldn't be found", err)
    
    def run(self):
        '''
        Starts the calculation process for this Schema.
        
        This starts (requests from the GlobalThreadManager) as many threads as there are input nodes.
        Each thread runs a caculation from an input node towards the next Input port.
        Each node's collection of ports will have a Thread Manager, who only invokes that node's 'run' method when all the input nodes have been
            satisfied (all the thread managers of the Nodes to which it is connected have reported "JOB DONE" and the results of the previous
            calculations are present.
        '''
        if self.is_runnable():
            startNodes = self._get_start_nodes()
            for node in startNodes:
                node.run_initial()
            self.successful = True
        else:
            raise SchemaRuntimeError("The schema is not ready for running. Check i/o nodes, connections, parameters",self._errors)
        
    def is_runnable(self):
        # Determine if there is at least 1 node with only OUT ports
        # 1: determine nodes with at least 1 port
        valid = False
        start_nodes = self._get_start_nodes()
        if len(start_nodes) > 0:
            valid = True
        else:
            err = SchemaConfigurationError('The Schema is not runnable because it contains no starting nodes')
            self._errors.append(err)
        # Determine whether all the machines for the nodes are reachable
        valid = valid and all([node.is_reachable() for node in self.nodes])
        #Determine whether all the registered modules are installed
        for moduleName in registered_modules:
            try:
                __import__(moduleName)
            except ImportError, err: 
                self._errors.append(err)
                valid = False
        
        return valid

    def _get_start_nodes(self):
        '''Returns the ports that don't have any Input ports (meaning they are themselves a source of output 
            (eg. file Nodes)'''
        return [node for node in self.nodes if node.ports is not None and len([port for port in node.ports if port.type is Port.IN]) == 0 ]
        
        
    def get_error_stack(self):
        pass
    def create_and_add_node(self, name=None, function=None):
        _newNode = Node(parent=self, name=name, function=function) 
        self.nodes.append(_newNode)
        return _newNode
    
    def add_Node(self, node=None):
        if node: self.nodes.append(node)
        
    def notify_job_done(self):
        self._lock.acquire()
        self._jobsDone += 1
        self._event.set()
        self._lock.release()
    
    def wait_for_all_nodes(self):
        while True:
            self._event.wait(1)
            self._lock.acquire()
            if self._jobsDone == len(self.nodes):
                self._lock.release()
                return
            try:
                self._lock.release()
            except ValueError:
                pass
                
    def __hash__(self):
        return hash(self.name) + 1087 * hash(tuple(self.nodes)) + 1609 * hash(self.name)

class Node(object):
    __idseed = 0
    PROXY = 1
    LOCAL = 2 
    def __init__(self, parent=None, name=None, function=None):
        """@param name: Must be unique!!
            @param parent: a Schema object
            @param function: a function
        """
        self.ports = []
        self.threadManager = ThreadManager(self)
        if name is None:
            # Generates a unique identifier, BUT is not thread-safe.
            self.name = Node.__idseed
            Node.__idseed += 1
        else:
            # Sets the ID manually - but doesn't guarantee the lack of collisions
            self.name = name
#        self.parent = parent
        self.schema = parent
        self.function = function
        self.params = {}
        self.location = Node.LOCAL  # default
        self.result = None
        self._jobsDone = 0
        self._lock = multiprocessing.Lock()
        
    def __repr__(self):
        return "Node obj: %s;" % self.name
    
    def create_and_add_port(self, name=None, ptype=None, linked=None):
        """@param  name: a Unique identifier. Optional but recommended
            @param ptype: either Port.IN or Port.OUT
            @param linked: a Port object to which self is connected"""
        newPort = Port(name, self, ptype, linked)
        self.ports.append(newPort)
        return newPort
    def add_port(self, port=None):
        if port:
            self.ports.append(port)
        
    def __hash__(self):
        return hash(self.name) + 461 * hash(tuple(self.ports)) + 881 * hash(self.function)
    
    def findPortByName(self, portName):
        try:
            result = [port for port in self.ports if port.name == portName]
            if len(result) == 1:
                return result[0]
            elif len(result) == 0:
                return None
            else:
                raise RuntimeError("%i ports with the same ID found" % len(result))
        except Exception, err:
            raise RuntimeError("Ports with the given name couldn't be found.", err)
            
    def run(self, *args, **kwargs):
        input_parameters = tuple(self.params.values() + [port.target.node.result for port in self.ports if port.type == Port.IN])
        self.job = self.schema.jobServer.submit(self.function, input_parameters, modules=registered_modules, callback=self.jobDoneCallback, globals=globals())
    
    def run_initial(self):
        input_parameters = tuple(self.params.values())
        # TODO: find a smarter way to pass the module names here.
        self.job = self.schema.jobServer.submit(self.function, input_parameters, modules=registered_modules, callback=self.jobDoneCallback)
    
    def signalJobDone(self):
        """This is used by a previous node to signal that its work has been completed. 
        When all input ports have been satisfied, this fires the current node"""
        self._lock.acquire()
        self._jobsDone += 1
        if self._jobsDone == len([port for port in self.ports if port.type == Port.IN]):
            self._lock.release()
            self.run()
        try:
            self._lock.release()
        except ValueError:
            pass
        
    def jobDoneCallback(self, *args, **kwargs):
        self.result = self.job.result
        for outport in (port for port in self.ports if port.type == Port.OUT):
            outport.runNextNode()
    
    def is_reachable(self):
        '''If a proxy node is used, check if the remote node's methods can be called.
        If a local node, just return True.
        '''
        # Default implementation for local nodes
        # todo: some checking of the remote worker process 
        return True
    
    def setParam(self, name, value):
        self.params[name] = value

#
class Port(object):
    """Represents a property of a Node, which can connect the parent Node to another port (of different type) of another node"""
    __idseed = 0
    IN = 1
    OUT = 2
    def __init__(self, name=None, parent=None, ptype=None , target=None):
        """@param name: string - if given, must be unique (at least for all the ports of one Node
            @param parent: a Node object
            @param ptype: either Port.IN or Port.OUT
            @param target: a Port object, to which this object is connected
        """
        if name is None:
            # Generates ID automatically, but is not thread safe
            self.name = Port.__idseed
            Port.__idseed += 1
        else:
            # Sets the ID manually, but doesn't guarantee collisions won't happen
            self.name = name
#        self.parent = parent
        self.node = parent
        self.type = ptype
        self.target = target
    def is_used(self):
        if self.target is not None:
            return True
        else:
            return False
        
    def __repr__(self):
        return "Port obj: %s;" % self.name
    
    def runNextNode(self):
        if self.type == Port.OUT:
            if self.is_used():
                self.target.node.signalJobDone()
    
    def connect(self, other):
        # other should be of type Port
        self.target = other
        other.target = self
    def __hash__(self):
        return hash(self.name) + 1747 * hash(self.target) + 1171 * hash(self.type)
    
    
class ThreadManager(object):
    '''A Monitor for each node.
    Before firing each node's 'run' method, the ThreadManager
    TODO: synchronize all methods of the class! 
    '''
    def __init__(self, node):
        self.node = node
        self.globalTM = GlobalThreadManagerFactory.getGlobalThreadManager()
        self._registrationList = []
    def job_done(self, inputPort):
        '''An input port of the Node calls this method to register itself as having completed the calcuations'''
        self._registrationList.append(inputPort)
    def get_nr_of_jobs_done(self):
        '''Returns the number of jobs that have reported to be done.'''
        return len(self._registrationList)

class GlobalThreadManagerFactory(object):
    @classmethod
    def getGlobalThreadManager(cls):
        """returns the single GlobalThreadManager"""
        if hasattr(cls, '_globalThreadManager'):
            return getattr(cls, '_globalThreadManager')
        else:
            cls._globalThreadManager = GlobalThreadManager()
        
class GlobalThreadManager(object):
    '''Handles the request for threads from the instances of the ThreadManagers.
    @warning: DO NOT INSTANTIATE! Use GlobalThreadManagerFactory.getGlobalThreadManager() instead!!!
    '''
    
class SchemaRuntimeError(Exception):
    pass

class SchemaConfigurationError(Exception):
    pass
# The nodes need actual functions that they wrap
# The schema needs to be loaded from an XML

# first: create more objects in the domain, map to XML later
