# -*- coding: utf-8 -*-
'''Generated code - isn't it wonderful?

Please don't modify this file. It will be generated each time
from the matrix_operations_demo.xcs file, created with the graphical tool

Please note that in order for this file to be executed from outside of the visual tool,
the paths of domain.py and lib.py will have to be included the list sys.path

USAGE:
import matrix_operations_demo
matrix_operations_demo.Schema.run()'''

import domain,lib
reload(domain)

Schema = domain.Schema('matrix_operations_demo',69798992)

#Defining the Schema structure
newNode = Schema.create_and_add_node(name='''N1: float_matrix_from_csv''',function=lib.importFunc('''float_matrix_from_csv''','''input_1''','''./user_functions/custom_1/input_1/input_1.py'''))
newNode.create_and_add_port(name='''Output 1''',ptype=domain.Port.OUT)
newNode.setParam(name='''filename''',value='''S:/Dropbox/pt_sqala/disertatie/workspace/src/xmlschemas/asdf/input.txt''')
newNode = Schema.create_and_add_node(name='''N2: square_matrix''',function=lib.importFunc('''square_matrix''','''funcs1''','''./user_functions/funcs1.py'''))
newNode.create_and_add_port(name='''Input 1''',ptype=domain.Port.IN)
newNode.create_and_add_port(name='''Output 1''',ptype=domain.Port.OUT)
newNode = Schema.create_and_add_node(name='''N3: float_matrix_from_csv''',function=lib.importFunc('''float_matrix_from_csv''','''input_1''','''./user_functions/custom_1/input_1/input_1.py'''))
newNode.create_and_add_port(name='''Output 1''',ptype=domain.Port.OUT)
newNode.setParam(name='''filename''',value='''S:/Dropbox/pt_sqala/disertatie/workspace/src/xmlschemas/asdf/input.txt''')
newNode = Schema.create_and_add_node(name='''N4: transpose_matrix''',function=lib.importFunc('''transpose_matrix''','''proc1''','''./user_functions/custom_1/process_1/proc1.py'''))
newNode.create_and_add_port(name='''Input 1''',ptype=domain.Port.IN)
newNode.create_and_add_port(name='''Output 1''',ptype=domain.Port.OUT)
newNode = Schema.create_and_add_node(name='''N5: sum_matrix''',function=lib.importFunc('''sum_matrix''','''funcs1''','''./user_functions/funcs1.py'''))
newNode.create_and_add_port(name='''Input 1''',ptype=domain.Port.IN)
newNode.create_and_add_port(name='''Input 2''',ptype=domain.Port.IN)
newNode.create_and_add_port(name='''Output 1''',ptype=domain.Port.OUT)
newNode = Schema.create_and_add_node(name='''N6: matrix_to_csv''',function=lib.importFunc('''matrix_to_csv''','''output_1''','''./user_functions/custom_1/output_1/output_1.py'''))
newNode.create_and_add_port(name='''Input 1''',ptype=domain.Port.IN)
newNode.setParam(name='''filename''',value='''S:/Dropbox/pt_sqala/disertatie/workspace/src/xmlschemas/asdf/matrix_operations_demo_output.txt''')
newNode = Schema.create_and_add_node(name='''N7: transpose_matrix''',function=lib.importFunc('''transpose_matrix''','''proc1''','''./user_functions/custom_1/process_1/proc1.py'''))
newNode.create_and_add_port(name='''Input 1''',ptype=domain.Port.IN)
newNode.create_and_add_port(name='''Output 1''',ptype=domain.Port.OUT)

#Defining a connection
node1 = Schema.findNodeByName('''N4: transpose_matrix''')
port1 = node1.findPortByName('''Output 1''')
node2 = Schema.findNodeByName('''N5: sum_matrix''')
port2 = node2.findPortByName('''Input 2''')
if port1 != None and port2 != None:
    port1.connect(port2)

node1 = Schema.findNodeByName('''N3: float_matrix_from_csv''')
port1 = node1.findPortByName('''Output 1''')
node2 = Schema.findNodeByName('''N4: transpose_matrix''')
port2 = node2.findPortByName('''Input 1''')
if port1 != None and port2 != None:
    port1.connect(port2)

node1 = Schema.findNodeByName('''N6: matrix_to_csv''')
port1 = node1.findPortByName('''Input 1''')
node2 = Schema.findNodeByName('''N7: transpose_matrix''')
port2 = node2.findPortByName('''Output 1''')
if port1 != None and port2 != None:
    port1.connect(port2)

node1 = Schema.findNodeByName('''N5: sum_matrix''')
port1 = node1.findPortByName('''Output 1''')
node2 = Schema.findNodeByName('''N7: transpose_matrix''')
port2 = node2.findPortByName('''Input 1''')
if port1 != None and port2 != None:
    port1.connect(port2)

node1 = Schema.findNodeByName('''N2: square_matrix''')
port1 = node1.findPortByName('''Output 1''')
node2 = Schema.findNodeByName('''N5: sum_matrix''')
port2 = node2.findPortByName('''Input 1''')
if port1 != None and port2 != None:
    port1.connect(port2)

node1 = Schema.findNodeByName('''N1: float_matrix_from_csv''')
port1 = node1.findPortByName('''Output 1''')
node2 = Schema.findNodeByName('''N2: square_matrix''')
port2 = node2.findPortByName('''Input 1''')
if port1 != None and port2 != None:
    port1.connect(port2)

try:
    del node1,node2,port1,port2
except NameError:
    pass