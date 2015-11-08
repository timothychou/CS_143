class Packet(object):
    '''This class represents a packet of data

    It can be sent between routers and hosts'''

    def __init__(self, source, dest, index, 
                 ack=False, fin=False, corrupted=False):
        """

        :param source: the address:port combination of the packet sender
        :param dest: the address:port combination of the packet recipient
        :param index: packet number, index
        :param flowId: the id of the Flow that this packet belongs to
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

        # TODO(tongcharlie) FIX SIZE IMPLEMENTATION
        self.size = 1024

class DataPacket(Packet):
    '''This class represents a packet transferring arbitrary data'''

    def __init__(self, source, dest, index, flowId,
                 ack=False, fin=False, corrupted=False):
        super(self.__class__, self).__init__(source, dest, index, ack, fin,
                                             corrupted)
        self.flowId = flowId
        self.size = 1024
        

class AckPacket(Packet):
    '''This class represents an ack packet'''

    def __init__(self, source, dest, index, 
                 ack=False, fin=False, corrupted=False):

        super(self.__class__, self).__init__(source, dest, index, 
                                             ack, fin, corrupted)
        self.ack = True
        self.size = 64

class RoutingPacket(Packet):
    '''
    This class represents a routing table packet'''
    
    def __init__(self, source, 
                 ack=False, fin=False, corrupted=False, routingTable=None):
        super(self.__class__, self).__init__(source, -1, 0,
                                             ack, fin, corrupted)
        self.size = 1024

        self.routingTable = routingTable

class RoutingRequestPacket(Packet):
    ''' This class represents a request for routing table'''

    def __init__(self, source, ack=False, fin=False, corrupted=False):

        super(self.__class__, self).__init__(source, -1, 0,
                                             ack, fin, corrupted)

        self.size = 64
