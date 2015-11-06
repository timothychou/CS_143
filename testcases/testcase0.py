import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler


def buildNetwork():
    """ This function builds the network for the test case """
    tc0 = Network()
    h1 = tc0.addHost("AAA")
    h2 = tc0.addHost("BBB")
    tc0.addLink(h1, h2)
    tc0.addFlow(h1, h2, 10000, 100, 'SuperSimpleFlow')
    # tc0.addFlow(h1, h2, 10000, 100, 'SuperSimpleFlow2')
    return tc0


if __name__ == '__main__':
    tc0 = buildNetwork()
    eh = EventHandler(tc0)
    eh.run(0, 100)
