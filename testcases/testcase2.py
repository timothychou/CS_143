import sys
import os

import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler
import icfire.stats as stats


def buildNetwork(static_routing=False, flowType = 'TCPRenoFlow'):
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
    r1 = tc2.addRouter("R1", -40000, static_routing=static_routing)
    r2 = tc2.addRouter("R2", -39000, static_routing=static_routing)
    r3 = tc2.addRouter("R3", -38000, static_routing=static_routing)
    r4 = tc2.addRouter("R4", -37000, static_routing=static_routing)
    tc2.addLink(r1, r2, rate=10, delay=10, buffsize=128, linkid='L1')
    tc2.addLink(r2, r3, rate=10, delay=10, buffsize=128, linkid='L2')
    tc2.addLink(r3, r4, rate=10, delay=10, buffsize=128, linkid='L3')
    tc2.addLink(s1, r1, rate=10, delay=10, buffsize=128, linkid='LS1')
    tc2.addLink(s2, r1, rate=10, delay=10, buffsize=128, linkid='LS2')
    tc2.addLink(s3, r3, rate=10, delay=10, buffsize=128, linkid='LS3')
    tc2.addLink(t1, r4, rate=10, delay=10, buffsize=128, linkid='LT1')
    tc2.addLink(t2, r2, rate=10, delay=10, buffsize=128, linkid='LT2')
    tc2.addLink(t3, r4, rate=10, delay=10, buffsize=128, linkid='LT3')
    tc2.addFlow(s1, t1, bytes=35000000, timestamp=500,
                flowType=flowType, flowId='F1')
    tc2.addFlow(s2, t2, bytes=15000000, timestamp=10000,
                flowType=flowType, flowId='F2')
    tc2.addFlow(s3, t3, bytes=30000000, timestamp=20000,
                flowType=flowType, flowId='F3')

    return tc2


if __name__ == '__main__':
    filename = 'testcase2.json'
    static_routing = False
    flowType = 'FastTCPFlow'
    tc2 = buildNetwork(static_routing, flowType)
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

    EventHandler(tc2a).run(2000000)

    # graph flows
    flowinterval = 100
    f1stats = tc2a.flows['F1'].stats
    f2stats = tc2a.flows['F2'].stats
    f3stats = tc2a.flows['F3'].stats

    # Byte Send Rate of all 3
    plt.figure()
    plt.subplot(411)
    stats.plotrate(f1stats.bytessent, flowinterval, False, label="F1")
    stats.plotrate(f2stats.bytessent, flowinterval, False, label="F2")
    stats.plotrate(f3stats.bytessent, flowinterval, False, label="F3")
    plt.title("Send rates in flows F1, F2, F3")
    plt.ylabel("Bytes/ms")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    # Byte Recieved Rate of all 3
    plt.subplot(412)
    stats.plotrate(f1stats.bytesreceived, flowinterval, False, label="F1")
    stats.plotrate(f2stats.bytesreceived, flowinterval, False, label="F2")
    stats.plotrate(f3stats.bytesreceived, flowinterval, False, label="F3")
    plt.title("Recieve rates in flows F1, F2, F3")
    plt.ylabel("Bytes/ms")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    # RTT of flows
    plt.subplot(413)
    stats.plotsmooth(f1stats.rttdelay, flowinterval, False, label="F1")
    stats.plotsmooth(f2stats.rttdelay, flowinterval, False, label="F2")
    stats.plotsmooth(f3stats.rttdelay, flowinterval, False, label="F3")
    plt.title("Round Trip Time in flows F1, F2, F3")
    plt.ylabel("Time (ms)")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    # Window size (This will break if there is no window size)
    if flowType == 'FastTCPFlow' or flowType == 'TCPRenoFlow':
        plt.subplot(414)
        stats.plotsmooth(f1stats.windowsize, flowinterval, label="F1")
        stats.plotsmooth(f2stats.windowsize, flowinterval, label="F2")
        stats.plotsmooth(f3stats.windowsize, flowinterval, label="F3")
        plt.title("Window sizes in flows F1, F2, F3")
        plt.ylabel("Size")
        stats.zeroxaxis()
        stats.zeroyaxis()
        plt.legend()
        
    plt.subplots_adjust(hspace=.5)

    # Graph Link information
    linkinterval = 100
    plt.figure()
    l1stats = tc2a.links['L1'].stats
    l2stats = tc2a.links['L2'].stats
    l3stats = tc2a.links['L3'].stats

    # link byte flow rate
    plt.subplot(311)
    stats.plotrate(l1stats.bytesflowed, linkinterval, False, label="L1")
    stats.plotrate(l2stats.bytesflowed, linkinterval, False, label="L2")
    stats.plotrate(l3stats.bytesflowed, linkinterval, False, label="L3")
    plt.title("Byte flow rate in L1, L2, L3")
    plt.ylabel("Flow Rate (Bytes/ms)")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    # link buffer occupancy
    plt.subplot(312)
    stats.plotsmooth(l1stats.bufferoccupancy, linkinterval, False, label="L1")
    stats.plotsmooth(l2stats.bufferoccupancy, linkinterval, False, label="L2")
    stats.plotsmooth(l3stats.bufferoccupancy, linkinterval, False, label="L3")
    plt.title("Buffer size in L1, L2, L3")
    plt.ylabel("Buffer Occupancy (Bytes)")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    # bytes lost
    plt.subplot(313)
    stats.plotintervalsum(l1stats.lostpackets, linkinterval, label="L1")
    stats.plotintervalsum(l2stats.lostpackets, linkinterval, label="L2")
    stats.plotintervalsum(l3stats.lostpackets, linkinterval, label="L3")
    plt.title("Packets lost in L1, L2, L3")
    plt.ylabel("Packets")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    plt.subplots_adjust(hspace=.5)

    # SOURCE
    # Plot source send and recieve rates
    plt.figure()
    s1stats = tc2a.nodes['S1'].stats
    s2stats = tc2a.nodes['S2'].stats
    s3stats = tc2a.nodes['S3'].stats

    # Byte send/receive rate of all 3 sources
    sourceinterval = 100
    stats.plotrate(s1stats.bytessent, sourceinterval, label="S1-send")
    stats.plotrate(s2stats.bytessent, sourceinterval, label="S2-send")
    stats.plotrate(s3stats.bytessent, sourceinterval, label="S3-send")
    stats.plotrate(s1stats.bytesreceived, sourceinterval, label="S1-receive")
    stats.plotrate(s2stats.bytesreceived, sourceinterval, label="S2-receive")
    stats.plotrate(s3stats.bytesreceived, sourceinterval, label="S3-receive")
    plt.title("Send/receive rates in source nodes S1, S2, S3")
    plt.ylabel("Bytes/ms")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    # Plot sink send and recieve rates
    t1stats = tc2a.nodes['T1'].stats
    t2stats = tc2a.nodes['T2'].stats
    t3stats = tc2a.nodes['T3'].stats

    plt.subplots_adjust(hspace=.5)

    # Byte send/receive rate of all 3 recipients
    plt.figure()
    stats.plotrate(t1stats.bytessent, sourceinterval, label="T1-send")
    stats.plotrate(t2stats.bytessent, sourceinterval, label="T2-send")
    stats.plotrate(t3stats.bytessent, sourceinterval, label="T3-send")
    stats.plotrate(t1stats.bytesreceived, sourceinterval, label="T1-receive")
    stats.plotrate(t2stats.bytesreceived, sourceinterval, label="T2-receive")
    stats.plotrate(t3stats.bytesreceived, sourceinterval, label="T3-receive")
    plt.title("Send/receive rates in recipient nodes T1, T2, T3")
    plt.ylabel("Bytes/ms")
    stats.zeroxaxis()
    stats.zeroyaxis()
    plt.legend()

    plt.subplots_adjust(hspace=.5)

    plt.show()
