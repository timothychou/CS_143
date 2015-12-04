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
    tc2 = Network()
    s1 = tc2.addHost("S1")
    s2 = tc2.addHost("S2")
    s3 = tc2.addHost("S3")
    t1 = tc2.addHost("T1")
    t2 = tc2.addHost("T2")
    t3 = tc2.addHost("T3")
    r1 = tc2.addRouter("R1", 0, static_routing=static_routing)
    r2 = tc2.addRouter("R2", 1000, static_routing=static_routing)
    r3 = tc2.addRouter("R3", 2000, static_routing=static_routing)
    r4 = tc2.addRouter("R4", 3000, static_routing=static_routing)
    tc2.addLink(r1, r2, rate=10, delay=10, buffsize=128, linkid='L1')
    tc2.addLink(r2, r3, rate=10, delay=10, buffsize=128, linkid='L2')
    tc2.addLink(r3, r4, rate=10, delay=10, buffsize=128, linkid='L3')
    tc2.addLink(s1, r1, rate=10, delay=10, buffsize=128, linkid='LS1')
    tc2.addLink(s2, r1, rate=10, delay=10, buffsize=128, linkid='LS2')
    tc2.addLink(s3, r3, rate=10, delay=10, buffsize=128, linkid='LS3')
    tc2.addLink(t1, r4, rate=10, delay=10, buffsize=128, linkid='LT1')
    tc2.addLink(t2, r2, rate=10, delay=10, buffsize=128, linkid='LT2')
    tc2.addLink(t3, r4, rate=10, delay=10, buffsize=128, linkid='LT3')
    # flowType = 'TCPRenoFlow'
    flowType = 'FastTCPFlow'
    tc2.addFlow(s1, t1, bytes=35000000, timestamp=30500,
                flowType=flowType, flowId='F1')
    tc2.addFlow(s2, t2, bytes=15000000, timestamp=40000,
                flowType=flowType, flowId='F2')
    tc2.addFlow(s3, t3, bytes=30000000, timestamp=50000,
                flowType=flowType, flowId='F3')

    return tc2


if __name__ == '__main__':
    filename = 'testcase2.json'
    static_routing = False
    tc2 = buildNetwork(static_routing)
    # tc1.save(filename)
    # tc1.draw()

    # tc1a = Network()
    # tc1a.load(filename)

    tc2a = tc2  # todo loading/saving not 100% functional right now

    # Set routing tables manually
    if static_routing:
        tc2a.nodes['R1'].routing_table = {'S1': (tc2a.links['LS1'], 3),
                                          'S2': (tc2a.links['LS2'], 3),
                                          'S3': (tc2a.links['L1'], 3),
                                          'T1': (tc2a.links['L1'], 3),
                                          'T2': (tc2a.links['L1'], 3),
                                          'T3': (tc2a.links['L1'], 3)}
        tc2a.nodes['R2'].routing_table = {'S1': (tc2a.links['L1'], 3),
                                          'S2': (tc2a.links['L1'], 3),
                                          'S3': (tc2a.links['L2'], 3),
                                          'T1': (tc2a.links['L2'], 3),
                                          'T2': (tc2a.links['LT2'], 3),
                                          'T3': (tc2a.links['L2'], 3)}
        tc2a.nodes['R3'].routing_table = {'S1': (tc2a.links['L2'], 3),
                                          'S2': (tc2a.links['L2'], 3),
                                          'S3': (tc2a.links['LS3'], 3),
                                          'T1': (tc2a.links['L3'], 3),
                                          'T2': (tc2a.links['L2'], 3),
                                          'T3': (tc2a.links['L3'], 3)}
        tc2a.nodes['R4'].routing_table = {'S1': (tc2a.links['L3'], 3),
                                          'S2': (tc2a.links['L3'], 3),
                                          'S3': (tc2a.links['L3'], 3),
                                          'T1': (tc2a.links['LT1'], 3),
                                          'T2': (tc2a.links['L3'], 3),
                                          'T3': (tc2a.links['LT3'], 3)}

    EventHandler(tc2a).run(1000000)

    # tc2a.graph()

    f1stats = tc2a.flows['F1'].stats
    f2stats = tc2a.flows['F2'].stats
    f3stats = tc2a.flows['F3'].stats
    f1stats.analyze()
    f2stats.analyze()
    f3stats.analyze()
    tc2a.nodes['S1'].stats.analyze()
    # tc1a.links['L1'].stats.analyze()
    # plt.show()

    plt.figure()
    link1flowrate = tc2a.links['L1'].stats.bytesflowed
    link2flowrate = tc2a.links['L2'].stats.bytesflowed
    link3flowrate = tc2a.links['L3'].stats.bytesflowed

    stats.plotrate(link1flowrate, 50, label="L1")
    stats.plotrate(link2flowrate, 50, label="L2")
    stats.plotrate(link3flowrate, 50, label="L3")
    plt.title("Byte flow rate in L1, L2, L3")
    plt.ylabel("Flow Rate (Bytes/ms)")
    stats.zeroxaxis()

    plt.figure()
    link1buffer = tc2a.links['L1'].stats.bufferoccupancy
    link2buffer = tc2a.links['L2'].stats.bufferoccupancy
    link3buffer = tc2a.links['L3'].stats.bufferoccupancy

    stats.plotrate(link1buffer, 50, label="L1")
    stats.plotrate(link2buffer, 50, label="L2")
    stats.plotrate(link3buffer, 50, label="L3")
    plt.title("Buffer size in L1, L2, L3")
    plt.ylabel("Buffer Occupancy (Bytes)")
    stats.zeroxaxis()

    plt.show()
