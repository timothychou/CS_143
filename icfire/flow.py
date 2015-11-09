from packet import AckPacket
from packet import DataPacket


class Flow(object):

    """ Abstract class representing a Flow from one host to another.

    There are many types of Flows governed by different congestion control
    algorithms.
    """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """
        raise NotImplementedError(
            'Flow class should never be instantiated.')

    def receiveAckPacket(self, packet):
        """ Alter the flow state based on the ACK packet received.

        Returns a list of new packets to send

        :param packet: The ACK packet received
        :return: A list of new packets
        """
        raise NotImplementedError('This should be overriden by subclass')

    def sendPackets(self):
        """ Try to send packets to send based on the current state of the Flow

        :return: A list of new packets
        """
        raise NotImplementedError('This should be overriden by subclass')


class SuperSimpleFlow(Flow):

    """ The most basic type of Flow with window size 1."""

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """
        self.source_id = source_id
        self.dest_id = dest_id
        self.bytes = bytes
        self.flowId = flowId

        self.lastAck = 0    # last received ACK number
        self.lastSent = -1  # last packet index sent

    def receiveAckPacket(self, packet):
        """ A new ACK number means that the next packet can be sent.

        :param packet: The ACK packet received
        :return: A list of new packets
        """
        assert packet.ack
        if packet.index > self.lastAck:
            self.lastAck = packet.index
        return self.sendPackets()

    def sendPackets(self):
        """ Send a packet if window size allows it

        :return: A list of new packets
        """
        if self.lastAck > self.lastSent:
            assert self.lastAck == self.lastSent + 1
            self.lastSent += 1
            return [DataPacket(self.source_id, self.dest_id,
                               self.lastSent, self.flowId)]

        return []


class SuperSimpleFlow2(Flow):

    """ Flow with window size 2. No resending packets """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """
        self.source_id = source_id
        self.dest_id = dest_id
        self.bytes = bytes
        self.flowId = flowId

        self.windowsize = 60

        self.acks = [0]
        self.inflight = []

    def receiveAckPacket(self, packet):
        """ A new ACK number means that the next packet can be sent.

        :param packet: The AckPacket received
        :return: A list of new packets
        """
        assert isinstance(packet, AckPacket)
        self.acks.append(packet.index)
        if packet.index - 1 in self.inflight:
            self.inflight.remove(packet.index - 1)
        return self.sendPackets()

    def sendPackets(self):
        """ Send packets if window size allows it

        :return: A list of new packets
        """
        lastack = self.acks[len(self.acks) - 1]

        newpackets = []
        while len(self.inflight) < self.windowsize:
            for i in range(self.windowsize):
                if lastack + i not in self.inflight:
                    newpackets.append(DataPacket(self.source_id, self.dest_id,
                                                 lastack + i, self.flowId))
                    self.inflight.append(lastack + i)
                    break

        return newpackets


class FlowRecipient(object):

    """ Class for the Flow recipient to manage the Flow. """

    def __init__(self, flowId):
        self.flowId = flowId

        self.received = []  # List of received packet indices
        self.lastAck = 0    # Last ack index sent (expected next packet index)

    def receiveDataPacket(self, packet):
        """ Note the received packet and respond with the appropriate ACK packet

        :param packet: received data packet
        :return: new AckPacket
        """
        self.received.append(packet.index)
        while self.lastAck in self.received:
            self.received.remove(self.lastAck)
            self.lastAck += 1

        return AckPacket(packet.dest, packet.source, self.lastAck, packet.flowId)
