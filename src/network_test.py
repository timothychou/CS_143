''' Unit test for the network construction'''

import unittest
from network import *


class NetworkTest(unittest.TestCase):

    def testcreate(self):
        network1 = Network()
        a = network1.addHost()
        b = network1.addRouter()
        c = network1.addHost()
        network1.addLink(a, b, rate=4000, latency=3)
        network1.addLink(b, c, rate=700, latency=1000)
        network1.addEvent(a, c, 1000000, 1)

        self.failUnlessEqual(len(network1.events), 1)
        self.failUnlessEqual(len(network1.events), 1)

    def testimport(self):
        # Generate data file
        filename = 'testfile.json'
        network1 = Network()
        a = network1.addHost()
        b = network1.addRouter()
        c = network1.addHost()
        self.failUnlessEqual(a, 0)
        self.failUnlessEqual(b, 1)
        self.failUnlessEqual(c, 2)
        network1.addLink(a, b, rate=4000, latency=3)
        network1.addLink(b, c, rate=700, latency=1000)
        network1.addEvent(a, c, 1000000, 1)
        network1.save(filename)

        # Load dataset
        network1.save(filename)
        network2 = Network()
        network2.load(filename)
        assert('events' in network2.G.graph)
        assert(len(network2.events) == 1)

    def testgets(self):
        N = Network()
        self.failUnlessEqual(N.getNewNodeId(), 0)
        self.failUnlessEqual(N.getNewNodeId(), 0)
        a = N.addHost()
        b = N.addRouter()
        c = N.addHost()
        self.failUnlessEqual(N.getNewNodeId(), 3)
        N.addLink(a, b, rate=4000, latency=3)
        N.addLink(b, c, rate=700, latency=1000)
        N.addEvent(a, c, 1000000, 1)
        self.failUnlessEqual(len(N.getNodeList()), 3)
        self.failUnlessEqual(len(N.getLinkList()), 2)




if __name__ == '__main__':
    unittest.main()
