from eventhandler import PacketEvent
from eventhandler import Event
from packet import Packet


class NetworkObject(object):
    """abstract class for all network objects"""

    def __init__(self):
        raise NotImplementedError('NetworkObject should never be instantiated.')

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

    def __init__(self, nodeA, nodeB, latency, speed):
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.latency = latency
        self.speed = speed

    def _processPacketEvent(self, packet_event):
        """Processes packet events

        Creates a new PacketEvent of the host receiving the packet at some time in the future.
        """
        return [PacketEvent(packet_event.timestamp + self.latency,
                           self, self._otherNode(packet_event.sender),
                           packet_event.packet,
                           packet_event.logMessage)]

    def _processOtherEvent(self, event):
        """ Processes non-packet events

        Links should only get packet events, so simply raises an error
        """
        raise AssertionError('Links should receive only packet events')

    def _otherNode(self, node):
        """returns the other node the link is connected to"""
        return self.nodeB if node == self.nodeA else self.nodeA


class Node(NetworkObject):
    """ class that represents a node in a network

    This class represents a node in a network connected by edges"""

    def __init__(self, address, links):
        """

        :param address: unique address of this Node
        :param links: list of links this Node is connected to
        :return:
        """
        self.address = address
        self.links = links


class Host(Node):

    """ Represents a host in a network

    This class represents a host in a network that is able to receive and
    send data"""


    def __init__(self, address, links):
        super(self.__class__, self).__init__(address, links)
        assert len(links) == 1


    def _processPacketEvent(self, event):
        """Processes packet event

        sends back an ack as needed"""
        packet = event.packet
        assert packet.dest == self.address
        if not packet.ack and not packet.corrupted:
            newPacket = Packet(packet.dest, packet.source, ack=True)
            return [PacketEvent(event.timestamp, self,
                                self.links[0], newPacket)]
        return []

    def sendPackets(self, numPackets, dest, timestamp):
        """Send numPackets packets to destination dest.

        This method should be called directly or indirectly by an EventHandler.
        """
        events = []
        for i in xrange(numPackets):
            packet = Packet(self.address, dest, i)
            # TODO make it so packets are not all sent at the same time
            events.append(PacketEvent(timestamp, self, self.links[0], packet))
        return events


class Router(NetworkObject):
    """ Represents router in a network

    This class represents a router in a network that is able to
    route packets"""


    def __init__(self, address, links):
        super(self.__class__, self).__init__(address, links)
        assert len(links) > 0
        self.routing_table = dict()
        # The routing table should either have a default starting state, or
        # _UpdateRoutingTable should be called once. Otherwise, the Router
        # will not be able to forward anything at all.


    def _processPacketEvent(self, event):
        """Processes packet event.

        Timestamp is not changed because there is no
        latency through the router.
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


