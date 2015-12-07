"""
icfire.stats
~~~~~~~~~~~~
Stats encapsulate the statistics and data of each node

"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
import time as timer

class Stats(object):

    """Base class for statistical objects"""

    def __init__(self, parent_id):
        self.parent_id = parent_id
        pass

    def analyze(self):
        """ This script does a full analysis over the objects in the Stats """
        raise NotImplementedError(
            'Handling of analysis not implemented')

DELAY = .5
class HostStats(Stats):

    """Statistics of a node

    This class should model the per-host send/recieve rate
    """

    def __init__(self, host_id, realTimePlot=False, subPlot=None, figure=None, interval=40):
        super(HostStats, self).__init__(host_id)
        self.bytessent = dict()
        self.bytesreceived = dict()
        self.realTimePlot = realTimePlot
        if self.realTimePlot:
            plt.ion()
            self.curTime = [timer.time()] * 3
            if not figure:
                self.fig = plt.figure()
            if not subPlot:
                self.ax = self.fig.add_subplot(111)
            else:
                self.ax = self.fig.add_subplot(subPlot)
            self.l1 = self.ax.plot([],[],label='sent')[0]
            self.l2 = self.ax.plot([],[],label='received')[0]
            self.xMax = 0
            self.yMax = 0
            self.yMin = 0
            self.interval = interval
            plt.legend()
            self.ax.set_title("Bytes send and recieve rates from host " +
                  str(self.parent_id))
            self.ax.set_ylabel("Bytes/ms")
            self.ax.set_xlabel("Time (ms)")

    def addBytesSent(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytessent[timestamp] += bytes
        else:
            self.bytessent[timestamp] = bytes

        if self.realTimePlot:
            if timer.time() > self.curTime[0] + DELAY:
                self.curTime[0] = timer.time()
                time, rate = calcRate(self.bytessent, self.interval)
                
                if len(time) > 0:
                    self.xMax = updateMax(self.xMax, max(time), 1.5)
                    self.yMax = updateMax(self.yMax, max(rate), 1.2)
                    self.yMin = updateMin(self.yMin, min(rate), 1.2)
            
                    self.ax.axis([0, self.xMax, self.yMin, self.yMax])
                    self.l1.set_data(time, rate)
                
                if timer.time() > self.curTime[-1] + DELAY:
                    self.curTime[-1] = timer.time()
                    self.fig.canvas.draw()

    def addBytesRecieved(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytesreceived[timestamp] += bytes
        else:
            self.bytesreceived[timestamp] = bytes
        if self.realTimePlot:
            if timer.time() > self.curTime[1] + DELAY:
                self.curTime[1] = timer.time()
                time, rate = calcRate(self.bytesreceived, self.interval)

                if len(time) > 0:
                    self.xMax = updateMax(self.xMax, max(time), 1.5)
                    self.yMax = updateMax(self.yMax, max(rate), 1.2)
                    self.yMin = updateMin(self.yMin, min(rate), 1.2)

                    self.ax.axis([0, self.xMax, self.yMin, self.yMax])
                    self.l2.set_data(time, rate)

                if timer.time() > self.curTime[-1] + DELAY:
                    self.curTime[-1] = timer.time()
                    self.fig.canvas.draw()

    def analyze(self, interval=40):
        """ This script does a full analysis over the stats stored in a host
        """
        plt.figure()
        plotrate(self.bytessent, interval, label="sent")
        plotrate(self.bytesreceived, interval, label="received")
        plt.title("Bytes send and recieve rates from host " +
                  str(self.parent_id))
        plt.ylabel("Bytes/ms")
        plt.legend()


class FlowStats(Stats):

    """Statistics of a flow

    This class should model
    1. the per-flow send/receive rate
    2. packet round-trip delay
    """

    def __init__(self, flow_id, realTimePlot=False, figure=None, interval=40):
        super(FlowStats, self).__init__(flow_id)
        self.bytessent = dict()
        self.bytesreceived = dict()
        self.rttdelay = dict()
        self.windowsize = dict()
        
        self.realTimePlot = realTimePlot
        if self.realTimePlot:
            plt.ion()
            self.curTime = [timer.time()] * 5
            if not figure:
                self.fig = plt.figure()
            self.ax = [self.fig.add_subplot(4,1,i) for i in range(4)]
            self.l = []
            self.l.append(self.ax[0].plot([],[], label='bytes sent')[0])
            self.l.append(self.ax[0].plot([],[], label='bytes received')[0])
            self.ax[0].set_title('Cumulative Bytes sent and received in flow ' + 
                             str(self.parent_id))

            self.ax[0].set_ylabel("Bytes")
            self.ax[0].set_xlabel('Time (ms)')

            self.l.append(self.ax[1].plot([],[], label='sent')[0])
            self.l.append(self.ax[1].plot([],[], label='bytes received')[0])
            self.ax[1].set_title('Send and receive data rates in flow ' + 
                             str(self.parent_id))
            self.ax[1].set_ylabel('Bytes/ms')


            self.l.append(self.ax[2].plot([],[])[0])
            self.ax[2].set_title('Rount-Trip delay in flow ' + 
                             str(self.parent_id))
            self.ax[2].set_ylabel('Round-Trip delay (ms)')

            self.l.append(self.ax[3].plot([],[])[0])
            self.ax[3].set_title('Window size of flow ' + str(self.parent_id))
            self.ax[3].set_ylabel('Window size')

            [self.ax[i].legend() for i in range(len(self.ax))]
            self.xMax = [0] * len(self.ax)
            self.yMax = [0] * len(self.ax)
            self.yMin = [0] * len(self.ax)
            self.interval = interval

            self.fig.subplots_adjust(hspace=.5)




    def addRTT(self, timestamp, rttd):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        self.rttdelay[timestamp] = rttd
        if self.realTimePlot:
            if timer.time() > self.curTime[0] + DELAY:
                self.curTime[0] = timer.time()
                time, rate = calcSmooth(self.rttdelay, self.interval)

                if len(time) > 0:
                    self.xMax[2] = updateMax(self.xMax[2], max(time), 1.5)
                    self.yMax[2] = updateMax(self.yMax[2], max(rate), 1.2)
                    self.yMin[2] = updateMin(self.yMin[2], min(rate), 1.2)

                    self.ax[2].axis([0, self.xMax[2], self.yMin[2], self.yMax[2]])
                    self.l[4].set_data(time, rate)

                if timer.time() > self.curTime[-1] + DELAY:
                    self.curTime[-1] = timer.time()
                    self.fig.canvas.draw()

    def addBytesSent(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """
        if timestamp in self.bytessent:
            self.bytessent[timestamp] += bytes
        else:
            self.bytessent[timestamp] = bytes

        if self.realTimePlot:
            if timer.time() > self.curTime[1] + DELAY:
                self.curTime[1] = timer.time()
                time, cumSum = calcCumsum(self.bytessent)
                time2, rate = calcRate(self.bytessent, self.interval)

                if len(time) > 0:
                    self.xMax[0] = updateMax(self.xMax[0], max(time), 1.5)
                    self.yMax[0] = updateMax(self.yMax[0], max(cumSum), 1.2)
                    self.yMin[0] = updateMin(self.yMin[0], min(cumSum), 1.2)
                    self.ax[0].axis([0, self.xMax[0], self.yMin[0], self.yMax[0]])
                    self.l[0].set_data(time, cumSum)

                if len(time2) > 0:
                    self.xMax[1] = updateMax(self.xMax[1], max(time2), 1.5)
                    self.yMax[1] = updateMax(self.yMax[1], max(rate), 1.2)
                    self.yMin[1] = updateMin(self.yMin[1], min(rate), 1.2)
                    self.ax[0].axis([0, self.xMax[0], self.yMin[0],self.yMax[0]])
                    self.l[2].set_data(time2, rate)

                if timer.time() > self.curTime[-1] + DELAY:
                    self.curTime[-1] = timer.time()
                    self.fig.canvas.draw()

    def addBytesReceived(self, timestamp, bytes):
        """ Function called to aggregate data into the stats

        :param timestamp: time this occurred
        :param bytes: number of bytes
        """


        if timestamp in self.bytesreceived:
            self.bytesreceived[timestamp] += bytes

        else:
            self.bytesreceived[timestamp] = bytes

        if self.realTimePlot:
            if timer.time() > self.curTime[2] + DELAY:
                self.curTime[2] = timer.time()
                time, cumSum = calcCumsum(self.bytesreceived)
                time2, rate = calcRate(self.bytesreceived, self.interval)

                if len(time) > 0:
                    self.xMax[0] = updateMax(self.xMax[0], max(time), 1.5)
                    self.yMax[0] = updateMax(self.yMax[0], max(cumSum), 1.2)
                    self.yMin[0] = updateMin(self.yMin[0], min(cumSum), 1.2)
                    self.ax[0].axis([0, self.xMax[0], self.yMin[0], self.yMax[0]])
                    self.l[1].set_data(time, cumSum)

                if len(time2) > 0:
                    self.xMax[1] = updateMax(self.xMax[1], max(time2), 1.5)
                    self.yMax[1] = updateMax(self.yMax[1], max(rate), 1.2)
                    self.yMin[1] = updateMin(self.yMin[1], min(rate), 1.2)
                    self.ax[1].axis([0, self.xMax[1], self.yMin[1],self.yMax[1]])
                    self.l[3].set_data(time2, rate)

                if timer.time() > self.curTime[-1] + DELAY:
                    self.curTime[-1] = timer.time()
                    self.fig.canvas.draw()

    def updateCurrentWindowSize(self, timestamp, cwnd):
        """ Function called to aggregate window size into stats

        :param timestamp: time this occurred
        :param cwnd: current window size
        """
        self.windowsize[timestamp] = cwnd
        if self.realTimePlot:
            if timer.time() > self.curTime[3] + DELAY:
                self.curTime[3] = timer.time()
                time, cwnd = calcSmooth(self.windowsize, self.interval)
                if len(time) > 0:
                    self.xMax[3] = updateMax(self.xMax[3], max(time), 1.5)
                    self.yMax[3] = updateMax(self.yMax[3], max(cwnd), 1.2)
                    self.yMin[3] = updateMin(self.yMin[3], min(cwnd), 1.2)
                    self.ax[3].axis([0, self.xMax[3], self.yMin[3], self.yMax[3]])
                    self.l[5].set_data(time, cwnd)

                    if timer.time() > self.curTime[-1] + DELAY:
                        self.curTime[-1] = timer.time()
                        self.fig.canvas.draw()

    def analyze(self, interval=40, sameFigure=True):
        """ This script does a full analysis over the stats stored in a flow
            and plots graphs relevant the data.

            Use this function as an example file to generate custom graphs,
            such as aggregating data from various links
        """
        plt.figure()
        if sameFigure:
            rows = 3
            if self.windowsize:
                rows += 1
            plt.subplot(rows, 1, 1)

        plotcumsum(self.bytessent, not sameFigure, label="bytes sent")
        plotcumsum(self.bytesreceived, not sameFigure, label="bytes received")
        plt.title("Cumulative Bytes sent and recieved in flow " +
                  str(self.parent_id))
        plt.ylabel("Bytes")
        plt.legend()

        if sameFigure:
            plt.subplot(rows, 1, 2)

        else:
            plt.figure()
        plotrate(self.bytessent, interval, not sameFigure, label="sent")
        plotrate(self.bytesreceived, interval, not sameFigure, label="breceived")
        plt.title("Send and receive data rates in flow " +
                  str(self.parent_id))
        plt.ylabel("Bytes/ms")
        plt.legend()

        isBottom = True
        if sameFigure:
            plt.subplot(rows, 1, 3)
            if self.windowsize:
                isBottom = False
        else:
            plt.figure()
        plotsmooth(self.rttdelay, interval, isBottom)
        plt.ylabel("Round-trip delay (ms)")
        plt.title("Round-Trip delay in flow " +
                  str(self.parent_id))

        # don't plot for flows without a windowsize
        if self.windowsize:
            if sameFigure:
                plt.subplot(rows, 1, 4)
                plt.xlabel('Time (ms)')
            else:
                plt.figure()
            plotsmooth(self.windowsize, interval)
            plt.title("Window size of flow " + str(self.parent_id))
            plt.ylabel("Window size")
        plt.subplots_adjust(hspace=0.5)

    def plot(self):
        """ Plots the raw data as a scatterplot """
        plt.figure()
        plotraw(self.bytessent)
        plt.figure()
        plotraw(self.bytesreceived)
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

    def __init__(self, link_id, realTimePlot=False, figure=None, interval=40):
        super(LinkStats, self).__init__(link_id)
        self.bufferoccupancy = dict()
        self.lostpackets = dict()
        self.bytesflowed = dict()

        self.realTimePlot = realTimePlot
        if self.realTimePlot:
            plt.ion()
            self.curTime = [timer.time()] * 4
            if not figure:
                self.fig = plt.figure()
            else:
                self.fig = figure
            self.ax = [self.fig.add_subplot(4,1,i) for i in range(4)]
            self.l = [self.ax[i].plot([],[])[0] for i in range(4)]

            self.ax[0].set_title('Byte flow rate through link ' +
                                 str(self.parent_id))
            self.ax[0].set_ylabel('Flow Rate (Byte/ms)')
            self.ax[0].set_xlabel('Time (ms)')

            self.ax[1].set_title('Cummulative byte flow through link ' + 
                                 str(self.parent_id))
            self.ax[1].set_ylabel('Bytes')

            self.ax[2].set_title('Packets lost in link ' + 
                                 str(self.parent_id))
            self.ax[2].set_ylabel('Packets')

            self.ax[3].set_title('Buffer occupancy in link ' + 
                                 str(self.parent_id))
            self.ax[3].set_ylabel('Occupancy (kb)')

            self.xMax = [0] * len(self.ax)
            self.yMax = [0] * len(self.ax)
            self.yMin = [0] * len(self.ax)
            self.interval = interval
            
            self.fig.subplots_adjust(hspace=.5)

            

            

    def addLostPackets(self, timestamp, nlost):
        if timestamp in self.lostpackets:
            self.lostpackets[timestamp] += nlost
        else:
            self.lostpackets[timestamp] = nlost

        if self.realTimePlot:
            if timer.time() > self.curTime[0] + DELAY:
                self.curTime[0] = timer.time()

                time, packets = calcIntervalsum(self.lostpackets, self.interval)
                if len(time) > 0:
                    
                    self.xMax[2] = updateMax(self.xMax[2], max(time), 1.5)
                    self.yMax[2] = updateMax(self.yMax[2], max(packets), 1.2)
                    self.yMin[2] = updateMin(self.yMin[2], min(packets), 1.2)
                    self.ax[2].axis([0, self.xMax[2], self.yMin[2], self.yMax[2\
]])
                    self.l[2].set_data(time, packets)
                    if timer.time() > self.curTime[-1] + DELAY:
                        self.curTime[-1] = timer.time()
                        self.fig.canvas.draw()

    def addBytesFlowed(self, timestamp, bytes):
        if timestamp in self.bytesflowed:
            self.bytesflowed[timestamp] += bytes
        else:
            self.bytesflowed[timestamp] = bytes

        if self.realTimePlot:
            if timer.time() > self.curTime[1] + DELAY:
                self.curTime[1] = timer.time()

                time, rate = calcRate(self.bytesflowed, self.interval)
                time2, cumSum = calcCumsum(self.bytesflowed)

                if len(time) > 0:
                    self.xMax[0] = updateMax(self.xMax[0], max(time), 1.5)
                    self.yMax[0] = updateMax(self.yMax[0], max(rate), 1.2)
                    self.yMin[0] = updateMin(self.yMin[0], min(rate), 1.2)
                    self.ax[0].axis([0, self.xMax[0], self.yMin[0], self.yMax[0\
]])
                    self.l[0].set_data(time, rate)
                if len(time2) > 0:
                    self.xMax[1] = updateMax(self.xMax[1], max(time2), 1.5)
                    self.yMax[1] = updateMax(self.yMax[1], max(cumSum), 1.2)
                    self.yMin[1] = updateMin(self.yMin[1], min(cumSum), 1.2)
                    self.ax[1].axis([0, self.xMax[1], self.yMin[1], self.yMax[1\
]])
                    self.l[1].set_data(time2, cumSum)

                if timer.time() > self.curTime[-1] + DELAY:
                    self.curTime[-1] = timer.time()
                    self.fig.canvas.draw()

    def updateBufferOccupancy(self, timestamp, buffersize):
        self.bufferoccupancy[timestamp] = buffersize

        if self.realTimePlot:
            if timer.time() > self.curTime[2] + DELAY:
                self.curTime[2] = timer.time()

                time, occupancy = calcRate(self.bufferoccupancy, self.interval)

                if len(time) > 0:
                    self.xMax[3] = updateMax(self.xMax[3], max(time), 1.5)
                    self.yMax[3] = updateMax(self.yMax[3], max(occupancy), 1.2)
                    self.yMin[3] = updateMin(self.yMin[3], min(occupancy), 1.2)
                    self.ax[3].axis([0, self.xMax[3], self.yMin[3], self.yMax[3\
]])
                    self.l[3].set_data(time, occupancy)
                    if timer.time() > self.curTime[-1] + DELAY:
                        self.curTime[-1] = timer.time()
                        self.fig.canvas.draw()

    def analyze(self, interval=40, sameFigure=True):
        plt.figure()
        if sameFigure:
            plt.subplot(4,1,1)
        plotrate(self.bytesflowed, interval, not sameFigure)
        plt.title("Byte flow rate through link " +
                  str(self.parent_id))
        plt.ylabel("Flow Rate (Byte/ms)")

        # Plots Cumulative
        
        if sameFigure:
            plt.subplot(4,1,2)
        else:
            plt.figure()
        
        plotcumsum(self.bytesflowed, not sameFigure)
        plt.title("Cummulative byte flow through link " +
                  str(self.parent_id))
        plt.ylabel("Bytes")

        if sameFigure:
            plt.subplot(4,1,3)
        else:
            plt.figure()
        plotintervalsum(self.lostpackets, interval, not sameFigure)
        plt.title("Packets lost in link " +
                  str(self.parent_id))
        plt.ylabel("Packets")

        if sameFigure:
            plt.subplot(4,1,4)
        else:
            plt.figure()
        plotrate(self.bufferoccupancy, interval)
        plt.title("Buffer occupancy in link " +
                  str(self.parent_id))
        plt.ylabel("Occupancy (kb)")

""" Helper Functions """

def calcRate(datadict, resolution):
    """ Calculates the rate of data value averaged over a time interval

    Creates a dicrete time interval and averages all values within interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in milliseconds to aggregate over
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
    return (times, rates)

def calcSmooth(datadict, resolution):
    """ Calculates the values of a data point averaged over the interval

    Creates dicrete timeintervals and averages all values within

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in milliseconds to aggregate over
    :return time, rates: time and rates lists for plotting
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

    return (times, rates)

def calcIntervalsum(datadict, resolution):
    """ Calculates the sum of data value aggregated over a time interval

    Creates discrete time interval sums of all values

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in milliseconds to aggregate over
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

    return (time, resolution)

def calcCumsum(datadict):
    """ Calculates the cumulative sum 

    :param datadict: dictionary of time-value pairs
    """
    sortedtimes = sorted(datadict.keys())
    sorteddata = [datadict[key] for key in sortedtimes]
    assert(len(sortedtimes) == len(sorteddata))
    cumsum = np.cumsum(sorteddata)

    return (sortedtimes, cumsum)

def plotrate(datadict, resolution, xlabel=True, **kwargs):
    """ Plots the rate of data value averaged over a time interval

    This works by creating discrete time interval and averaging all values
    within said interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in millisecond to aggregate over
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """

    times, rates = calcRate(datadict, resolution)

    plt.plot(times, rates, **kwargs)
    plt.autoscale(True)
    if xlabel:
        plt.xlabel("Time (ms)")
    zeroxaxis()


def plotsmooth(datadict, resolution, xlabel=True, **kwargs):
    """ Plots the value of a data point averaged over the interval

    This works by creating discrete time interval and averaging all values
    within said interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in millisecond to aggregate over
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    times, rates = calcSmooth(datadict, resolution)

    plt.step(times, rates, **kwargs)
    plt.autoscale(True)
    if xlabel:
        plt.xlabel("Time (ms)")
    zeroxaxis()


def plotintervalsum(datadict, resolution, xlabel=True, **kwargs):
    """ Plots the sum of data value aggregated over a time interval

    This works by creating discrete time interval and summing all values
    within said interval

    :param datadict: dictionary of time-value pairs
    :param resolution: interval in millisecond to aggregate over
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    times, rates = calcIntervalsum(datadict, resolution)

    plt.plot(times, rates, **kwargs)
    plt.autoscale(True)
    if xlabel:
        plt.xlabel("Time (ms)")
    zeroxaxis()


def plotcumsum(datadict, xlabel=True, **kwargs):
    """ Plots a cumulative sum

    :param datadict: dictionary of time-value pairs
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """

    sortedtimes, cumsum = calcCumsum(datadict)

    plt.plot(sortedtimes, cumsum, **kwargs)
    plt.autoscale(True)
    if xlabel:
        plt.xlabel("Time (ms)")
    zeroxaxis()


def plotraw(datadict, xlabel=True, **kwargs):
    """ Plots the raw data

    :param datadict: dictionary of time-value pairs
    :param kwargs: dictionary, or keyword arguments to be passed to pyplot
    """
    plt.scatter(datadict.keys(), datadict.values())
    if xlabel:
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

def updateMax(curMax, newMax, ratio=1.2, threshold=.9):
    """ Updates curMax value with new max by ratio if needed

    :param curMax: current max
    :param newMax: new max to check if overflow
    :param ratio: amount to increase curMax if overflow
    :param threshold: threshold at which newMax is considered overflowing
    """
    if newMax > curMax * .9:
        curMax = newMax * ratio
    return curMax

def updateMin(curMin, newMin, ratio=1.2, threshold=.9):
    """ Updates curMin value with new min by ratio if needed

    :param curMin: current min
    :param newMin: new min to check if overflow
    :param ratio: amount to decrease curMin if overflow
    :param threshold: threshold at which newMin is considered overflowing
    """
    if newMin < curMin * threshold:
        if newMin < 0:
            curMin = newMin * ratio
        else:
            curMin = newMin / ratio
    return curMin

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
