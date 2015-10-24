import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph
import json


class NetworkGraph(object):
    """ This class is a wrapper over networkx to create the graph specification

    Routers and hosts must be created before links and instructions that use
    them are created.
    """
    G = None
    node_id = -1
    nodes = []

    def __init__(self):
        self.G = nx.Graph(instructions=[])

    def add_router(self, **args):
        """ Returns id of router added """
        self.node_id += 1
        self.G.add_node(self.node_id, host=0)
        self.nodes.append(self.node_id)
        return self.node_id

    def add_host(self, **args):
        """ Returns id of host added """
        self.node_id += 1
        self.G.add_node(self.node_id, host=1)
        self.nodes.append(self.node_id)
        return self.node_id

    def add_link(self, source_id, target_id, rate):
        if (source_id in self.nodes and target_id in self.nodes):
            self.G.add_edge(source_id, target_id, rate=rate)
        else:
            print("Source or target not in the graph!")

    def add_instruction(self, host_id, target_id, size=0, time=0):
        """ Adds an instruction to the graph description

        It checks that the ids in the instructions actually exist first.

        args:
            host_id: the thing sending instructions
            target_id: the target
        """
        if host_id in self.nodes:
            if target_id not in self.nodes:
                print("target_id not found")
                return
            else:
                instruction = {
                    'host_id': host_id,
                    'target_id': target_id,
                    'size': size,
                    'time': time,
                }
                self.G.graph['instructions'].append(instruction)
        else:
            print("host_id not found")

    def write(self, filename):
        data = json_graph.node_link_data(self.G)
        s = json.dumps(data)
        with open(filename, 'w') as f:
            f.write(s)


class InputParser(object):
    """ Parses inputs

    This class parses data files and sets up the routers. It then intializes
    the data flow

    """
    def __init__(self):
        pass

    def load(self, filename='testfile.json'):
        with open(filename, 'r') as f:
            data = json.load(f)
        self.G = json_graph.node_link_graph(data)
        for node in self.G.nodes():
            # generate hosts and routers
            if (self.G.node[node]['host']):
                # generate host
                pass
            else:
                # generate router
                # generate router update events
                pass

        for edge in self.G.edges():
            # generate link
            pass

        for i in self.G.graph:
            # generate events
            pass

    def draw(self):
        colors = [self.G.node[n]['host'] for n in self.G.nodes()]
        nx.draw(self.G, node_color=colors)
        plt.show()

