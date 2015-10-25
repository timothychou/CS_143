""" Unittests for networkobject.py """

from networkobject import NetworkObject
from networkobject import Link
from networkobject import Host
from eventhandler import Event
from eventhandler import PacketEvent
import unittest


class NetworkObjectTest(unittest.TestCase):
    def testAbstractClass(self):
        """ Tests that NetworkObject is abstract and cannot be instantiated. """
        with self.assertRaises(NotImplementedError):
            no = NetworkObject()


class LinkTest(unittest.TestCase):
    def testProcessWithNonPacketEvent(self):
        """ Tests that processEvent will fail when not passed a PacketEvent. """
        with self.assertRaises(AssertionError):
            l = Link('nodeA', 'nodeB', 5, 5)
            e = Event(5, 'obj', 'message')
            l.processEvent(e)
        e2 = PacketEvent(1, 'sender2', 'receiver3', 4, 'message5')
        l.processEvent(e2)      # Should not fail

    def testOtherNode(self):
        """ Tests _otherNode. """
        l = Link('nodeA', 'nodeB', 5, 5)
        self.assertEqual('nodeA', l._otherNode('nodeB'))
        self.assertEqual('nodeB', l._otherNode('nodeA'))


class HostTest(unittest.TestCase):
    def testExactlyOneLink(self):
        """ Tests that Hosts can only have exactly 1 Link. """
        with self.assertRaises(AssertionError):
            Host('addr', [])
        with self.assertRaises(AssertionError):
            Host('addr', ['link1', 'link2'])
        Host('addr', ['link1'])      # Should not fail

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
            self.assertEqual(h.address, p.source)  # Host address is source of packet
            self.assertEqual('destaddr', p.dest)   # Destination is address 'destaddr'
            # Unsure how to check packet index (may change)


if __name__ == '__main__':
    unittest.main()
