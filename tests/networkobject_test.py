""" Unittests for networkobject.py """
import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))

from icfire.networkobject import NetworkObject, Link, Host
from icfire.eventhandler import Event, PacketEvent
import unittest


class NetworkObjectTest(unittest.TestCase):

    def testAbstractClass(self):
        """ Tests that NetworkObject is abstract and cannot be instantiated. """
        with self.assertRaises(NotImplementedError):
            NetworkObject()


class LinkTest(unittest.TestCase):

    def testProcessWithNonPacketEvent(self):
        """ Tests that processEvent will fail when not passed a PacketEvent. """
        l = Link('nodeA', 'nodeB', 5, 5)
        e = Event(5, 'obj', 'message')
        e2 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')

        with self.assertRaises(AssertionError):
            l.processEvent(e)
        l.processEvent(e2)      # Should not fail

    def testOtherNode(self):
        """ Tests _otherNode. """
        l = Link('nodeA', 'nodeB', 5, 5)
        self.assertEqual('nodeA', l._otherNode('nodeB'))
        self.assertEqual('nodeB', l._otherNode('nodeA'))


class HostTest(unittest.TestCase):

    def testSendPackets(self):
        """ Tests sendPackets generates the correct set of new Events. """
        l = Link('nodeA', 'nodeB', 5, 5)
        h = Host('hostaddr', [l])
        newevents = h.sendPackets(10, 'destaddr', 42)

        self.assertEqual(10, len(newevents))
        for e in newevents:
            self.assertEqual(h, e.sender)          # Event sender is the host
            self.assertEqual(l, e.eventObject)     # Event receiver is the link
            self.assertEqual(42, e.timestamp)      # Timestamp is 42
            p = e.packet
            # Host address is source of packet
            self.assertEqual(h.address, p.source)
            # Destination is address 'destaddr'
            self.assertEqual('destaddr', p.dest)
            # Unsure how to check packet index (may change)


if __name__ == '__main__':
    unittest.main()
