from Queue import PriorityQueue
import time

class EventHandler:
    def __init__(self, network, initialEvents):
        """ Constructor for an EventHandler. """
        self._network = network
        self._queue = PriorityQueue()

        for e in initialEvents:
            self._queue.put(e)

    def _processEvent(self):
        """ Processes one Event from the queue, corresponding to one 'tick'.

        If the queue is empty, this will raise an Empty error.
        :return: The Event that was just processed.
        """

        # When we get an object from the queue, do not block if empty. This may be changed later.
        event = self._queue.get(block=False)
        event.doEvent()
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
                self._processEvent()
        else:
            for i in xrange(steps):
                self._processEvent()
                time.sleep(interval / 1000.0)


class Event(object):
    def __init__(self, timestamp, eventObject, logMessage=None):
        """ Constructor for an Event.

        :param timestamp: time (integer) representing when the Event occurs.
        :param eventObject: object that the Event occurs on.
        :param logMessage: [optional] string describing the event for logging purposes.
        """
        self._timestamp = timestamp
        self._eventObject = eventObject
        self._logMessage = logMessage

    def __cmp__(self, other):
        """ Overloaded comparison operator using timestamp for the Priority Queue.

        e1 > e2 = True if e1 has a timestamp greater than e2
        """
        return self._timestamp > other._timestamp

    def doEvent(self):
        """ Carries out the event.
        
        :return: new Events spawned by this Event.
        """
        # TODO(tongcharlie) Process Event here
        pass


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
        self._sender = sender
        self._packet = packet

    def doEvent(self):
        """ Carries out the event.

        :return: new Events spawned by this Event.
        """
        # TODO(tongcharlie) Process Event here
        pass