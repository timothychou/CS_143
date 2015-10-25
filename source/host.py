class Host(Node):

    ''' Represents a host in a network

    This class represents a host in a network that is able to receive and 
    send data'''


    def __init__(self, links, id):
        assert len(links) == 1
        self = super(Host, self).__init__(links, id)

    def processEvent(self, events):
        ''' Processes events
        
        '''
        newEvents = []
        for event in events:
            if isInstance(event, PacketEvent):
                newEvents.append(self.processPacketEvent(event))
        return newEvents

    def processPacketEvent(self, event):
        '''Processes packet event
        
        sends back an ack as needed'''
        packet = event.packet
        if (packet.ack == False and packet.corrupted == False):
            newPacket = new Packet(packet.dest, packet.source, ack=True)
        return new PacketEvent(event.timestamp, self, self.links[0],
                               newPacket)

    def sendPackets(self, numPackets, dest, timestamp):
        '''Send numPackets packets to destination dest'''
        events = []
        for i in xrange(len(numPackets)):
            packet = new Packet(self.id, dest, i)
            events.append(new PacketEvent(timestamp, self, self.links[0],
                                          packet))
        return events

                    
        



        


        
