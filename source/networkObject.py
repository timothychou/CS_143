from source.eventhandler import PacketEvent
from source.eventhandler import Event
from packet import Packet


class NetworkObject(object):
    """abstract class for all network objects"""

    def processEvent(self, events):
        """Processes events

        Input: list of events from the event processor
        Output: list of new events to enqueu in event processor"""

        raise NotImplementedError('subclasses should override processEvent')


class Link(NetworkObject):
    """Represents link in a network

    This class represents a link in a network that packets can travel
    across"""

    def __init__(self, nodeA, nodeB, latency, speed):
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.latency = latency
        self.speed = speed

    def processEvent(self, event):
        """ Processes one event.

        Links should receive ONLY PacketEvents. Any other Event passed will raise an AssertionError.

        :param event: Event to be processed.
        :return: list of new Events to be enqueued.
        """
        assert type(event) is PacketEvent

        newEvents = []
        newtimestamp = event.timestamp + self.latency
        return self._processPacketEvent(event, newtimestamp)

    def _processPacketEvent(self, packet_event, newtimestamp):
        """Processes packet events.

        Creates a new PacketEvent of the host receiving the packet at some time in the future.
        """
        return PacketEvent(newtimestamp,
                           self, self._otherNode(packet_event.sender),
                           packet_event.packet,
                           packet_event.logMessage)

    def _otherNode(self, node):
        """returns the other node the link is connected to"""
        return self.nodeB if node == self.nodeA else self.nodeB


class Node(NetworkObject):
    """ Abstract class that represents a node in a network

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

    def processEvent(self, event):
        """ Processes one event, depending on what the event is.

        This method should be called directly or indirectly by an EventHandler.

        :param event: Event to be processed.
        :return: list of new Events to be enqueued.
        """
        if type(event) is PacketEvent:
            return self._processPacketEvent(event)
        elif type(event) is Event:
            # Generic Event, implementation not handled yet.
            raise NotImplementedError('Host not able to handle generic Event yet')
        else:
            # Not an Event...
            pass

    def _processPacketEvent(self, event):
        """Processes packet event

        sends back an ack as needed"""
        packet = event.packet
        # TODO (choutim) Verify that this Host is the proper recipient of the packet (use packet.dest)
        if not packet.ack and not packet.corrupted:
            newPacket = Packet(packet.dest, packet.source, ack=True)
            return PacketEvent(event.timestamp, self, self.links[0], newPacket)

    def sendPackets(self, numPackets, dest, timestamp):
        """Send numPackets packets to destination dest.

        This method should be called directly or indirectly by an EventHandler.
        """
        events = []
        for i in xrange(len(numPackets)):
            packet = Packet(self.address, dest, i)
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

    def processEvent(self, event):
        """ Processes one event, depending on what the event is.

        This method should be called directly or indirectly by an EventHandler.

        :param event: Event to be processed.
        :return: list of new Events to be enqueued.
        """
        newEvents = []
        if type(event) is PacketEvent:
            newEvents.append(self._processPacketEvent(event))
        return newEvents

    def _processPacketEvent(self, event):
        """Processes packet event.

        Timestamp is not changed because there is no latency through the router.
        """
        return PacketEvent(event.timestamp, self,
                           self.getRoute(event.packet.destination),
                           event.packet)

    def _UpdateRoutingTable(self):
        """ Updates the internal routing table.

        This method should be the result of an Event that tells informs the Router to update.
        """
        # TODO(choutim) Implement at a later time.
        pass

    def getRoute(self, destination):
        """checks routing table for route to destination"""
        return self.routing_table[destination]


