from icfire.event import LinkTickEvent, PacketEvent
from icfire.networkobjects.networkobject import NetworkObject
from icfire import logger
from Queue import Queue


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
        :param maxbuffersize: maximum buffer size (combined for both sides) (KB)
        :param linkid: id of the Link
        """
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.rate = rate
        self.delay = delay
        self.maxbuffersize = maxbuffersize
        self.id = linkid

        self.buffer = Queue()  # Queue using a cyclic array
        self.buffersizeA = 0   # size of items in the buffer for node A
        self.buffersizeB = 0   # size of items in the buffer for node B

        self.freeAt = 0

    def _processPacketEvent(self, packet_event):
        """Processes packet events, storing them in the buffer."""
        if packet_event.sender == self.nodeA:
            if self.buffersizeA + packet_event.packet.size > self.maxbuffersize * 1024:
                logger.Log('Dropping packet... %s' % packet_event.packet.index)
                return []

            self.buffer.put(packet_event)
            self.buffersizeA += packet_event.packet.size
        else:
            assert packet_event.sender == self.nodeB
            if self.buffersizeB + packet_event.packet.size > self.maxbuffersize * 1024:
                logger.Log('Dropping packet... %s' % packet_event.packet.index)
                return []

            self.buffer.put(packet_event)
            self.buffersizeB += packet_event.packet.size

        # If this is the first packet in the buffer, start the LinkTickEvents
        if self.buffer.qsize() == 1:
            return [LinkTickEvent(max(packet_event.timestamp, self.freeAt), self,
                                  'Link ' + self.id + ' processes a packet')]
        return []

    def _linkTickEvent(self, event):
        """ Dequeues a packet from the buffer and forwards it.

        Also possibly generates a new LinkTickEvent if there are more packets
        in the buffer.
        """
        packet_event = self.buffer.get()
        if packet_event.sender == self.nodeA:
            self.buffersizeA -= packet_event.packet.size
        else:
            assert packet_event.sender == self.nodeB
            self.buffersizeB -= packet_event.packet.size

        # Generate a new PacketEvent
        # Use event.timestamp because this is when the packet is actually
        # forwarded, not the PacketEvent time
        otherNode = self._otherNode(packet_event.sender)
        tick = packet_event.packet.size * 8.0 / self.rate / 1024 / 1024 * 1000
        newevents = [PacketEvent(event.timestamp + self.delay + tick,
                                 self, otherNode, packet_event.packet,
                                 'Node %s receives packet %s from link %s' %
                                 (otherNode.address,
                                  packet_event.packet.index,
                                  self.id))]

        # Make a new LinkTickEvent
        self.freeAt = event.timestamp + tick
        if self.buffer.qsize():
            newevents.append(LinkTickEvent(self.freeAt, self,
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
