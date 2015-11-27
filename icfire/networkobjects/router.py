import sys
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
        # dict with link object as key, list of dest addresses as values
        self.lookup_table = dict()
        # The routing table should either have a default starting state, or
        # _UpdateRoutingTable should be called once. Otherwise, the Router
        # will not be able to forward anything at all.

    def _processPacketEvent(self, event):
        """Processes packet event.

        Timestamp is not changed because there is no
        delay through the router.
        """

        # Data packet, forward to correct link
        if isinstance(event.packet, DataPacket) or isinstance(event.packet, AckPacket):
            nextLink = self.getRoute(event.packet.dest)
            if nextLink:
                return [PacketEvent(event.timestamp, self,
                                    nextLink, event.packet,
                                    'Router %s forwards packet to %s' % (self.address, nextLink.id))]
            else:
                logger.log('Router %s dropped packet %s' % (self.address, event.packet.index))

        # Received routing table information, update table
        elif isinstance(event.packet, RoutingPacket):
            neighborTable = event.packet.routingTable
            link = event.sender
            cost = link.cost()
            # overwrite parts of routing table that use neighbor 
            # where neighbor changed
            for dest in self.lookup_table.get(link, []):
                self.routing_table[dest] = [link, 
                                            neighborTable[dest][1] + cost]
            
            # update new mins
            for dest, val in neighborTable.iteritems():
                if self.routing_table.get(dest, [0, sys.maxint])[1] > (val[1] + cost):
                    if dest in self.routing_table:
                        self.lookup_table[self.routing_table[dest][0]].remove(dest)

                    self.routing_table[dest] = [link, val[1] + cost]
                    self.lookup_table[link] = self.lookup_table.get(link, []) + [dest]

            # logger.log3(self.address + ' ' + str(self.routing_table))

        # Received routing table request
        elif isinstance(event.packet, RoutingRequestPacket):
            # process request for routing table
            return [PacketEvent(event.timestamp, self, event.sender,
                                RoutingPacket(self.address, event.packet.source,
                                              routingTable=self.routing_table),
                                'Routing table packet for router %s' % self.address)]

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
        return [PacketEvent(event.timestamp + i*10, self, self.links[i],
                            RoutingRequestPacket(self.address),
                            'Routing table request packet for router %s' % self.address)
                for i in xrange(len(self.links))] + \
               [UpdateRoutingTableEvent(event.timestamp + 5000, self,
                                        'Router %s updates routing table' % self.address)]

    def getRoute(self, destination):
        """checks routing table for route to destination"""

        if destination in self.routing_table:
            return self.routing_table[destination][0]
        return None
