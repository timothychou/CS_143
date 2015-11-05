''' Unit tests for the network construction '''
import sys
sys.path.append("C:\Users\Kevin\Documents\GitHub\CS_143")

import unittest
from icfire.network import *


class NetworkTest(unittest.TestCase):

    def testCreate(self):
        network1 = Network()
        a = network1.addHost()
        b = network1.addRouter()
        c = network1.addHost()
        network1.addLink(a, b, rate=4000, delay=3)
        network1.addLink(b, c, rate=700, delay=1000)
        network1.addEvent(a, c, 1000000, 1)

        self.assertEqual(len(network1.events), 1)
        self.assertEqual(len(network1.events), 1)

    def testImport(self):
        # Generate data file
        filename = 'testfile.json'
        network1 = Network()
        a = network1.addHost()
        b = network1.addRouter()
        c = network1.addHost()
        self.assertEqual(a, 0)
        self.assertEqual(b, 1)
        self.assertEqual(c, 2)
        network1.addLink(a, b, rate=4000, delay=3)
        network1.addLink(b, c, rate=700, delay=1000)
        network1.addEvent(a, c, 1000000, 1)
        network1.save(filename)

        # Load dataset
        network1.save(filename)
        network2 = Network()
        network2.load(filename)
        self.assertIn('events', network2.G.graph)
        self.assertEqual(len(network2.events), 1)

    def testGets(self):
        N = Network()
        self.assertEqual(N.getNewNodeId(), 0)
        self.assertEqual(N.getNewNodeId(), 0)
        a = N.addHost()
        b = N.addRouter()
        c = N.addHost()
        self.assertEqual(N.getNewNodeId(), 3)
        N.addLink(a, b, rate=4000, delay=3)
        N.addLink(b, c, rate=700, delay=1000)
        N.addEvent(a, c, 1000000, 1)
        self.assertEqual(len(N.getNodeList()), 3)
        self.assertEqual(len(N.getLinkList()), 2)


if __name__ == '__main__':
    unittest.main()
