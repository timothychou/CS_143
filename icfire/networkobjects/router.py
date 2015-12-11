"""
icfire.router
~~~~~~~~~~~~~

This module represents the routers
"""

from icfire.event import PacketEvent, UpdateRoutingTableEvent
from icfire.networkobjects.networkobject import Node
from icfire.packet import RoutingPacket, RoutingRequestPacket, DataPacket, AckPacket
from icfire import logger


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
        # dict with link -> dict with key=dest, val=dist
        self.link_table = dict()
        # The routing table should either have a default starting state, or
        # _UpdateRoutingTable should be called once. Otherwise, the Router
        # will not be able to forward anything at all.

    def _processPacketEvent(self, event):
        """ Process a PacketEvent

        Timestamp is not changed because there is no
        delay through the router.

        :param packet_event: PacketEvent to process
        :return: new Events to enqueue
        """

        # Data packet, forward to correct link
        if isinstance(event.packet, DataPacket) or \
                isinstance(event.packet, AckPacket):
            nextLink = self.getRoute(event.packet.dest)
            if nextLink:
                logger.log('Router %s forwards packet to %s' %
                           (self.address, nextLink.id))
                return nextLink.addPackets([event.packet], self)
            else:
                logger.log('Router %s dropped packet %s' %
                           (self.address, event.packet.index))

        # Received routing table information, update table
        elif isinstance(event.packet, RoutingPacket):
            neighborTable = event.packet.routingTable
            link = event.sender
            cost = link.cost()

            # overwrite previous
            self.link_table[link] = dict()
            for dest in neighborTable:
                # split horizon to avoid cycles
                if neighborTable[dest][0] != link:
                    self.link_table[link][dest] = neighborTable[dest][1] + cost

            # add dests to routing_table
            for dest in self.link_table[link]:
                if dest not in self.routing_table:
                    self.routing_table[dest] = (link, self.link_table[link][dest])

            # reset all and recalculate
            for dest in self.routing_table:
                self.routing_table[dest] = (None, 999999)
                for link in self.link_table:
                    if dest in self.link_table[link] and self.link_table[link][dest] < self.routing_table[dest][1]:
                        self.routing_table[dest] = (link, self.link_table[link][dest])

        # Received routing table request
        elif isinstance(event.packet, RoutingRequestPacket):
            # process request for routing table
            logger.log('Routing table packet for router %s' % self.address)
            return event.sender.addPackets(
                [RoutingPacket(self.address, event.packet.source,
                               routingTable=self.routing_table)], self)

        # Else we don't know what to do
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.packet.__class__)

        return []

    def _processOtherEvent(self, event):
        """ Process other types of Events.

        Routers can handle UpdateRoutingTableEvents too

        :param packet_event: Event to process
        :return: new Events to enqueue
        """

        if isinstance(event, UpdateRoutingTableEvent):
            return self._updateRoutingTable(event)
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.__class__)

    def _updateRoutingTable(self, event):
        """ Updates the internal routing table.

        This method should be the result of an Event that informs
        the Router to update. Begins bellman ford on all nodes in the graph

        :param packet_event: UpdateRoutingTableEvent
        :return: new Events to enqueue
        """
        packetevents = \
            [PacketEvent(event.timestamp + i * 10, self, self.links[i],
                         RoutingRequestPacket(self.address),
                         'Routing table request packet for router %s'
                         % self.address)
             for i in xrange(len(self.links))]

        packetevents.append(
            UpdateRoutingTableEvent(event.timestamp + 5000, self,
                                    'Router %s updates routing table'
                                    % self.address))
        return packetevents

    def getRoute(self, destination):
        """ Check routing table to see how to get to destination

        :param destination: Host to send to
        :return: Link to forward to
        """

        if destination in self.routing_table:
            return self.routing_table[destination][0]
        return None
