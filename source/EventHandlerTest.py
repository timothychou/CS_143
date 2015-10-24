from EventHandler import EventHandler
from EventHandler import Event
from EventHandler import PacketEvent
from unittest import TestCase
from Queue import Empty

class EventHandlerTest(TestCase):
    def testEventHandlerInit(self):
        """ Test the constructor of EventHandler.

        Checks the priority queue enqueues Events in the correct order.
        """
        e1 = Event(5, 'obj', 'message')
        e2 = Event(0, 'obj', 'message')
        e3 = Event(7, 'obj', 'message')
        e4 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)
        self.assertEqual('network', eventHandler._network)
        self.assertEqual(4, eventHandler._queue.qsize())

    def testProcessEventOrder(self):
        """ Test that _processEvent returns the event with smallest timestamp.
        """
        e1 = Event(5, 'obj', 'message')
        e2 = Event(0, 'obj', 'message')
        e3 = Event(7, 'obj', 'message')
        e4 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)
        self.assertEqual(e2, eventHandler._processEvent())
        self.assertEqual(e4, eventHandler._processEvent())
        self.assertEqual(e1, eventHandler._processEvent())
        self.assertEqual(e3, eventHandler._processEvent())
        with self.assertRaises(Empty) as e:
            eventHandler._processEvent()

    def testRun(self):
        """ Test that run() handles interval and steps correctly.
        """
        e1 = Event(5, 'obj', 'message')
        e2 = Event(0, 'obj', 'message')
        e3 = Event(7, 'obj', 'message')
        e4 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')
        eventList = [e1, e2, e3, e4]

        eventHandler = EventHandler('network', eventList)
        eventHandler.run(0, 4)
        with self.assertRaises(Empty) as e:
            eventHandler.run(0, 1)


class EventTest(TestCase):
    def testEventInit(self):
        """ Test the constructor of Event.
        """
        e1 = Event(5, 'obj', 'message')
        self.assertEqual(e1._timestamp, 5)
        self.assertEqual(e1._eventObject, 'obj')
        self.assertEqual(e1._logMessage, 'message')

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
        self.assertEqual(e1._timestamp, 1)
        self.assertEqual(e1._eventObject, 'receiver3')
        self.assertEqual(e1._sender, 'sender2')
        self.assertEqual(e1._packet, 4)
        self.assertEqual(e1._logMessage, 'message5')