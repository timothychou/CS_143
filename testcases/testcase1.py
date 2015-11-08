import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler


def buildNetwork():
    """ This function builds the network for the test case """
    tc0 = Network()
    h1 = tc0.addHost("H1")
    h2 = tc0.addHost("H2")
    r1 = tc0.addRouter("R1")
    r2 = tc0.addRouter("R2")
    r3 = tc0.addRouter("R3")
    r4 = tc0.addRouter("R4")
    tc0.addLink(h1, r1, rate=12.5, delay=10, buffsize=64, linkid='L0')
    tc0.addLink(r1, r2, rate=10, delay=10, buffsize=64, linkid='L1')
    tc0.addLink(r1, r3, rate=10, delay=10, buffsize=64, linkid='L2')
    tc0.addLink(r2, r4, rate=10, delay=10, buffsize=64, linkid='L3')
    tc0.addLink(r3, r4, rate=10, delay=10, buffsize=64, linkid='L4')
    tc0.addLink(r4, h2, rate=12.5, delay=10, buffsize=64, linkid='L5')
    tc0.addFlow(h1, h2, bytes=20000000, timestamp=500, flowType='SuperSimpleFlow')
    return tc0


if __name__ == '__main__':
    filename = 'testcase1.json'
    tc0 = buildNetwork()
    tc0.save(filename)
    tc0.draw()

    # tc0a = Network()
    # tc0a.load(filename)
    # eh = EventHandler(tc0a)
    # eh.run(0, 100)
