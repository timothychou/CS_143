"""
icfire.packet
~~~~~~~~~~~~~

This module implements the base packet class and other sub packets

"""


class Packet(object):
    """This class represents a packet of data

    It can be sent between routers and hosts"""

    def __init__(self, source, dest, index, size,
                 ack=False, fin=False, corrupted=False):
        """ Constructor

        :param source: the address:port combination of the packet sender
        :param dest: the address:port combination of the packet recipient
        :param index: packet number, index
        :param size: size of packet in bytes
        :param ack: ACK flag
        :param fin: FIN flag
        :param corrupted:
        """
        self.source = source
        self.dest = dest
        self.index = index

        self.ack = ack
        self.fin = fin
        self.corrupted = corrupted

        self.size = size


class DataPacket(Packet):
    """ This class represents a packet transferring arbitrary data """

    def __init__(self, source, dest, index, flowId, timestamp=None):
        super(self.__class__, self).__init__(source, dest, index, size=1024)

        self.flowId = flowId
        self.timestamp = timestamp


class AckPacket(Packet):
    """ This class represents an ack packet """

    def __init__(self, source, dest, index, flowId, timestamp=None):
        super(self.__class__, self).__init__(
            source, dest, index, size=64, ack=True)

        self.flowId = flowId
        self.timestamp = timestamp


class RoutingPacket(Packet):
    """ This class represents a routing table packet """

    def __init__(self, source, dest, routingTable=None):
        super(self.__class__, self).__init__(
            source, dest, index=None, size=1024)

        # Routing table can fit inside 1024 bytes
        self.routingTable = routingTable


class RoutingRequestPacket(Packet):
    """ This class represents a request for routing table """

    def __init__(self, source):
        super(self.__class__, self).__init__(
            source, dest=None, index=None, size=64)
