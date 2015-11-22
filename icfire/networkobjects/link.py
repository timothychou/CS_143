from networkobject import *
from packet import *
from eventhandler import *
import logger


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
        return self.buffersize * self.delay / self.rate / self.maxbuffersize
