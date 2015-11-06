""" The EventHandler, Event objects.

EventHandler manages queueing Events and processing them in sequential order.

The Event object represents any form of an Event that occurs
non-instantaneously.

Examples include:
-packet transmission
-packet generation
-updating routing tables
-generating flow

All Events have two main components: a timestamp and an eventObject.

timestamp: The time that this Event occurs (an integer).
eventObject: the object that will receive this Event occurs on.

When the timestamp is reached, the EventHandler will dequeue the Event and call
eventObject.processEvent(). It is up to the eventObject to handle the Event.
processEvent() should also return a list of new Events to enqueue.
"""

from Queue import PriorityQueue
import time
import logger


class EventHandler:

    def __init__(self, network, initialEvents=[]):
        """ Constructor for an EventHandler. """
        self._network = network
        self._queue = PriorityQueue()
        if initialEvents:
            for e in initialEvents:
                self._queue.put(e)
        elif network.events:
            for e in network.events:
                self._queue.put(e)
        else:
            print "No events queued"

    def step(self):
        """ Processes one Event from the queue, corresponding to one 'tick'.

        If the queue is empty, this will raise an Empty error.
        :return: The Event that was just processed.
        """

        # When we get an object from the queue, do not block if empty.
        # Simply raise an Empty exception. This may be changed later.
        event = self._queue.get(block=False)

        # Log each event
        logger.Log('[%6s] %s' % (event.timestamp, event.logMessage))

        newevents = event.eventObject.processEvent(event)
        for e in newevents:
            self._queue.put(e)

        return event

    def run(self, interval, steps):
        """
        :param interval: Time (milliseconds) between each step.
        :param steps:
        :return:
        """

        # If interval is 0 we branch and to avoid calling time.sleep(0)
        if interval == 0:
            for i in xrange(steps):
                self.step()
        else:
            for i in xrange(steps):
                self.step()
                time.sleep(interval / 1000.0)


class Event(object):

    def __init__(self, timestamp, eventObject, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param eventObject: object that the Event occurs on.
        :param logMessage: [optional] string describing the event for logging purposes.
        """
        self.timestamp = timestamp
        self.eventObject = eventObject
        self.logMessage = logMessage
        if not self.logMessage:
            self.logMessage = 'An Event took place at %d on object %s' % (timestamp, eventObject)

    def __cmp__(self, other):
        """ Overloaded comparison operator using timestamp for the Priority Queue.

        e1 > e2 = True if e1 has a timestamp greater than e2
        """
        return self.timestamp > other.timestamp


class PacketEvent(Event):
    """ Event related to a Packet being received. """

    def __init__(self, timestamp, sender, receiver, packet, logMessage=None):
        """ Constructor for a PacketEvent.

        :param timestamp: time (integer) representing when the Event occurs.
        :param sender: sender of the packet (object).
        :param receiver: receiver of the packet (object).
        :param packet: actual packet being sent.
        :param logMessage: [optional] string describing the event for logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, receiver, logMessage)
        self.sender = sender
        self.packet = packet


class UpdateFlowEvent(Event):
    """ Event that tells the Host to check on the Flow status (e.g. timeout). """

    def __init__(self, timestamp, host, flowId, logMessage=None):
        """ Constructor for an UpdateFlowEvent.

        :param timestamp: time (integer) representing when the Event occurs.
        :param host: Host that owns the Flow.
        :param flowId: id of the Flow to check up on.
        :param logMessage: [optional] string describing the event for logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, host, logMessage)
        self.flowId = flowId


class LinkTickEvent(Event):
    """ Event that tells the Link to send another Packet from its buffer. """

    def __init__(self, timestamp, link, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param link: Link that needs to send another packet.
        :param logMessage: [optional] string describing the event for logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, link, logMessage)
