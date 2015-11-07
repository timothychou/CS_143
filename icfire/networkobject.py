from eventhandler import PacketEvent
from eventhandler import Event
from eventhandler import UpdateFlowEvent
from eventhandler import LinkTickEvent
# from packet import Packet
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

        self.buffer = [None] * maxbuffersize    # Queue using a cyclic array
        self.bufferindex = 0                    # index of the front PacketEvent
        self.buffersize = 0                     # number of items in the buffer

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
        newpacketevent = PacketEvent(event.timestamp + self.delay,
                                     self, otherNode, packet_event.packet,
                                     'Host %s receives packet %s from link %s' %
                                     (otherNode.address,
                                      packet_event.packet.index,
                                      self.id))

        # Make a new LinkTickEvent
        if self.buffersize:
            newlinktickevent = LinkTickEvent(
                event.timestamp + packet_event.packet.size / self.rate, self,
                'Link %d processes a packet' % self.id)
            return [newpacketevent, newlinktickevent]

        return [newpacketevent]

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


class Node(NetworkObject):

    """ class that represents a node in a network

    This class represents a node in a network connected by edges"""

    def __init__(self, address, links):
        """

        :param address: unique address of this Node
        :param links: list of Links (objects) this Node is connected to
        """
        self.address = address
        self.links = links

    def addLink(self, target):
        self.links.append(target)


class Host(Node):

    """ Represents a host in a network

    This class represents a host in a network that is able to receive and
    send data"""

    def __init__(self, address, links):
        super(self.__class__, self).__init__(address, links)
        self.flows = dict()
        self.flowrecipients = dict()

    def addLink(self, link):
        """ Overwrites default add link to check for single link """
        if not self.links:
            self.links.append(link)
        else:
            print "Node %d already has a link!" % self.address
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
        assert packet.dest == self.address

        # Packet is ACK, update Flow accordingly
        if packet.ack:
            assert packet.flowId in self.flows
            newpackets = self.flows[packet.flowId].receiveAckPacket(packet)
            return [PacketEvent(event.timestamp, self,
                                self.links[0], p,
                                'Flow %s, packet %s from host %s to link %s' %
                                (p.flowId, p.index,
                                    self.address, self.links[0].id))
                    for p in newpackets]

        # Treat packet as data packet, return appropriate ACK
        else:
            assert packet.flowId in self.flowrecipients

            # TODO(choutim) include packet integrity checks, maybe

            newPacket = self.flowrecipients[
                packet.flowId].receiveDataPacket(packet)
            return [PacketEvent(event.timestamp, self,
                                self.links[0], newPacket,
                                'ACK %s for flow %s from host %s to link %s' %
                                (newPacket.index, newPacket.flowId,
                                    self.address, self.links[0].id))]

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

    def __init__(self, address, links):
        super(self.__class__, self).__init__(address, links)
        self.routing_table = dict()
        # The routing table should either have a default starting state, or
        # _UpdateRoutingTable should be called once. Otherwise, the Router
        # will not be able to forward anything at all.

    def _processPacketEvent(self, event):
        """Processes packet event.

        Timestamp is not changed because there is no
        delay through the router.
        """
        return [PacketEvent(event.timestamp, self,
                            self.getRoute(event.packet.destination),
                            event.packet)]

    def _UpdateRoutingTable(self):
        """ Updates the internal routing table.

        This method should be the result of an Event that informs
        the Router to update.
        """
        # TODO(choutim) Implement at a later time.
        pass

    def getRoute(self, destination):
        """checks routing table for route to destination"""
        return self.routing_table[destination]
