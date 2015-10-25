class Link(Network_object):
    '''Represents link in a network

    This class represents a link in a network that packets can travel
    across'''

    def __init__(self, nodeA, nodeB, latency, speed):
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.latency = latency
        self.speed = speed

        
    def processEvent(self, events):
        ''' Processes events'''
        newEvents = []
        timestamp = events[0].timestamp
        for event in events:
            if isInstance(event, PacketEvent):
                timestamp += self.latency
                newEvents.append(self.processPacketEvent(event, timestamp))
                
        return newEvents

    def processPacketEvent(self, packet_event, timestamp):
        '''Processes packet events'''
        newEvent = new PacketEvent(timestamp,
                                   self, self.otherNode(packet_event.sender),
                                   packet_event.packet,
                                   packet_event.logMessage)
        return newEvent

    def otherNode(self, node):
        '''returns the other node the link is connected to'''
        if node == self.nodeA:
            return self.nodeB
        else:
            return self.nodeA

                             
