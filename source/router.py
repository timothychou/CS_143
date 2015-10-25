class Router(Network_object):
    ''' Represents router in a network

    This class represents a router in a network that is able to 
    route packets'''


    def __init__(self, links, id):
        self.links = links
        self.id = id
        self.routing_table = dict()

    def processEvent(self, events):
        ''' Processes events

        Input: list of events from the event processor
        Output: list of new events to enqueue in event processor'''
        newEvents = []
        for event in events:
            if isInstance(event, PacketEvent):
                newEvents.append(self.processPacketEvent(event))
        return newEvents
        
    def processPacketEvent(self, event):
        '''Processes packet event'''
        return new PacketEvent(timestamp, self, 
                               self.getRoute(event.packet.destination),
                               event.packet)

    def getRoute(self, destination):
        '''checks routing table for route to destination'''
        self.routing_table[destination]
