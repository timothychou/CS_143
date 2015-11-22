from icfire.networkobjects.networkobject import Node
from icfire.packet import *
from icfire.eventhandler import *
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
