class Packet(object):
    '''This class represents a packet of data

    It can be sent between routers and hosts'''

    def __init__(self, source, dest, index, ack=False,
                 fin=False, corrupted=False):
        """

        :param source: the address:port combination of the packet sender
        :param dest: the address:port combination of the packet receipient
        :param index: packet number, index
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
