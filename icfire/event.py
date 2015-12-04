# -*- coding: utf-8 -*-

"""
icfire.events
~~~~~~~~~~~~~

This module contains the event base class and all events that belong in the
eventhandler. Events are used to time actions such delays

"""


class Event(object):

    def __init__(self, timestamp, eventObject, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param eventObject: object that the Event occurs on.
        :param logMessage: [optional] string describing the event for
            logging purposes.
        """
        self.timestamp = timestamp
        self.eventObject = eventObject
        self.logMessage = logMessage
        if not self.logMessage:
            self.logMessage = 'An %s event took place at %d on object %s' % (
                self.__class__, timestamp, eventObject)

        # Keep track of order that Events are created to break ties for
        # timestamps
        self._id = getUniqueEventId()

    def __cmp__(self, other):
        """ Overloaded comparison operator using timestamp for the Priority Queue.

        e1 > e2 = True if e1 has a timestamp greater than e2
        """
        if self.timestamp == other.timestamp:
            return self._id > other._id     # Use _id to break ties.
        return self.timestamp > other.timestamp


class PacketEvent(Event):

    """ Event related to a Packet being received. """

    def __init__(self, timestamp, sender, receiver, packet, logMessage=None):
        """ Constructor for a PacketEvent.

        :param timestamp: time (integer) representing when the Event occurs.
        :param sender: sender of the packet (object).
        :param receiver: receiver of the packet (object).
        :param packet: actual packet being sent.
        :param logMessage: [optional] string describing the event for
            logging purposes.
        """

        super(self.__class__, self).__init__(timestamp, receiver, logMessage)
        self.sender = sender
        self.packet = packet


class UpdateFlowEvent(Event):

    """ Event that tells the Host to check on the Flow status (e.g. timeout).
    """

    def __init__(self, timestamp, host, flowId, logMessage=None):
        """ Constructor for an UpdateFlowEvent.

        :param timestamp: time (integer) representing when the Event occurs.
        :param host: Host that owns the Flow.
        :param flowId: id of the Flow to check up on.
        :param logMessage: [optional] string describing the event for
            logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, host, logMessage)
        self.flowId = flowId

class UpdateWindowEvent(Event):

    """ Event that tells flow to update window size for fast-tcp
    """

    def __init__(self, timestamp, flow, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param router: flow that needs to update its window size
        :param logMessage: [optional] string describing the event for logging
        """
        super(self.__class__, self).__init__(timestamp, flow, logMessage)

class UpdateRoutingTableEvent(Event):

    """ Event that tells router to update routing table """

    def __init__(self, timestamp, router, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param router: router that needs to update its routing table
        :param logMessage; [optional] string describing the event for logging
        """
        super(self.__class__, self).__init__(timestamp, router, logMessage)


class LinkTickEvent(Event):

    """ Event that tells the Link to send another Packet from its buffer. """

    def __init__(self, timestamp, link, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param link: Link that needs to send another packet.
        :param logMessage: [optional] string describing the event for
            logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, link, logMessage)


# Will deprecate
class GatherDataEvent(Event):

    """ Event that tells the Network to gather networkobject data. """

    def __init__(self, timestamp, network, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param network: Network to gather data for.
        :param logMessage: [optional] string describing the event for
            logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, network, logMessage)


globalid = 0


def getUniqueEventId():
    """ A cheap hack to order the Events secondarily based on creation order """
    global globalid
    globalid += 1
    return globalid
