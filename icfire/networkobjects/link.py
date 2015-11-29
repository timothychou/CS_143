from icfire.event import LinkTickEvent, PacketEvent
from icfire.networkobjects.networkobject import NetworkObject
from icfire import logger
from icfire.stats import LinkStats
from Queue import Queue
import icfire.timer as timer


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
        self.maxbuffersize = maxbuffersize * 1024
        self.id = linkid

        self.buffer = Queue()  # Queue using a cyclic array
        self.buffersize = 0    # size of items in the buffer, bytes

        self.freeAt = 0
        self.stats = LinkStats(self.id)

    def addPackets(self, packets, sender):
        """ Add packets and return new Events if any.

        A shortcut for sending PacketEvents and having them go through the EventHandler

        :param packets: new packets to add
        :return: new Events
        """
        newevents = []

        # If this is the first packet in the buffer, start the LinkTickEvents
        if self.buffer.qsize() == 0 and len(packets) > 0:
            newevents = [
                LinkTickEvent(max(timer.time, self.freeAt), self,
                              'Link ' + self.id + ' processes a packet')]

        for i, p in enumerate(packets):
            if self.buffersize + p.size > self.maxbuffersize:
                # Drop em' like its hot
                logger.log('Dropping packet %s from host %s at link %s' %
                           (p.index, p.source, self.id))
                self.stats.addLostPackets(timer.time, 1)
                continue
            else:
                self.buffer.put((p, sender))
                self.buffersize += p.size

        return newevents

    def _processPacketEvent(self, packet_event):
        """Processes packet events, storing them in the buffer."""
        if self.buffersize + packet_event.packet.size > self.maxbuffersize:
            self.stats.addLostPackets(packet_event.timestamp, 1)
            logger.log('Dropping packet %s from host %s at link %s' %
                       (packet_event.packet.index,
                        str(packet_event.sender), self.id))
            return []

        self.buffer.put((packet_event.packet, packet_event.sender))
        self.buffersize += packet_event.packet.size

        # If this is the first packet in the buffer, start the LinkTickEvents
        if self.buffer.qsize() == 1:
            linkevent = LinkTickEvent(max(packet_event.timestamp, self.freeAt),
                                      self,
                                      'Link ' + self.id + ' processes a packet')
            return [linkevent]
        return []

    def _linkTickEvent(self, event):
        """ Dequeues a packet from the buffer and forwards it.

        Also possibly generates a new LinkTickEvent if there are more packets
        in the buffer.
        """
        packet, sender = self.buffer.get()
        self.buffersize -= packet.size

        # Generate a new PacketEvent
        # Use event.timestamp because this is when the packet is actually
        # forwarded, not the PacketEvent time
        otherNode = self._otherNode(sender)
        tick = 125.0 / 16384 * packet.size / self.rate
        type = 'ACK' if packet.ack else 'packet'
        newevents = [PacketEvent(event.timestamp + self.delay + tick,
                                 self, otherNode, packet,
                                 'Node %s receives %s %s from link %s' %
                                 (otherNode.address, type, packet.index, self.id))]
        self.stats.addBytesFlowed(event.timestamp, packet.size)
        # Make a new LinkTickEvent to time the next dequeue event
        self.freeAt = event.timestamp + tick
        if not self.buffer.empty():
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
        return self.delay + 125.0 / 16384 * self.buffersize / self.rate
