""" The EventHandler, Event objects.

EventHandler manages queueing Events and processing them in sequential order.

The Event object represents any form of an Event that occurs non-instantaneously.

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


class EventHandler:
    def __init__(self, network, initialEvents):
        """ Constructor for an EventHandler. """
        self._network = network
        self._queue = PriorityQueue()

        for e in initialEvents:
            self._queue.put(e)

    def step(self):
        """ Processes one Event from the queue, corresponding to one 'tick'.

        If the queue is empty, this will raise an Empty error.
        :return: The Event that was just processed.
        """

        # When we get an object from the queue, do not block if empty.
        # Simply raise an Empty exception. This may be changed later.
        event = self._queue.get(block=False)

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

        # If interval is 0 we branch and do not sleep because Python is interpreted and sucks shit at optimizing.
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

    def __cmp__(self, other):
        """ Overloaded comparison operator using timestamp for the Priority Queue.

        e1 > e2 = True if e1 has a timestamp greater than e2
        """
        return self.timestamp > other.timestamp


class PacketEvent(Event):
    def __init__(self, timestamp, sender, receiver, packet, logMessage=None):
        """ Constructor for a PacketEvent.

        :param timestamp: time (integer) representing when the Event occurs.
        :param sender: sender of the packet.
        :param receiver: receiver of the packet.
        :param packet: actual packet being sent.
        :param logMessage: [optional] string describing the event for logging purposes.
        """
        super(self.__class__, self).__init__(timestamp, receiver, logMessage)
        self.sender = sender
        self.packet = packet
