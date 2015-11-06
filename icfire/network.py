import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph
import json
import flow

from eventhandler import *
from networkobject import *


class Network(object):

    """This class contains all information encapsulating a computer network.

    The network is kept track of as a dictionary of objects, as well as within
    a NetworkX graph.

    It is capable of importing and exporting the network and its specifications
    to file

    All add* methods should be called only at the beginning of the simulation.

    """

    def __init__(self):
        self.G = nx.Graph(events=[])
        self.nodes = dict()
        self.links = dict()
        self.flows = dict()
        self.events = []
        self.last_node = 0
        self.last_link = 0
        self.last_flow = 0
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
        if self.G.has_node(newid):
            print "Graph already has said node. Not adding."
            return newid
        else:
            self.G.add_node(newid, host=1)
        self.nodes[newid] = Host(newid, [])
        return newid

    def addLink(self, source_id, target_id,
                rate=10, delay=10, buffsize=64, linkid=None):
        """ Adds a link from source_id to target_id

        :param source_id: id of a node
        :param target_id: id of a node
        :param rate: link rate (Mbps)
        :param delay: delay of the link (ms)
        :param buffsize: link buffer size (KB)
        :returns: integer or string key of the link

        """
        if (source_id in self.nodes and target_id in self.nodes):
            # If no linkid is provided, generate a unique
            if linkid is None:
                linkid = self.getNewLinkId()
            if not self.G.has_edge(source_id, target_id):
                self.G.add_edge(source_id, target_id,
                                rate=rate, delay=delay,
                                buffsize=buffsize, linkid=linkid)
            self.links[linkid] = Link(self.nodes[source_id],
                                      self.nodes[target_id],
                                      rate, delay, buffsize, linkid)
            self.nodes[source_id].addLink(self.links[linkid])
            self.nodes[target_id].addLink(self.links[linkid])
        else:
            print("Source or target not in the graph!")
            return

    def addFlow(self, source_id, dest_id, bytes, timestamp, flowType):
        """ Adds a new Flow from source_id to dest_id

        Uses reflection on flowType to create the appropriate Flow object

        :param source_id: source host id
        :param dest_id: dest host id
        :param bytes: number of bytes to send
        :param timestamp: time that Flow sends first packet
        :param flowType: name of Flow class to be used
        """
        if source_id in self.nodes and dest_id in self.nodes:
            assert flowType in flow.__dict__

            newFlowId = self.getNewFlowId()
            f = flow.__dict__[flowType](source_id, dest_id, bytes, newFlowId)
            self.flows[newFlowId] = f

            self.nodes[source_id].addFlow(f)
            self.nodes[dest_id].addFlowRecipient(flow.FlowRecipient(newFlowId))

            # TODO(tangerine) Make additional relevant network changes in self.G

            # Create an Event to update the Flow (send first packet)
            self.events.append(
                UpdateFlowEvent(timestamp, self.nodes[source_id], newFlowId,
                                'Initialize flow %d' % newFlowId))
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
            linkid = edge[2].get('linkid', self.getNewLinkId())
            self.addLink(edge[0], edge[1],
                         edge[2]['rate'], edge[2]['delay'],
                         edge[2]['buffsize'], linkid)

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

    def getNewFlowId(self):
        while(self.last_flow in self.flows):
            self.last_flow += 1
        return self.last_flow

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
