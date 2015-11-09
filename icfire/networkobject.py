import sys
import random
from packet import RoutingPacket
from packet import RoutingRequestPacket
from packet import DataPacket
from packet import AckPacket
from eventhandler import UpdateRoutingTableEvent
from eventhandler import UpdateFlowEvent
from eventhandler import PacketEvent
from eventhandler import LinkTickEvent
from eventhandler import Event
import logger


class NetworkObject(object):
    """abstract class for all network objects"""

    def __init__(self):
        raise NotImplementedError(
            'NetworkObject should never be instantiated.')

    def processEvent(self, event):
        """ Processes one event, depending on what the event is.

        This method should be called directly or indirectly by an EventHandler.

        :param event: Event to be processed.
        :return: list of new Events to be enqueued.
        """
        if isinstance(event, PacketEvent):
            return self._processPacketEvent(event)
        elif isinstance(event, Event):
            return self._processOtherEvent(event)
        else:
            raise AssertionError('process event should only be given an event')

    def _processPacketEvent(self, packet_event):
        raise NotImplementedError('This should be overriden by subclass')

    def _processOtherEvent(self, event):
        raise NotImplementedError('This should be overriden by subclass')


class Link(NetworkObject):
    """Represents link in a network

    This class represents a link in a network that packets can travel
    across"""

    def __init__(self, nodeA, nodeB, rate, delay, maxbuffersize, linkid):
        """ Create a Link

        :param nodeA: Node that it is connected to (object)
        :param nodeB: Node that it is connected to (object)
        :param rate: rate (mbps) that this Link can send
        :param delay: time (ms) for a packet to propagate
        :param maxbuffersize: maximum buffer size (combined for both sides)
        :param linkid: id of the Link
        """
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.rate = rate
        self.delay = delay
        self.maxbuffersize = maxbuffersize
        self.id = linkid

        self.buffer = [None] * maxbuffersize  # Queue using a cyclic array
        self.bufferindex = 0  # index of the front PacketEvent
        self.buffersize = 0  # number of items in the buffer

    def _processPacketEvent(self, packet_event):
        """Processes packet events, storing them in the buffer."""
        if self.buffersize == self.maxbuffersize:
            logger.Log('Dropping packet...')
            return

        nextopen = (self.bufferindex + self.buffersize) % self.maxbuffersize
        self.buffer[nextopen] = packet_event
        self.buffersize += 1

        # If this is the first packet in the buffer, start the LinkTickEvents
        if self.buffersize == 1:
            return [LinkTickEvent(packet_event.timestamp, self,
                                  'Link ' + self.id + ' processes a packet')]
        return []

    def _linkTickEvent(self, event):
        """ Dequeues a packet from the buffer and forwards it.

        Also possibly generates a new LinkTickEvent if there are more packets
        in the buffer.
        """
        packet_event = self.buffer[self.bufferindex]
        self.bufferindex = (self.bufferindex + 1) % self.maxbuffersize
        self.buffersize -= 1

        # Generate a new PacketEvent
        # Use event.timestamp because this is when the packet is actually
        # forwarded, not the PacketEvent time
        otherNode = self._otherNode(packet_event.sender)
        newevents = [PacketEvent(event.timestamp + self.delay,
                                 self, otherNode, packet_event.packet,
                                 'Node %s receives packet %s from link %s' %
                                 (otherNode.address,
                                  packet_event.packet.index,
                                  self.id))]

        # Make a new LinkTickEvent
        if self.buffersize:
            nexTickTime = event.timestamp + \
                          packet_event.packet.size * 8.0 / self.rate / 1024 / 1024 * 1000
            newevents.append(LinkTickEvent(nexTickTime, self,
                                           'Link %s processes a packet' % self.id))

        return newevents

    def _processOtherEvent(self, event):
        """ Processes non-packet events """
        if isinstance(event, LinkTickEvent):
            return self._linkTickEvent(event)
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.__class__)

    def _otherNode(self, node):
        """returns the other node the link is connected to"""
        return self.nodeB if node == self.nodeA else self.nodeA

    def cost(self):
        """ cost of going through this edge """
        return random.random()  # TODO(choutim) fix


class Node(NetworkObject):
    """ abstract class that represents a node in a network

    This class represents a node in a network connected by edges"""

    def __init__(self, address, links=None):
        """ Constructor for Node

        :param address: unique address of this Node
        :param links: list of Links (objects) this Node is connected to
        """
        self.address = address
        if not links:
            self.links = []
        else:
            self.links = links

    def addLink(self, target):
        self.links.append(target)

    def _processPacketEvent(self, packet_event):
        raise NotImplementedError('This should be overriden by subclass')

    def _processOtherEvent(self, event):
        raise NotImplementedError('This should be overriden by subclass')


class Host(Node):
    """ Represents a host in a network

    This class represents a host in a network that is able to receive and
    send data"""

    def __init__(self, address, links=None):
        """ Constructor for Host

        :param address: unique address of this Node
        :param links: list of Links (objects) this Node is connected to
        """
        super(self.__class__, self).__init__(address, links)
        self.flows = dict()
        self.flowrecipients = dict()

    def addLink(self, link):
        """ Overwrites default add link to check for single link """
        if not self.links:
            self.links.append(link)
        else:
            print "Node " + str(self.address) + " already has a link!"
            # todo: raise some type of error instead

    def addFlow(self, flow):
        """ Add a Flow that this Host is sending. """
        self.flows[flow.flowId] = flow

    def addFlowRecipient(self, flowrecipient):
        """ Add a Flow that this Host is receiving. """
        self.flowrecipients[flowrecipient.flowId] = flowrecipient

    def _processPacketEvent(self, event):
        """Processes packet event

        sends back an ack as needed"""
        packet = event.packet

        # Handle routing table update requests
        if isinstance(event.packet, RoutingRequestPacket):
            return [PacketEvent(event.timestamp, self, self.links[0],
                                RoutingPacket(self.address, event.packet.source,
                                              routingTable={self.address: [self.address, 0]}),
                                'Routing table packet for host %s' % self.address)]

        # Packet is ACK, update Flow accordingly
        elif isinstance(event.packet, AckPacket):
            assert packet.dest == self.address
            assert packet.flowId in self.flows
            newpackets = self.flows[packet.flowId].receiveAckPacket(packet)
            return [PacketEvent(event.timestamp, self,
                                self.links[0], p,
                                'Flow %s, packet %s from host %s to link %s' %
                                (p.flowId, p.index,
                                 self.address, self.links[0].id))
                    for p in newpackets]

        # Treat packet as data packet, return appropriate ACK
        elif isinstance(event.packet, DataPacket):
            assert packet.dest == self.address
            assert packet.flowId in self.flowrecipients

            # TODO(choutim) include packet integrity checks, maybe

            newPacket = self.flowrecipients[
                packet.flowId].receiveDataPacket(packet)
            return [PacketEvent(event.timestamp, self,
                                self.links[0], newPacket,
                                'ACK %s for flow %s from host %s to link %s' %
                                (newPacket.index, newPacket.flowId,
                                 self.address, self.links[0].id))]

        # Else we don't know what to do
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.packet.__class__)

    def _processOtherEvent(self, event):
        """ Processes non-packet events """
        if isinstance(event, UpdateFlowEvent):
            return self._processUpdateFlowEvent(event)
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.__class__)

    def _processUpdateFlowEvent(self, update_flow_event):
        f = self.flows[update_flow_event.flowId]
        t = update_flow_event.timestamp

        # Send packets
        newpackets = f.sendPackets()
        return [PacketEvent(t, self, self.links[0], p,
                            'Flow %s, packet %s from host %s to link %s' %
                            (f.flowId, p.index, self.address, self.links[0].id))
                for p in newpackets]


class Router(Node):
    """ Represents router in a network

    This class represents a router in a network that is able to
    route packets"""

    def __init__(self, address, links=None):
        """ Constructor for Router

        The routing table should either have a default starting state, or
        _UpdateRoutingTable should be called once. Otherwise, the Router
        will not be able to forward anything at all.

        :param address: unique address of this Node
        :param links: list of Links (objects) this Node is connected to
        """
        super(self.__class__, self).__init__(address, links)

        # dict with destination address as key
        # values are 2-tuples (link object, distance)
        self.routing_table = dict()

        # The routing table should either have a default starting state, or
        # _UpdateRoutingTable should be called once. Otherwise, the Router
        # will not be able to forward anything at all.

    def _processPacketEvent(self, event):
        """Processes packet event.

        Timestamp is not changed because there is no
        delay through the router.
        """

        # Received routing table information, update table
        if isinstance(event.packet, RoutingPacket):
            neighborTable = event.packet.routingTable
            link = event.sender
            cost = link.cost()

            for key, val in neighborTable.iteritems():
                if self.routing_table.get(key, [0, sys.maxint])[1] > (val[1] + cost):
                    self.routing_table[key] = [link, val[1] + cost]

        # Received routing table request
        elif isinstance(event.packet, RoutingRequestPacket):
            # process request for routing table
            return [PacketEvent(event.timestamp, self, event.sender,
                                RoutingPacket(self.address, event.packet.source,
                                              routingTable=self.routing_table),
                                'Routing table packet for router %s' % self.address)]

        # Data packet, forward to correct link
        elif isinstance(event.packet, DataPacket) or isinstance(event.packet, AckPacket):
            nextLink = self.getRoute(event.packet.dest)
            if nextLink:
                return [PacketEvent(event.timestamp, self,
                                    nextLink, event.packet,
                                    'Router %s forwards packet to %s' % (self.address, nextLink.id))]
            else:
                logger.Log('Router %s dropped packet %s' % (self.address, event.packet.index))

        # Else we don't know what to do
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.packet.__class__)

        return []

    def _processOtherEvent(self, event):
        """ Processes non-packet events """

        if isinstance(event, UpdateRoutingTableEvent):
            return self._updateRoutingTable(event)
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.__class__)

    def _updateRoutingTable(self, event):
        """ Updates the internal routing table.

        This method should be the result of an Event that informs
        the Router to update. Begins bellman ford on all nodes in the graph
        """
        return [PacketEvent(event.timestamp, self, link,
                            RoutingRequestPacket(self.address),
                            'Routing table request packet for router %s' % self.address)
                for link in self.links] + [UpdateRoutingTableEvent(event.timestamp + 100, self,
                                                                   'Router %s updates routing table' % self.address)]

    def getRoute(self, destination):
        """checks routing table for route to destination"""

        if destination in self.routing_table:
            return self.routing_table[destination][0]
        return None
