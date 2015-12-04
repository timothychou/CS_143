"""
icfire.stats
~~~~~~~~~~~~
Stats encapsulate the statistics and data of each node

"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage


class Stats(object):

    """Base class for statistical objects"""

    def __init__(self, parent_id):
        self.parent_id = parent_id
        pass

    def analyze(self):
        """ This script does a full analysis over the objects in the Stats """
        raise NotImplementedError(
            'Handling of analysis not implemented')


class HostStats(Stats):

    """Statistics of a node

    This class should model the per-host send/recieve rate
    """

    def __init__(self, host_id):
        super(HostStats, self).__init__(host_id)
        self.bytessent = dict()
        self.bytesrecieved = dict()

    def addBytesSent(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytessent[timestamp] += bytes
        else:
            self.bytessent[timestamp] = bytes

    def addBytesRecieved(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytesrecieved[timestamp] += bytes
        else:
            self.bytesrecieved[timestamp] = bytes

    def analyze(self, interval=40):
        """ This script does a full analysis over the stats stored in a host
        """
        plt.figure()
        plotrate(self.bytessent, interval, label="sent")
        plotrate(self.bytesrecieved, interval, label="recieved")
        plt.title("Bytes send and recieve rates from host " +
                  str(self.parent_id))
        plt.ylabel("Bytes/ms")
        plt.legend()


class FlowStats(Stats):

    """Statistics of a flow

    This class should model
    1. the per-flow send/recieve rate
    2. packet round-trip delay
    """

    def __init__(self, flow_id):
        super(FlowStats, self).__init__(flow_id)
        self.bytessent = dict()
        self.bytesrecieved = dict()
        self.rttdelay = dict()
        self.windowsize = dict()

    def addRTT(self, timestamp, rttd):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        self.rttdelay[timestamp] = rttd

    def addBytesSent(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytessent[timestamp] += bytes
        else:
            self.bytessent[timestamp] = bytes

    def addBytesRecieved(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytesrecieved[timestamp] += bytes
        else:
            self.bytesrecieved[timestamp] = bytes

    def updateCurrentWindowSize(self, timestamp, cwnd):
        """ Function called to aggregate window size into stats

        :param timestamp: time this occurred
        :param cwnd: current window size
        """
        self.windowsize[timestamp] = cwnd

    def analyze(self, interval=40):
        """ This script does a full analysis over the stats stored in a flow
            and plots graphs relevant the data.

            Use this function as an example file to generate custom graphs,
            such as aggregating data from various links
        """
        plt.figure()
        plotcumsum(self.bytessent, label="bytes sent")
        plotcumsum(self.bytesrecieved, label="bytes recieved")
        plt.title("Cumulative Bytes sent and recieved in flow " +
                  str(self.parent_id))
        plt.ylabel("Bytes")
        plt.legend()

        plt.figure()
        plotrate(self.bytessent, interval, label="sent")
        plotrate(self.bytesrecieved, interval, label="breceived")
        plt.title("Send and recieve data rates in flow " +
                  str(self.parent_id))
        plt.ylabel("Bytes/ms")
        plt.legend()

        plt.figure()
        plotsmooth(self.rttdelay, interval)
        plt.ylabel("Round-trip delay (ms)")
        plt.title("Round-Trip delay in flow " +
                  str(self.parent_id))

        # don't plot for flows without a windowsize
        if self.windowsize:
            plt.figure()
            plotsmooth(self.windowsize, interval)
            plt.title("Window size of flow " + str(self.parent_id))
            plt.ylabel("Window size")

    def plot(self):
        """ Plots the raw data as a scatterplot """
        plt.figure()
        plotraw(self.bytessent)
        plt.figure()
        plotraw(self.bytesrecieved)
        plt.figure()
        plotraw(self.rttdelay)
        plt.show()


class LinkStats(Stats):

    """Statistics of a node

    This class should model

    1. buffer occupancy
    2. packet loss
    3. flow rate

    """

    def __init__(self, link_id):
        super(LinkStats, self).__init__(link_id)
        self.bufferoccupancy = dict()
        self.lostpackets = dict()
        self.bytesflowed = dict()

    def addLostPackets(self, timestamp, nlost):
        if timestamp in self.lostpackets:
            self.lostpackets[timestamp] += nlost
        else:
            self.lostpackets[timestamp] = nlost

    def addBytesFlowed(self, timestamp, bytes):
        if timestamp in self.bytesflowed:
            self.bytesflowed[timestamp] += bytes
        else:
            self.bytesflowed[timestamp] = bytes

    def updateBufferOccupancy(self, timestamp, buffersize):
        self.bufferoccupancy[timestamp] = buffersize

    def analyze(self, interval=40):
        plt.figure()
        plotrate(self.bytesflowed, interval)
        plt.title("Byte flow rate through link " +
                  str(self.parent_id))
        plt.ylabel("Flow Rate (Byte/ms)")

        # Plots Cumulative
        plt.figure()
        plotcumsum(self.bytesflowed)
        plt.title("Cummulative byte flow through link " +
                  str(self.parent_id))
        plt.ylabel("Bytes")
        plt.figure()
        plotintervalsum(self.lostpackets, interval)
        plt.title("Packets lost in link " +
                  str(self.parent_id))
        plt.ylabel("Packets")

        plt.figure()
        plotrate(self.bufferoccupancy, interval)
        plt.title("Buffer occupancy in link " +
                  str(self.parent_id))
        plt.ylabel("Occupancy (kb)")

""" Helper Functions """


def plotrate(datadict, resolution, **kwargs):
    """ Plots the rate of data value averaged over a time interval

    This works by creating discrete time interval and averaging all values
    within said interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in millisecond to aggregate over
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    sortedtimes = sorted(datadict.keys())
    sorteddata = [datadict[key] for key in sortedtimes]
    assert(len(sortedtimes) == len(sorteddata))
    time = 0
    datatotal = 0
    times = []
    rates = []
    for i in range(len(sortedtimes)):
        while(True):
            if sortedtimes[i] < time:
                datatotal += sorteddata[i]
                break
            else:
                times.append(time)
                rates.append(datatotal / float(resolution))
                datatotal = 0
                time += resolution

    plt.plot(times, rates, **kwargs)
    plt.xlabel("Time (ms)")
    zeroxaxis()


def plotsmooth(datadict, resolution, **kwargs):
    """ Plots the value of a data point averaged over the interval

    This works by creating discrete time interval and averaging all values
    within said interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in millisecond to aggregate over
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    sortedtimes = sorted(datadict.keys())
    sorteddata = [datadict[key] for key in sortedtimes]
    assert(len(sortedtimes) == len(sorteddata))
    time = 0
    datatotal = 0
    times = []
    rates = []
    count = 0
    for i in range(len(sortedtimes)):
        while(True):
            if sortedtimes[i] < time:
                datatotal += sorteddata[i]
                count += 1
                break
            elif count > 0:
                times.append(time)
                rates.append(datatotal / count)
                datatotal = 0
                time += resolution
                count = 0
            else:
                time += resolution

    plt.plot(times, rates, **kwargs)
    plt.xlabel("Time (ms)")
    zeroxaxis()


def plotintervalsum(datadict, resolution, **kwargs):
    """ Plots the sum of data value aggregated over a time interval

    This works by creating discrete time interval and summing all values
    within said interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in millisecond to aggregate over
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    sortedtimes = sorted(datadict.keys())
    sorteddata = [datadict[key] for key in sortedtimes]
    assert(len(sortedtimes) == len(sorteddata))
    time = 0
    datatotal = 0
    times = []
    rates = []
    for i in range(len(sortedtimes)):
        while(True):
            if sortedtimes[i] < time:
                datatotal += sorteddata[i]
                break
            else:
                times.append(time)
                rates.append(datatotal)
                datatotal = 0
                time += resolution

    plt.plot(times, rates, **kwargs)
    plt.xlabel("Time (ms)")
    zeroxaxis()


def plotcumsum(datadict, **kwargs):
    """ Plots a cumulative sum

    :param datadict: dictionary of time-value pairs
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    sortedtimes = sorted(datadict.keys())
    sorteddata = [datadict[key] for key in sortedtimes]
    assert(len(sortedtimes) == len(sorteddata))
    cumsum = np.cumsum(sorteddata)

    plt.plot(sortedtimes, cumsum, **kwargs)
    plt.xlabel("Time (ms)")
    zeroxaxis()


def plotraw(datadict, **kwargs):
    """ Plots the raw data

    :param datadict: dictionary of time-value pairs
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    plt.scatter(datadict.keys(), datadict.values())
    plt.xlabel("Time (ms)")
    zeroxaxis()


def zeroxaxis():
    """ Sets the left hand side of the axis to 0
    """
    cumaxis = list(plt.axis())
    cumaxis[0] = 0
    plt.axis(cumaxis)


def zeroyaxis():
    """ Sets the left hand side of the axis to 0
    """
    cumaxis = list(plt.axis())
    cumaxis[2] = 0
    plt.axis(cumaxis)


""" The following functions are experimental. Do not use """


def movingaverage(datadict, ylabel="Bytes/ms",
                  title="Data rate using moving average"):
    """ NOT REALLY WORKING DO NOT USE """
    x = sorted(datadict.keys())
    dx = np.diff(x)
    y = [datadict[key] for key in x]
    cy = np.convolve(y, np.ones(20) / 20, 'same')[1:] / dx
    plt.plot(x[1:], cy)


def finitedifference(datadict, ylabel="Bytes/ms",
                     title="Data rate using Finite Differences"):
    """ Plots the derivative of data using various Finite Difference
        algorithms
        NOT REALLY WORKING NOW
        :param datadict: A dictionary of time:value entries
        :param ylabel: (optional) what to label the graph
        :param title: (optional) graph title

    """
    x = sorted(datadict.keys())
    # Apply weighted convolutional filter to smooth
    y = np.cumsum([datadict[key] for key in x])

    # Calculate derivatives
    dx = np.diff(x)
    dy = np.diff(y) / dx
    cy = np.convolve(y, [1, -1], 'same')[1:] / dx
    gy = ndimage.gaussian_filter1d(
        y, sigma=1, order=1, mode='wrap')[1:] / dx
    print str(len(x)) + str(len(dy)) + str(len(cy)) + str(len(gy))
    plt.figure()
    plt.plot(x[1:], dy, label="diff")
    plt.plot(x[1:], cy, label="convolution")
    plt.plot(x[1:], gy, label="gaussian")
    plt.xlabel('Time (ms)')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
