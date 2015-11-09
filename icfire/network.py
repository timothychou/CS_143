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
        self.G = nx.Graph(flows=[])
        self.nodes = dict()
        self.links = dict()
        self.flows = dict()
        self.events = []
        self.last_node = 0
        self.last_link = 0
        self.last_flow = 0
    # graph creation functions

    def addRouter(self, node_id=None, static_routing=False):
        """ Adds a router to the list of hosts and to the graph representation

        :param node_id: (optional) specify a node id to use for this node.
        :param static_routing (optional) specify whether to use static
         or dyanmic routing
        :returns: id of router added
        """
        if node_id is not None:
            newid = node_id
        else:
            newid = self.getNewNodeId()
        if self.G.has_node(newid):
            print("router " + node_id + " is already in the graph.")
            return
        self.G.add_node(newid, host=0)
        self.nodes[newid] = Router(newid, [])

        if not static_routing:
            # if dynamic routing, create a update routing table event
            self.events.append(
                UpdateRoutingTableEvent(0, self.nodes[newid]))
        
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
        if newid in self.G:
            print "Graph already has node " + node_id + ". Not adding."
            return newid
        else:
            self.G.add_node(newid, host=1)
        self.nodes[newid] = Host(newid)
        
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
            return linkid
        else:
            print("Source or target not in the graph!")
            return None

    def addFlow(self, source_id, dest_id, bytes, timestamp, flowType):
        """ This function adds a flow to the network description

        This also creates the flow if the flow has not been created already

        :param source_id: source host id
        :param dest_id: dest host id
        :param bytes: number of bytes to send
        :param timestamp: time that Flow sends first packet
        :param flowType: name of Flow class to be used
        """
        # Check if the network has a flow list yet
        if not isinstance(self.G.graph.get('flows'), dict):
            self.G.graph['flows'] = dict()
        if source_id in self.nodes:
            if dest_id not in self.nodes:
                print("dest_id not found")
                return
            else:
                newFlowId = self._createFlow(source_id, dest_id, bytes,
                                            timestamp, flowType)
                eventjson = {
                    'source_id': source_id,
                    'dest_id': dest_id,
                    'bytes': bytes,
                    'timestamp': timestamp,
                    'flowType': flowType,
                }
                self.G.graph['flows'][newFlowId] = eventjson
        else:
            print("host_id not found")

    def _createFlow(self, source_id, dest_id, bytes, timestamp, flowType):
        """ Adds a new Flow from source_id to dest_id

        Uses reflection on flowType to create the appropriate Flow object

        :param source_id: source host id
        :param dest_id: dest host id
        :param bytes: number of bytes to send
        :param timestamp: time that Flow sends first packet
        :param flowType: name of Flow class to be used
        :returns: if a flow has been created, the flowId is returned
        """
        if source_id not in self.nodes or dest_id not in self.nodes:
            print("Source or target not in the graph!")
            return None

        assert flowType in flow.__dict__

        newFlowId = self.getNewFlowId()
        f = flow.__dict__[flowType](source_id, dest_id, bytes, newFlowId)
        self.flows[newFlowId] = f

        self.nodes[source_id].addFlow(f)
        self.nodes[dest_id].addFlowRecipient(flow.FlowRecipient(newFlowId))

        # Create an Event to update the Flow (send first packet)
        self.events.append(
            UpdateFlowEvent(timestamp, self.nodes[source_id], newFlowId,
                            'Initialize flow %d' % newFlowId))
        return newFlowId

    def loadFlows(self, filename=None):
        """ This function loads flows from file and instantiates them.

        If it is not given a filename, it tries to load from the graph.

        :param filename: optional filename
        """

        if filename is None:
            G = self.G
        else:
            with open(filename, 'r') as f:
                data = json.load(f)
                G = json_graph.node_link_graph(data)

        assert len(G) > 0

        if 'flows' in self.G.graph:
            flows = self.G.graph['flows']
            for i in flows:
                # generate events
                source_id = flows[i].get('source_id')
                dest_id = flows[i].get('dest_id')
                bytes = flows[i].get('bytes')
                timestamp = flows[i].get('timestamp')
                flowType = flows[i].get('flowType', 'Flow')
                self._createFlow(source_id, dest_id, bytes,
                                timestamp, flowType)

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
        for node_id in self.G.nodes():
            # generate hosts and routers
            if (self.G.node[node_id].get('host')):
                self.nodes[node_id] = Host(node_id)
            else:
                self.nodes[node_id] = Router(node_id)

        for edge in self.G.edges(data=True):
            linkid = edge[2].get('linkid', self.getNewLinkId())
            self.addLink(edge[0], edge[1],
                         edge[2].get('rate'),
                         edge[2].get('delay'),
                         edge[2].get('buffsize'),
                         linkid)

        self.loadFlows()

    def draw(self):
        colors = [self.G.node[n]['host'] for n in self.G.nodes()]
        pos = nx.spring_layout(self.G)
        nx.draw(self.G, pos=pos, node_color=colors)
        nx.draw_networkx_labels(self.G, pos, font_color='w')
        edges = self.G.edges(data=True)
        edgelabels = dict(((edge[0], edge[1]), str(edge[2].get('rate')) + ' mbps') for edge in edges)
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edgelabels)
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
