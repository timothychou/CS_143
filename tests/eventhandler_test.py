""" Unittests for EventHandler. """
import sys
sys.path.append("C:\Users\Kevin\Documents\GitHub\CS_143")

from icfire.eventhandler import EventHandler, Event, PacketEvent
from icfire.networkobject import NetworkObject
from Queue import Empty

import unittest


class NetworkObjectStub(NetworkObject):

    """ A stub used for testing Event processing.

    Implements processEvent() but does nothing.
    """

    def __init__(self):
        pass

    def processEvent(self, event):
        return []


class NetworkObjectStubWithNewEvents(NetworkObject):

    """ A stub used for testing Event processing.

    Implements processEvent() and generates new Events to enqueue.

    The timestamps will start at 102 (100 + 2) and go up by 1 each time.
    """

    def __init__(self):
        self._index = 100
        pass

    def processEvent(self, event):
        self._index = self._index + 2
        return [Event(self._index, NetworkObjectStub(), 'msg1'),
                Event(self._index + 1, NetworkObjectStub(), 'msg2')]


class EventHandlerTest(unittest.TestCase):

    def testEventHandlerInit(self):
        """ Test the constructor of EventHandler.

        Checks the priority queue enqueues Events in the correct order.
        """
        stub = NetworkObjectStub()

        e1 = Event(5, stub, 'message')
        e2 = Event(0, stub, 'message')
        e3 = Event(7, stub, 'message')
        e4 = PacketEvent(1, 'sender2', stub, 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)
        self.assertEqual('network', eventHandler._network)
        self.assertEqual(4, eventHandler._queue.qsize())

    def testStepOrder(self):
        """ Test that step grabs the event with smallest timestamp.
        """
        stub = NetworkObjectStub()

        e1 = Event(5, stub, 'message')
        e2 = Event(0, stub, 'message')
        e3 = Event(7, stub, 'message')
        e4 = PacketEvent(1, 'sender2', stub, 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)

        # Test that there are 4 Events enqueued and in the correct order
        self.assertEqual(4, eventHandler._queue.qsize())
        self.assertEqual(e2, eventHandler.step())
        self.assertEqual(e4, eventHandler.step())
        self.assertEqual(e1, eventHandler.step())
        self.assertEqual(e3, eventHandler.step())

        # Test that stepping into an empty queue raises Empty
        with self.assertRaises(Empty) as e:
            eventHandler.step()

    def testStepNewEvents(self):
        """ Test that step correctly enqueues new events.
        """
        stub = NetworkObjectStubWithNewEvents()

        e1 = Event(5, stub, 'message')
        e2 = Event(0, stub, 'message')
        e3 = Event(7, stub, 'message')
        e4 = PacketEvent(1, 'sender2', stub, 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)
        self.assertEqual(e2, eventHandler.step())
        self.assertEqual(e4, eventHandler.step())
        self.assertEqual(e1, eventHandler.step())
        self.assertEqual(e3, eventHandler.step())

        # Test that there are 8 more Events enqueued and in the correct order
        self.assertEqual(8, eventHandler._queue.qsize())
        for i in xrange(102, 110):
            self.assertEqual(i, eventHandler.step().timestamp)

        # Test that stepping into an empty queue raises Empty
        with self.assertRaises(Empty) as e:
            eventHandler.step()

    def testRun(self):
        """ Test that run() handles interval and steps correctly.
        """
        stub = NetworkObjectStub()

        e1 = Event(5, stub, 'message')
        e2 = Event(0, stub, 'message')
        e3 = Event(7, stub, 'message')
        e4 = PacketEvent(1, 'sender2', stub, 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)
        eventHandler.run(0, 4)
        with self.assertRaises(Empty) as e:
            eventHandler.run(0, 1)


class EventTest(unittest.TestCase):

    def testEventInit(self):
        """ Test the constructor of Event.
        """
        e1 = Event(5, 'obj', 'message')
        self.assertEqual(e1.timestamp, 5)
        self.assertEqual(e1.eventObject, 'obj')
        self.assertEqual(e1.logMessage, 'message')

    def testEventCmp(self):
        """ Test the comparator for Events.
        """
        e1 = Event(5, 'obj', 'message')
        e2 = Event(3, 'obj', 'message')
        self.assertGreater(e1, e2)
        e3 = Event(5, 'obj', 'message')
        e4 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')
        self.assertGreater(e3, e4)

    def testPacketEventInit(self):
        """ Test the constructor of PacketEvent.
        """
        e1 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')
        self.assertEqual(e1.timestamp, 1)
        self.assertEqual(e1.eventObject, 'receiver3')
        self.assertEqual(e1.sender, 'sender2')
        self.assertEqual(e1.packet, 4)
        self.assertEqual(e1.logMessage, 'message5')

if __name__ == '__main__':
    unittest.main()
