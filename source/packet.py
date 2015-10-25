class Packet(object):
    '''This class represents a packet of data

    It can be sent betweem routers and hosts'''





    def __init__(self, source, dest, id, ack=False, 
                 fin=False, corrupted=False):
        self.source_port = source
        self.dest_port = dest
        self.id = id
        self.ack = ack
        self.fin = fin
        self.corrupted = corrupted
