""" Stats encapsulate the statistics and data of each node """

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class Stats(object):

    """Base class for statistical objects"""

    def __init__(self):
        pass


class HostStats(Stats):

    """Statistics of a node

    This class should model the per-host send/recieve rate
    """

    def __init__(self):
        super(HostStats, self).__init__()
        self.bytessent = dict()
        self.bytesrecieved = dict()


class FlowStats(Stats):

    """Statistics of a flow

    This class should model
    1. the per-flow send/recieve rate
    2. packet round-trip delay
    """

    def __init__(self):
        super(FlowStats, self).__init__()
        self.bytessent = dict()
        self.bytesrecieved = dict()
        self.rttdelay = dict()

    def addRTT(self, timestamp, rttd):
        self.rttdelay[timestamp] = rttd

    def addBytesSent(self, timestamp, bytes):
        if timestamp in self.bytessent:
            self.bytessent[timestamp] += bytes
        else:
            self.bytessent[timestamp] = bytes

    def addBytesRecieved(self, timestamp, bytes):
        if timestamp in self.bytessent:
            self.bytesrecieved[timestamp] += bytes
        else:
            self.bytesrecieved[timestamp] = bytes

    def plot(self):
        plt.figure()
        plt.scatter(self.bytessent.keys(), self.bytessent.values())
        plt.figure()
        plt.scatter(self.bytesrecieved.keys(), self.bytesrecieved.values())
        plt.figure()
        plt.scatter(self.rttdelay.keys(), self.rttdelay.values())
        plt.show()


class LinkStats(Stats):

    """Statistics of a node

    This class should model

    1. buffer occupancy
    2. packet loss
    3. flow rate

    """

    def __init__(self):
        super(LinkStats, self).__init__()
        self.bufferoccupancy = dict()
        self.lostpackets = dict()
        self.flowrate = dict()

    def addLostPackets(self, timestamp, nlost):
        if timestamp in self.lostpackets:
            self.bytesrecieved[timestamp] += nlost
        else:
            self.bytesrecieved[timestamp] = nlost
