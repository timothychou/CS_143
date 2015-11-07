import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler


def buildNetwork():
    """ This function builds the network for the test case """
    tc0 = Network()
    h1 = tc0.addHost("h1")
    h2 = tc0.addHost("h2")
    tc0.addLink(h1, h2, rate=10, delay=10, buffsize=64, linkid='L1')
    tc0.addFlow(h1, h2, 10000, 100, 'SuperSimpleFlow')
    # tc0.addFlow(h1, h2, 10000, 100, 'SuperSimpleFlow2')
    return tc0


if __name__ == '__main__':
    filename = 'testcase0.json'
    tc0 = buildNetwork()
    tc0.save(filename)

    tc0a = Network()
    tc0a.load(filename)
    eh = EventHandler(tc0a)
    eh.run(0, 100)
