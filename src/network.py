import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph
import json

from eventhandler import *
from networkobject import *


class Network(object):

    """This class contains all information encapsulating a computer network.

    The network is kept track of as a dictionary of objects, as well as within
    a NetworkX graph.

    It is capable of importing and exporting the network and its specifications
    to file
    """

    def __init__(self):
        self.G = nx.Graph(events=[])
        self.nodes = dict()
        self.links = dict()
        self.events = []
        self.last_node = 0
        self.last_link = 0
    # graph creation functions

    def addRouter(self, node_id=None):
        """ Adds a router to the list of hosts and to the graph representation

        :param node_id: (optional) specify a node id to use for this node.
        :returns: id of router added
        """
        if node_id is not None:
            newid = node_id
        else:
            newid = self.getNewNodeId()
        if not self.G.has_node(newid):
            self.G.add_node(newid, host=0)
        self.nodes[newid] = Router(newid, [])
        return newid

    def addHost(self, node_id=None):
        """ Adds a host to the list of hosts and to the graph representation

        :param node_id: (optional) specify a node id to use for this node.
        :returns: id of host added
        """
        if node_id is not None:
            newid = node_id
        else:
            newid = self.getNewNodeId()
        if not self.G.has_node(newid):
            self.G.add_node(newid, host=1)
        self.nodes[newid] = Host(newid, [])
        return newid

    def addLink(self, source_id, target_id, latency, rate):
        """ Adds a link from source_id to target_id

        :param source_id: id of a node
        :param target_id: id of a node
        :param latency: latency of the link
        :param latency: link rate
        """
        if (source_id in self.nodes and target_id in self.nodes):
            if not self.G.has_edge(source_id, target_id):
                self.G.add_edge(source_id, target_id,
                                latency=latency, rate=rate)
            linkid = self.getNewLinkId()
            self.links[linkid] = Link(source_id, target_id, latency, rate)
            self.nodes[source_id].addLink(linkid)
            self.nodes[target_id].addLink(linkid)
        else:
            print("Source or target not in the graph!")
            return

    def addEvent(self, host_id, target_id, size=0, time=0):
        """ Adds an event to the graph description

        It checks that the ids in the events actually exist first.

        :param host_id: the thing sending events
        :param target_id: the target
        :param size: size of data being sent (optional)
        :param time: time (integer) representing when the Event should happen.
        """
        if host_id in self.nodes:
            if target_id not in self.nodes:
                print("target_id not found")
                return
            else:
                eventjson = {
                    'host_id': host_id,
                    'target_id': target_id,
                    'size': size,
                    'time': time,
                }
                self.G.graph['events'].append(eventjson)
                self.events.append(
                    PacketEvent(time, host_id, target_id, size))  # TODO
        else:
            print("host_id not found")

    def save(self, filename):
        """ Writes the data to file

        :param filename: file to write to
        """
        data = json_graph.node_link_data(self.G)
        s = json.dumps(data)
        with open(filename, 'w') as f:
            f.write(s)

    def load(self, filename='testfile.json'):
        with open(filename, 'r') as f:
            data = json.load(f)
        self.G = json_graph.node_link_graph(data)
        self.last_node = max(self.G.nodes())
        for node in self.G.nodes():
            # generate hosts and routers
            if (self.G.node[node]['host']):
                self.addHost(node)
            else:
                self.addRouter(node)

        for edge in self.G.edges(data=True):
            self.addLink(edge[0], edge[1], edge[2]['latency'], edge[2]['rate'])

        if 'events' in self.G.graph:
            for i in self.G.graph['events']:
                # generate events
                time = i['time']
                sender = i['host_id']
                receiver = i['target_id']
                # todo: generate packet from event
                packet = i['size']
                self.events.append(PacketEvent(time, sender, receiver, packet))
        else:
            print("No events found for graph")

    def getNewNodeId(self):
        while(self.last_node in self.nodes):
            self.last_node += 1
        return self.last_node

    def getNewLinkId(self):
        while(self.last_link in self.links):
            self.last_link += 1
        return self.last_link

    def draw(self):
        colors = [self.G.node[n]['host'] for n in self.G.nodes()]
        nx.draw(self.G, node_color=colors)
        plt.show()

    def getNewNodeId(self):
        while(self.last_node in self.nodes):
            self.last_node += 1
        return self.last_node

    def getNewLinkId(self):
        while(self.last_link in self.links):
            self.last_link += 1
        return self.last_link

    def getLinkList(self):
        return list(self.links.keys())

    def getNodeList(self):
        return list(self.nodes.keys())

    def getRouterList(self):
        return [node for node in self.nodes.keys()
                if not self.nodes[node]['host']]

    def getHostList(self):
        return [node for node in self.nodes.keys()
                if self.nodes[node]['host']]
