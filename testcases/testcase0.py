import sys
sys.path.append("C:\Users\Kevin\Documents\GitHub\CS_143")

from icfire.network import Network
from icfire.eventhandler import EventHandler


def buildNetwork():
    """ This function builds the network for the test case """
    tc0 = Network()
    h1 = tc0.addHost("H1")
    h2 = tc0.addHost("H2")
    tc0.addLink(h1, h2)
    tc0.addEvent(h1, h2, 20, 1000)
    return tc0


if __name__ == '__main__':
    tc0 = buildNetwork()
    eh = EventHandler(tc0)
    eh.run(0, 100)
