"""
icfire.network
~~~~~~~~~~~

This module models the network. It handles network object creation, importing
and exporting, and later on it may have built in functions to analyze network
wide statistics. For example, it is capable of drawing our network itself.

Network requires the NetworkX package and is primarily a wrapper over NetworkX
for much of importing and exporting

"""

import json

import networkx as nx

from icfire import logger
import icfire.flow as flow
from icfire.event import UpdateRoutingTableEvent, UpdateFlowEvent, UpdateWindowEvent
from icfire.networkobjects.link import Link
from icfire.networkobjects.router import Router
from icfire.networkobjects.host import Host
from icfire.stats import *


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

    # graph creation functions

    def addRouter(self, node_id, init_time, static_routing):
        """ Adds a router to the list of hosts and to the graph representation

        :param node_id: (optional) specify a node id to use for this node.
        :param init_time: (optional) time the router starts up
        :param static_routing: (optional) specify whether to use static
         or dyanmic routing
        :returns: id of router added
        """
        if self.G.has_node(node_id):
            logger.log("router " + str(node_id) + " is already in the graph.")
            return

        self.G.add_node(node_id, host=0)
        self.nodes[node_id] = Router(node_id, [])

        if not static_routing:
            # if dynamic routing, create a update routing table event
            self.events.append(
                UpdateRoutingTableEvent(
                    init_time,
                    self.nodes[node_id],
                    'Router %s updates routing table' % node_id))

        return node_id

    def addHost(self, node_id):
        """ Adds a host to the list of hosts and to the graph representation

        :param node_id: (optional) specify a node id to use for this node.
        :returns: id of host added
        """
        if node_id in self.G:
            print "Graph already has node " + node_id + ". Not adding."
            return node_id
        else:
            self.G.add_node(node_id, host=1)
        self.nodes[node_id] = Host(node_id)

        return node_id

    def addLink(self, source_id, target_id,
                rate, delay, buffsize, linkid):
        """ Adds a link from source_id to target_id

        :param source_id: id of a node
        :param target_id: id of a node
        :param rate: link rate (Mbps)
        :param delay: delay of the link (ms)
        :param buffsize: link buffer size (KB)
        :param linkid: (optional) optional unique id in
        :returns: integer or string key of the link

        """
        if source_id in self.nodes and target_id in self.nodes:
            # If no linkid is provided, generate a unique
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

    def addFlow(self, source_id, dest_id, bytes, timestamp, flowType, flowId):
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
                                             timestamp, flowType, flowId)
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

    def _createFlow(self, source_id, dest_id, bytes, timestamp, flowType, flowId):
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

        f = flow.__dict__[flowType](source_id, dest_id, bytes, flowId)
        self.flows[flowId] = f

        self.nodes[source_id].addFlow(f)
        fr = flow.FlowRecipient(flowId, f.stats)
        self.nodes[dest_id].addFlowRecipient(fr)

        # Create an Event to update the Flow (send first packet)
        self.events.append(
            UpdateFlowEvent(timestamp, self.nodes[source_id], flowId,
                            'Initialize flow ' + repr(flowId)))

        if flowType == 'FastTCPFlow':
            self.events.append(UpdateWindowEvent(timestamp,
                                                 self.flows[flowId],
                                                 logMessage='Updating window size on flow %s' % flowId))
        return flowId

    def load(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            f.close()

        # load hosts
        for host in data["hosts"]:
            self.addHost(host["id"])

        # load routers
        for router in data["routers"]:
            self.addRouter(
                router["id"], router["init_time"], router["static_routing"])

        # load links
        for link in data["links"]:
            id = link["id"]
            source_id = link["source_id"]
            target_id = link["target_id"]
            rate = link["rate"]
            delay = link["delay"]
            buffsize = link["buffsize"]
            self.addLink(source_id, target_id, rate, delay, buffsize, id)

        # load flows
        for flow in data["flows"]:
            name = flow["name"]
            source_id = flow["source_id"]
            dest_id = flow["dest_id"]
            timestamp = flow["timestamp"]
            bytes = flow["bytes"]
            flowType = flow["flowType"]
            self.addFlow(source_id, dest_id, bytes, timestamp, flowType, name)

    def draw(self):
        colors = [self.G.node[n]['host'] for n in self.G.nodes()]
        pos = nx.spring_layout(self.G)
        nx.draw(self.G, pos=pos, node_color=colors)
        nx.draw_networkx_labels(self.G, pos, font_color='w')
        edges = self.G.edges(data=True)
        edgelabels = dict(
            ((edge[0], edge[1]), str(edge[2].get('rate')) + ' mbps') for edge in edges)
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edgelabels)
        plt.show()

    def plotAll(self, flowres, plotflows, linkres, plotlinks,
                hostres, plothosts, flowType="Reno"):
        """ plot data for specified flows, links, hosts

        :param flowres: resolution for flow plots
        :param plotflows: flows to plot
        :param linkres: resolution for link plots
        :param plotlinks: links to plot
        :param hostres: resolution for host plots
        :param plothosts: hosts to plot
        :param flotType: string to describe the type of flow used.
            Defaults to Reno
        """
        # FLOWS
        # Byte Send Rate of all 3
        plt.figure()
        plt.subplot(411)
        plt.title("Flow statistics using TCP " + flowType)
        for f in plotflows:
            plotrate(self.flows[f].stats.bytessent, flowres, False, label=f)
        plt.ylabel('Send rate (Bytes/ms)')

        # Byte Recieved Rate of all 3
        plt.subplot(412)
        for f in plotflows:
            plotrate(self.flows[f].stats.bytesreceived, flowres, False, label=f)
        plt.ylabel('Recieve rate (Bytes/ms)')

        # RTT of flows
        plt.subplot(413)
        for f in plotflows:
            plotsmooth(self.flows[f].stats.rttdelay, flowres, False, label=f)
        plt.ylabel('Flow RTT (ms)')

        # Window size (This will break if there is no window size)
        plt.subplot(414)
        for f in plotflows:
            if self.flows[f].stats.windowsize:
                plotsmooth(self.flows[f].stats.windowsize, flowres, label=f)
        plt.ylabel('Window size')

        plt.subplots_adjust(hspace=.5)

        # LINKS
        # link byte flow rate
        plt.figure()
        plt.subplot(311)
        plt.title("Link statistics using TCP " + flowType)
        for l in plotlinks:
            plotrate(self.links[l].stats.bytesflowed, linkres, False, label=l)
        plt.ylabel('Flow Rate (Bytes/ms)')

        # link buffer occupancy
        plt.subplot(312)
        for l in plotlinks:
            plotsmooth(
                self.links[l].stats.bufferoccupancy, linkres, False, label=l)
        plt.ylabel('Buffer Occupancy (Bytes)')

        # bytes lost
        plt.subplot(313)
        for l in plotlinks:
            plotintervalsum(self.links[l].stats.lostpackets, linkres, label=l)
        plt.ylabel('Packets lost')

        plt.subplots_adjust(hspace=.5)

        # HOSTS
        # Plot send and recieve rates
        plt.figure()
        for i in xrange(len(plothosts)):
            h = plothosts[i]
            plt.subplot(len(plothosts) * 100 + 10 + i + 1)  # dank code man
            plt.title("Host " + h + " using TCP " + flowType)
            plotrate(
                self.nodes[h].stats.bytessent, hostres, label='%s-send' % h)
            plotrate(
                self.nodes[h].stats.bytesreceived, hostres, label='%s-receive' % h)
            plt.ylabel('Bytes/ms')

        plt.subplots_adjust(hspace=.5)

        plt.show()
