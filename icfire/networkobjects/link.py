"""
icfire.networkobjects.link
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the objects that represent links in the network.
Links connect different nodes and have buffers, data rates, and some sort
of delay

"""

from Queue import Queue

from icfire.event import LinkTickEvent, PacketEvent
from icfire.networkobjects.networkobject import NetworkObject
from icfire import logger
from icfire.stats import LinkStats
import icfire.simtimer as simtimer


class Link(NetworkObject):
    """ Represents link in a network

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
        self.totalbuffersize = 0  # total size of items in the buffer, bytes
        self.buffersizes = dict()  # size of items in buffer for A, B in bytes
        self.buffersizes[self.nodeA] = 0
        self.buffersizes[self.nodeB] = 0

        self.freeAt = -9999999 # Next time the Link is free
        self.stats = LinkStats(self.id)

    def addPackets(self, packets, sender):
        """ Add packets and return new Events if any.

        A shortcut for sending PacketEvents and so they do not go through
        the EventHandler

        :param packets: new packets to add
        :return: new Events
        """
        newevents = []

        # If this is the first packet in the buffer, start the LinkTickEvents
        if self.buffer.qsize() == 0 and len(packets) > 0:
            newevents = [
                LinkTickEvent(max(simtimer.simtime, self.freeAt), self,
                              'Link ' + self.id + ' processes a packet')]

        for p in packets:
            if self.buffersizes[sender] + p.size > self.maxbuffersize:
                # Drop em' like its hot
                logger.log('Dropping packet %s from host %s at link %s' %
                           (p.index, p.source, self.id))
                self.stats.addLostPackets(simtimer.simtime, 1)
            else:
                self.buffer.put((p, sender))
                self.totalbuffersize += p.size
                self.buffersizes[sender] += p.size

        self.stats.updateBufferOccupancy(simtimer.simtime, self.totalbuffersize)

        return newevents

    def _processPacketEvent(self, packet_event):
        """ Processes packet events, storing them in the buffer.

        :param packet_event: PacketEvent to process (packet to insert)
        :return: new Events to enqueue
        """
        packet, sender = packet_event.packet, packet_event.sender
        if self.buffersizes[sender] + packet.size > self.maxbuffersize:
            self.stats.addLostPackets(packet_event.timestamp, 1)
            logger.log('Dropping packet %s from host %s at link %s' %
                       (packet.index, str(sender), self.id))
            return []

        self.buffer.put((packet, sender))
        self.totalbuffersize += packet.size
        self.buffersizes[sender] += packet.size
        self.stats.updateBufferOccupancy(simtimer.simtime, self.totalbuffersize)

        # If this is the first packet in the buffer, start the LinkTickEvents
        if self.buffer.qsize() == 1:
            linkevent = LinkTickEvent(max(packet_event.timestamp, self.freeAt),
                                      self, 'Link ' + self.id + ' processes a packet')
            return [linkevent]
        return []

    def _linkTickEvent(self, event):
        """ Dequeues a packet from the buffer and forwards it.

        Also possibly generates a new LinkTickEvent if there are more packets
        in the buffer.

        :param event: LinkTickEvent to process
        :return: new Events to enqueue
        """
        packet, sender = self.buffer.get()
        self.totalbuffersize -= packet.size
        self.buffersizes[sender] -= packet.size
        self.stats.updateBufferOccupancy(simtimer.simtime, self.totalbuffersize)

        # Generate a new PacketEvent
        # Use event.timestamp because this is when the packet is actually
        # forwarded, not the PacketEvent time
        otherNode = self._otherNode(sender)
        tick = 125.0 / 16384 * packet.size / self.rate  # convert bytes to ms
        type = 'ACK' if packet.ack else 'packet'
        newevents = [
            PacketEvent(event.timestamp + self.delay + tick,
                        self, otherNode, packet,
                        'Node %s receives %s %s from link %s' %
                        (otherNode.address, type, packet.index, self.id))]
        self.stats.addBytesFlowed(event.timestamp, packet.size)
        # Make a new LinkTickEvent to time the next dequeue event
        self.freeAt = event.timestamp + tick
        if not self.buffer.empty():
            newevents.append(
                LinkTickEvent(self.freeAt, self,
                              'Link %s processes a packet' % self.id))

        return newevents

    def _processOtherEvent(self, event):
        """ Processes non-packet events

        :param event: Event to process
        :return: new Events to enqueue
        """
        if isinstance(event, LinkTickEvent):
            return self._linkTickEvent(event)
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.__class__)

    def _otherNode(self, node):
        """ Returns the other node the link is connected to

        :param node: nodeA or nodeB
        :return: nodeB or nodeA (opposite of parameter node)
        """
        return self.nodeB if node == self.nodeA else self.nodeA

    def cost(self):
        """ Return cost of going through the edge

        :return: cost, in ms
        """
        return self.delay + 125.0 / 16384 * self.totalbuffersize / self.rate
