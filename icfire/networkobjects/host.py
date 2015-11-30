"""
icfire.networkobjects.host
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the objects that represent computers and devices in
the real world.

Hosts own flows, and also keeps tabs on various stats through a stats objects.

"""

from icfire.event import PacketEvent, UpdateFlowEvent
from icfire.networkobjects.networkobject import Node
from icfire.packet import *
from icfire.eventhandler import *
from icfire.stats import HostStats

from icfire import logger


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
        self.stats = HostStats(address)

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
        """Processes packet events

        sends back an ack as needed"""
        packet = event.packet
        timestamp = event.timestamp
        newPackets = []
        # Record arrival of new packet
        if isinstance(packet, Packet):
            self.stats.addBytesRecieved(timestamp, packet.size)

        # Handle routing table update requests
        if isinstance(event.packet, RoutingRequestPacket):
            logger.log('Routing table packet for host %s' % self.address)
            newPacket = RoutingPacket(
                self.address, event.packet.source,
                routingTable={self.address: [self.address, 0]})
            newPackets.append(newPacket)

        # Packet is ACK, update Flow accordingly
        elif isinstance(event.packet, AckPacket):
            assert packet.dest == self.address
            assert packet.flowId in self.flows
            newPackets = self.flows[packet.flowId].receiveAckPacket(
                packet, event.timestamp)
            for p in newPackets:
                logger.log('Flow %s, packet %s from host %s to link %s' %
                           (p.flowId, p.index,
                            self.address, self.links[0].id))

        # Treat packet as data packet, return appropriate ACK
        elif isinstance(event.packet, DataPacket):
            assert packet.dest == self.address
            assert packet.flowId in self.flowrecipients

            # TODO(choutim) include packet integrity checks, maybe

            newPacket = self.flowrecipients[
                packet.flowId].receiveDataPacket(packet, event.timestamp)
            logger.log('ACK %s for flow %s from host %s to link %s' %
                       (newPacket.index, newPacket.flowId,
                        self.address, self.links[0].id))
            newPackets.append(newPacket)

        # Else we don't know what to do
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.packet.__class__)

        # Record new packets
        for p in newPackets:
            self.stats.addBytesSent(timestamp, p.size)

        return self.links[0].addPackets(newPackets, self)

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
        newpackets, rto = f.checkTimeout(t)
        packetEvents = \
            [PacketEvent(t, self, self.links[0], p,
                         'Flow %s, packet %s from host %s to link %s' %
                         (f.flowId, p.index, self.address, self.links[0].id))
             for p in newpackets]
        packetEvents.append(
            UpdateFlowEvent(t + rto, self, f.flowId,
                            'Check for timeout on flow %s' % f.flowId))
        return packetEvents
