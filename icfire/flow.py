from packet import Packet


class Flow(object):

    """ Abstract class representing a Flow from one host to another.

    There are many types of Flows governed by different congestion control
    algorithms.
    """

    def __init__(self):
        raise NotImplementedError(
            'Flow should never be instantiated.')

    def receiveAckPacket(self, packet):
        """ Alter the flow based on the ACK packet received.

        This should only be called on the sender Flow.

        :param packet: The ACK packet received
        """
        raise NotImplementedError('This should be overriden by subclass')


class FlowRecipient(object):

    """ Class for the Flow recipient to manage the Flow. """

    def __init__(self, flowId):
        self.flowId = flowId

        self.received = []  # List of received packet indices
        self.lastAck = 0    # Last ack index sent (expected next packet index)

    def receiveDataPacket(self, packet):
        """ Note the received packet and respond with the appropriate ACK packet

        :param packet: received data packet
        :return: new ACK packet
        """
        self.received.append(packet.index)
        while self.lastAck in self.received:
            self.received.remove(self.lastAck)
            self.lastAck += 1

        return Packet(packet.dest, packet.source, self.lastAck,
                      packet.flowId, ack=True)


class SuperSimpleFlow(Flow):

    """ The most basic type of Flow with window size 1. """

    def __init__(self, bytes, otherHost, flowId):
        """ Create a new Flow

        :param bytes: bytes to send (0 for continuous)
        :param otherHostAddr: address of the other host
        :param flowId: id of the flow
        :return:
        """
        self.bytes = bytes
        self.otherHost = otherHost
        self.flowId = flowId

        self.lastAck = 0    # last received ACK number
        self.lastSent = -1  # last packet index sent

    def receiveAckPacket(self, packet):
        """ A new ACK received means that the next packet can be sent.
        """
        raise NotImplementedError('This should be overriden by subclass')
