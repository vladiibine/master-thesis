import weakref

GUI_PROPERTY_NAME = '_guiInfo'
#The name of the property added to the decorated functions

PARAM_FILE = 0
PARAM_INT = 1
PARAM_STRING = 2


def validate(f=None, **kwargs):
	"""Decorator pattern.
	Decorates functions, specifing 2 validators (functions), one for the input and one for
	the output. The input validator (parameter "pre") gets executed before the function, and the
	output validator (parameter "post") gets executed on the results of the function.
	
	Either use @validate def Or @validate(pre=func1,post=func2) where at least on of the pre/post functions are specified
	Use case 1:
	@validate
	def myfunc(...

	Use case 2:
	@validate(pre=myinputvalidator, post=myoutputvalidator)
	def myfunc(...

	In the second scenario at least one of the validators needs to be specified.
	The decorator is NOT to be used like this:
	@validate()
	def myfunc(...

	Features list:
	Keeps the original function name
	Keeps a reference to the original function
	Makes the original function keep a reference to the decorated function
	
	It supports the methods "append_child" and "set_parent" for validation
	It supports a global tree validation mechanism

	Incomplete features, to be improved:
	The weak regitry in the validate lib does not dispose of the elements due to circular references
	The function does not implement a mechanism for querying the registered wrappers... dunno if that's useful though....
	The class leaves the dictionary of the wrappers too dirty ->should make the function fields secretive.
	"""
	def wrapper(*args, **kw):
		if wrapper.validation_state is True:
			print "wrapper"
			try:
				if "pre"in wrapper.__dict__:wrapper.pre(*args, **kw)
			except: raise
			result = wrapper.original_func(*args, **kw)
			try:
				if"post"in wrapper.__dict__: wrapper.post(result)
			except:raise
			return result
		else: return wrapper.original_func(*args, **kw)
		
	def mediator(func):
		print"mediator"
		mediator.original_func = func
		wrapper.original_func = mediator.original_func
		wrapper.func_name = func.func_name
		wrapper.original_func.wrapper_func = wrapper
		wrapper.validation_state = True
		wrapper.__doc__ = wrapper.original_func.__doc__
		def self_validation(boolean):
			wrapper.validation_state = boolean
		wrapper.self_validation = self_validation
		
		if not hasattr(validate, "_registry"):
			validate._registry = weakref.WeakValueDictionary()
		validate._registry[id(wrapper)] = wrapper
		def set_parent(parent):
			"""parent=another wrapped function"""
			if not hasattr(parent, "validation_level"):
				parent.validation_level = 0
				wrapper.validation_level = 1
			else:
				if not hasattr(parent, "append_child"):
					raise Exception("The parent as no 'append_child' method. You might be trying to set as parent an object of the wrong type")
				else:
					parent.append_child(wrapper)
					wrapper.validation_level = parent.validation_level + 1
		wrapper.set_parent = set_parent
		def append_child(child):
			if wrapper is child:
				raise Exception("Can't add the element as a child or parent to itself")
			if not hasattr(wrapper, "child_nodes"):
				wrapper.child_nodes = []
			if not hasattr(child, "validation_level"):
				raise Exception("The child you are trying to add has no attribute 'validation_level'. You might be trying to add as a validation child node an object of the wrong type")
			else:
				child.validation_level = wrapper.validation_level + 1
			wrapper.child_nodes.append(child)
		wrapper.append_child = append_child
		wrapper.validation_level = 0
		def set_branch_state(boolean):
			def rec(wrapper):
				if hasattr(wrapper, "child_nodes"):
					for child in wrapper.child_nodes:
						if hasattr(child, "validation_state"):
							child.validation_state = boolean
							rec(child)
			wrapper.validation_state = boolean							
			rec(wrapper)
		wrapper.set_branch_state = set_branch_state
		return wrapper
		
		
		
	if not hasattr(validate, "validation_off"):
		def validation_off(level= -1):
			reg = validate._registry
			for wrap in reg:
				reg[wrap].validation_state = False
		validate.validation_off = validation_off
		# print"validate did not have the 'validation_off' attribute"
	if not hasattr(validate, "validation_on"):
		def validation_on(level= -1):
			reg = validate._registry
			for wrap in reg:
				reg[wrap].validation_state = True
		validate.validation_on = validation_on
		
	if f is None:
		if len(kwargs) > 0:
			print"validate [args]"
			try: wrapper.pre = kwargs["pre"]
			except: pass
			try: wrapper.post = kwargs["post"]
			except:pass
			return mediator
		else:
			raise Exception("Declaration exception '@validate()' not allowed. Specify at least 1 function validator")
	else:
		if len(kwargs) == 0:
			print"validate NO-args"
			return mediator(f)
		else:
			raise Exception("Declaration exception: None of the possible 2 decoration scenarios. Check the docs. Use help(validate)")
	
def guiInfo(inputPorts=0, outputPorts=0, params={}):
	"""Decorator pattern.
	Makes it easy to specify how many input and output ports a user function requires.
	@param inputPorts: int - Number of input ports
	@param outputPorts: int - Number of output ports
	@param params: dict of {'name':type} values, where 'name' is a name of a parameter of the actual function and 'type' is one of the PARAM_* members of this module. It specifies how the parameter 'name' should be treated by the GUI. 
	
	It sets "_guiInfo.input" and "_guiInfo.output" attributes on the decorated function. These
	are then used by the application to dynamically create nodes from the given function.
	
	It also sets the "_guiInfo.params" attribute. This attribute tells the gui that the current node
	will need user input in the GUI mode (for example asking for a file path where to store data, or
	to load data from). The "_guiInfo.params" attribute is a tuple of type (("fist_param_name",types.MyFirstType),("second_param_name",types.MySecondType)...)
	where types is a standard import.
	
	Usage:
	@guiInfo(1,1)
	def my_func(...
	
	DON'T use it without arguments:
	@guiInfo
	def my_func
	
	TODO: Should specify some other information here, like picture to be used, some documentation, etc.
	P.S. this looks a lot simpler function "validate", doesn't it? :P
	"""
	def mediator(func):
		temp_name = func
		if hasattr(func, "wrapper_func"):  # Very careful about changing property names, as they are used in reflection like this
			temp_name = func.wrapper_func
		setattr(temp_name, GUI_PROPERTY_NAME, type('', (object,), {})())
		getattr(temp_name, GUI_PROPERTY_NAME).input 	= inputPorts
		getattr(temp_name, GUI_PROPERTY_NAME).output 	= outputPorts
		if isinstance(params,dict):
			getattr(temp_name, GUI_PROPERTY_NAME).params	= params
		else:
			raise DecorationException("The gui params should be specified as a dictionary {name:type...}, where name is a string, and type is one of the decorators.PARAM_* variables")
		return func
	return mediator

class DecorationException(Exception):
	pass
