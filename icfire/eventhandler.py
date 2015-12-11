"""
icfire.eventhandler
~~~~~~~~~~~~~~~~~~~

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

from tqdm import trange

import icfire.logger as logger
import icfire.simtimer as simtimer


class EventHandler(object):

    """ The eventhandler class handles events and timers

    It is reponsible for actually running the simulation
    """

    def __init__(self, network, initialEvents=None):
        """ Constructor for an EventHandler.

        :param network: network.Network object that models the network
        :param initialEvents: List of initial events
        :return:
        """
        self._network = network
        self._queue = PriorityQueue()
        self.time = 0
        if initialEvents:
            for e in initialEvents:
                self._queue.put(e)
        elif network.events:
            for e in network.events:
                self._queue.put(e)
        else:
            print "No events queued"

    def step(self, realtime=False, slowdown=1.):
        """ Processes one Event from the queue, corresponding to one 'tick'.

        If the queue is empty, this will raise an Empty error.
        :param realtime: [optional] Set to true to simulate in real time
        :param slowdown: [optional] factor to slow down the simulation. Half the simulation rate with .5
        :return: The Event that was just processed.
        """
        # When we get an object from the queue, do not block if empty.
        # Simply raise an Empty exception. This may be changed later.
        event = self._queue.get(block=False)
        simtimer.simtime = event.timestamp

        # TODO disabled for now
        # if realtime:
        #     waittime = event.timestamp - self.time
        #     if waittime < 0:
        #         logger.Log("Error: events are not occuring in order")
        # wait for a maximum of 5 seconds
        #     time.sleep((waittime / 1000 / slowdown) % 5)

        # Log each event
        logger.log('[%10.3f][%15s] %s' %
                   (event.timestamp, event.__class__, event.logMessage))

        newevents = event.eventObject.processEvent(event)
        for e in newevents:
            self._queue.put(e)
        self.time = event.timestamp
        return event

    def completed(self):
        """ Check whether simulation is completed
        :return: true if all flows are done
        """
        for flow_id in self._network.flows:
            if not self._network.flows[flow_id].done:
                return False
        return True

    def run(self, steps=0):
        """
        :param steps: [optional] Maximum number of steps to take.
            If 0, the simulation runs until completion.
        """

        # If interval is 0 we branch and to avoid calling time.sleep(0)
        if steps == 0:
            while not self._queue.empty():
                self.step()
                if self.completed():
                    break
        else:
            for _ in trange(steps):
                self.step()
                if self.completed():
                    break
