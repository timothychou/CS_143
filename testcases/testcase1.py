import sys
import os

import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler
import icfire.stats as stats


def buildNetwork(static_routing=False):
    """ This function builds the network for the test case

    :param static_routing whether to use dyanamic or static routing table
    """
    tc1 = Network()
    h1 = tc1.addHost("H1")
    h2 = tc1.addHost("H2")
    r1 = tc1.addRouter("R1", 0, static_routing=static_routing)
    r2 = tc1.addRouter("R2", 100, static_routing=static_routing)
    r3 = tc1.addRouter("R3", 200, static_routing=static_routing)
    r4 = tc1.addRouter("R4", 300, static_routing=static_routing)
    tc1.addLink(h1, r1, rate=12.5, delay=10, buffsize=64, linkid='L0')
    tc1.addLink(r1, r2, rate=10, delay=10, buffsize=64, linkid='L1')
    tc1.addLink(r1, r3, rate=10, delay=10, buffsize=64, linkid='L2')
    tc1.addLink(r2, r4, rate=10, delay=10, buffsize=64, linkid='L3')
    tc1.addLink(r3, r4, rate=10, delay=10, buffsize=64, linkid='L4')
    tc1.addLink(r4, h2, rate=12.5, delay=10, buffsize=64, linkid='L5')
    #flowType = 'TCPRenoFlow'
    flowType = 'FastTCPFlow'
    tc1.addFlow(h1, h2, bytes=20000000, timestamp=20000,
                flowType=flowType, flowId='F1')

    return tc1


if __name__ == '__main__':
    filename = 'testcase1.json'
    static_routing = False
    tc1 = buildNetwork(static_routing)
    # tc1.save(filename)
    # tc1.draw()

    # tc1a = Network()
    # tc1a.load(filename)

    tc1a = tc1  # todo loading/saving not 100% functional right now

    # Set routing tables manually
    if static_routing:
        tc1a.nodes['R1'].routing_table = {'H1': (tc1a.links['L0'], 3),
                                          'H2': (tc1a.links['L1'], 3)}
        tc1a.nodes['R2'].routing_table = {'H1': (tc1a.links['L1'], 3),
                                          'H2': (tc1a.links['L3'], 3)}
        tc1a.nodes['R3'].routing_table = {'H1': (tc1a.links['L2'], 3),
                                          'H2': (tc1a.links['L4'], 3)}
        tc1a.nodes['R4'].routing_table = {'H1': (tc1a.links['L4'], 3),
                                          'H2': (tc1a.links['L5'], 3)}

    EventHandler(tc1a).run(1000000)
    f1stats = tc1a.flows['F1'].stats
    f1stats.analyze()
    tc1a.nodes['H1'].stats.analyze()
    # tc1a.links['L1'].stats.analyze()
    # plt.show()

    plt.figure()
    link1flowrate = tc1a.links['L1'].stats.bytesflowed
    link2flowrate = tc1a.links['L2'].stats.bytesflowed

    stats.plotrate(link1flowrate, 50, label="L1")
    stats.plotrate(link2flowrate, 50, label="L2")
    plt.title("Byte flow rate in L1 and L2")
    plt.ylabel("Flow Rate (Bytes/ms)")
    stats.zeroxaxis()

    plt.figure()
    link1buffer = tc1a.links['L1'].stats.bufferoccupancy
    link2buffer = tc1a.links['L2'].stats.bufferoccupancy

    stats.plotrate(link1buffer, 50, label="L1")
    stats.plotrate(link2buffer, 50, label="L2")
    plt.title("Byte flow rate in L1 and L2")
    plt.ylabel("Buffer Occupancy (Bytes)")
    stats.zeroxaxis()

    plt.show()
