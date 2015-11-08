''' Unit tests for the network construction '''
import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))

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
        network1.addFlow(a, c, bytes=1000, timestamp=1,
                         flowType="SuperSimpleFlow")

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
        network1.addFlow(a, c, bytes=1000, timestamp=1,
                         flowType="SuperSimpleFlow")
        network1.save(filename)

        # Load dataset
        network1.save(filename)
        network2 = Network()
        network2.load(filename)
        print(network2.nodes[2])
        print(network2.nodes[2].links)

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
        N.addFlow(a, c, bytes=1000, timestamp=1,
                         flowType="SuperSimpleFlow")
        self.assertEqual(len(N.getNodeList()), 3)
        self.assertEqual(len(N.getLinkList()), 2)


if __name__ == '__main__':
    unittest.main()
