"""
icfire.flow
~~~~~~~~~~~

This module contains objects that represent connections between nodes that
send data to each other.

Flows should be owned by the sender host, and flow recipients should be
owned by the destination. Various types of flows are implemented, including
TCP_fast and TCP_Reno. Flows own their own stats objects which holds a record
of various stats in the simulation

Note that SuperSimpleFlow and SuperSimpleFlow2 are deprecated

"""

from icfire import logger
from icfire.packet import AckPacket
from icfire.packet import DataPacket
from icfire.stats import FlowStats
from icfire.event import UpdateWindowEvent


class Flow(object):
    """ Abstract class representing a Flow from one host to another.

    There are many types of Flows governed by different congestion control
    algorithms.
    """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """
        self.source_id = source_id
        self.dest_id = dest_id
        self.bytes = bytes
        self.flowId = flowId
        self.stats = FlowStats(flowId)
        self.done = False

    def receiveAckPacket(self, packet, timestamp):
        """ Alter the flow state based on the ACK packet received.
        Returns a list of new packets to send

        :param packet: The ACK packet received
        :param timestamp: time that this occurs
        :return: A list of new packets
        """
        raise NotImplementedError('This should be overriden by subclass')

    def sendPackets(self, timestamp):
        """ Try to send packets to send based on the current state of the Flow

        :param timestamp: time that this occurs
        :return: A list of new packets
        """
        raise NotImplementedError('This should be overriden by subclass')

    def checkTimeout(self, timestamp):
        """ Check timeout status of the flow.
        :param timestamp: time that this occurs
        :return: A tuple of (list of new packets, new timeout)
        """
        raise NotImplementedError('This should be overriden by subclass')


class SuperSimpleFlow(Flow):
    """ The most basic type of Flow with window size 1.

    For debugging purposes only. """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """
        super(SuperSimpleFlow, self).__init__(source_id, dest_id, bytes, flowId)

        self.lastAck = 0  # last received ACK number
        self.lastSent = -1  # last packet index sent

    def receiveAckPacket(self, packet, timestamp):
        """ A new ACK number means that the next packet can be sent.

        :param packet: The ACK packet received
        :param timestamp: time that this occurs
        :return: A list of new packets
        """
        assert packet.ack
        if packet.index > self.lastAck:
            self.lastAck = packet.index
        return self.sendPackets()

    def sendPackets(self, timestamp):
        """ Send a packet if window size allows it

        :param timestamp: time that this occurs
        :return: A list of new packets
        """
        if self.lastAck > self.lastSent:
            assert self.lastAck == self.lastSent + 1
            self.lastSent += 1
            return [DataPacket(self.source_id, self.dest_id,
                               self.lastSent, self.flowId)]

        return []


class SuperSimpleFlow2(Flow):
    """ Flow with window size N. No resending packets.

    For debugging purposes only. """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """
        super(SuperSimpleFlow2, self).__init__(
            source_id, dest_id, bytes, flowId)

        self.windowsize = 60

        self.acks = [0]
        self.inflight = []

    def receiveAckPacket(self, packet, timestamp):
        """ A new ACK number means that the next packet can be sent.

        :param timestamp: time that this occurs
        :param packet: The AckPacket received
        :return: A list of new packets
        """
        assert isinstance(packet, AckPacket)
        self.acks.append(packet.index)
        if packet.index - 1 in self.inflight:
            self.inflight.remove(packet.index - 1)
        return self.sendPackets(timestamp)

    def sendPackets(self, timestamp):
        """ Send packets if window size allows it

        :param timestamp: time that this occurs
        :return: A list of new packets
        """
        lastack = self.acks[len(self.acks) - 1]

        newpackets = []
        while len(self.inflight) < self.windowsize:
            for i in range(self.windowsize):
                if lastack + i not in self.inflight:
                    newpackets.append(DataPacket(self.source_id, self.dest_id,
                                                 lastack + i, self.flowId))
                    self.inflight.append(lastack + i)
                    break
        return newpackets


class TCPRenoFlow(Flow):
    """ TCP Reno """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new Flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """

        # General flow info
        super(TCPRenoFlow, self).__init__(
            source_id, dest_id, bytes, flowId)

        # Flow status
        self.lastAck = 0  # last received ACK
        self.numLastAck = 1  # number of times last ACK was received
        self.nextSend = 0  # Packet number of next packet to send
        self.finalPacket = self.bytes / 1024  # last packet to send

        # TCP Reno specific (FRT/FR)
        self.ssthresh = 1000  # slow start threshold
        self.cwnd = 1  # current window
        self.canum = 0  # congestion avoidance num, counts number of +1/cwnd
        self.fastrecovery = False  # if in fast recovery mode
        self.maxwnd = -1  # max window size before timeout (FR mode)
        self.expectedack = 0  # expected ACK once exiting FR mode

        # RTT calculator
        self.srtt = 3000  # smoothed RTT, default RTT is 3s
        self.alpha = 0.9  # alpha for adjusting RTT
        self.inflight = {}  # dict of packet index -> (time sent, if repeated)
        self.lastRepSent = 0  # last repeated ACK sent, ignore prev for RTT

        # Timeout
        self.rto = 60000  # timeout time, default 60s
        self.ubound = 60000  # Upper bound 60s
        self.lbound = 1000  # Lower bound 1s
        self.beta = 1.5  # beta for adjusting timeout
        self.active = True  # if packets sent/received, then Flow is active
        self.nextTimeout = 0  # next allowed timeout time (every 2 RTT)
        self.ignoreuntil = 0  # ignore duplicate ACKS for a while after timeout

    def receiveAckPacket(self, packet, timestamp):
        """ A new ACK number means that the next packet can be sent.

        :param packet: The AckPacket received
        :param timestamp: the time this action occurs
        :return: A list of new packets
        """
        assert isinstance(packet, AckPacket)
        self.active = True
        resend = []

        # Duplicate ACK
        if packet.index == self.lastAck and timestamp > self.ignoreuntil:
            self.numLastAck += 1

            # Fast Retransmit/Fast Recovery
            # http://www.isi.edu/nsnam/DIRECTED_RESEARCH/DR_WANIDA/DR/JavisInActionFastRecoveryFrame.html
            if self.numLastAck == 4:
                self.ssthresh = max(self.cwnd / 2, 2)
                resend = [DataPacket(self.source_id, self.dest_id,
                                     self.lastAck, self.flowId)]
                self.cwnd = self.ssthresh + 3
                self.canum = 0

                self.fastrecovery = True
                self.expectedack = self.nextSend
                self.maxwnd = self.cwnd * 2
                self.lastRepSent = max(self.lastRepSent, self.nextSend)

            # Exceeded maximum allowed window size (resent packet was dropped)
            elif self.fastrecovery and self.numLastAck > self.maxwnd:
                # Timed out.
                self._timeout(timestamp)

            # FR mode
            elif self.numLastAck > 4:
                self.cwnd += 1
                self.canum = 0

        # New ACK
        elif packet.index > self.lastAck:
            # Calculate RTT if this packet is determinable (not repeated)
            if packet.index - 1 > self.lastRepSent and \
                    not self.inflight[packet.index - 1][1]:
                rtt = timestamp - self.inflight[packet.index - 1][0]
                self.stats.addRTT(timestamp, rtt)
                self.srtt = self.alpha * self.srtt + (1 - self.alpha) * rtt

            # Remove previous inflight packets
            for i in range(self.lastAck, packet.index):
                self.inflight.pop(i)

            # Update parameters
            self.lastAck = packet.index
            self.nextSend = max(self.nextSend, self.lastAck)
            self.numLastAck = 1

            # Done
            if self.lastAck == self.finalPacket:
                self.done = True

            # Exit fast recovery
            if self.fastrecovery:
                # Check whether expected ACK out of FR. If not, timeout.
                if packet.index >= self.expectedack:
                    self.cwnd = self.ssthresh
                    self.canum = 0
                    self.fastrecovery = False
                else:
                    self.ignoreuntil = timestamp + 1000
                    self._timeout(timestamp)

            # Slow start
            if self.cwnd < self.ssthresh:
                self.cwnd += 1
                self.canum = 0

            # Congestion avoidance
            else:
                self.canum += 1
                if self.canum == self.cwnd:
                    self.cwnd += 1
                    self.canum = 0

        # Log stats
        if not self.done:
            # Log ssthresh as real window size during FR mode
            if self.fastrecovery:
                self.stats.updateCurrentWindowSize(timestamp, self.ssthresh)
            else:
                self.stats.updateCurrentWindowSize(timestamp, self.cwnd)
        return resend + self.sendPackets(timestamp)

    def sendPackets(self, timestamp):
        """ Send packets if window size allows it

        :param timestamp: time that this occurs
        :return: A list of new packets
        """

        newpackets = [DataPacket(self.source_id, self.dest_id, ind, self.flowId)
                      for ind in range(self.nextSend,
                                       min(self.finalPacket, self.lastAck + self.cwnd))]

        # Set sent time for RTT calcs
        totalbytes = 0
        for p in newpackets:
            self.inflight[p.index] = (timestamp, p.index in self.inflight)
            totalbytes += p.size
        self.stats.addBytesSent(timestamp, totalbytes)

        self.nextSend = max(self.nextSend, self.lastAck + self.cwnd)

        if len(newpackets) > 0:
            self.active = True

        return newpackets

    def _timeout(self, timestamp):
        """ Internal function that is called to handle timeouts

        :param timestamp: time that this occurs
        """
        if not self.done and timestamp > self.nextTimeout:
            logger.log('TIMED OUT!')

            self.cwnd = 1
            self.canum = 0
            self.fastrecovery = False

            self.lastRepSent = max(self.lastRepSent, self.nextSend)
            self.nextSend = self.lastAck
            self.nextTimeout = timestamp + 2 * self.srtt

    def checkTimeout(self, timestamp):
        """ Check timeout status of the flow.

        :param timestamp: time that this occurs
        :return: A tuple of (list of new packets, new timeout)
        """

        # Timed out, crash to window size 1.
        if not self.active:
            self._timeout(timestamp)

        self.rto = min(self.ubound, max(self.lbound, self.beta * self.srtt))
        self.active = False

        return self.sendPackets(timestamp), self.rto


class FastTCPFlow(TCPRenoFlow):
    """ Fast TCP """

    def __init__(self, source_id, dest_id, bytes, flowId):
        """ Create a new flow

        :param source_id: address of the flow sender (owner of this Flow)
        :param dest_id: dest address of the other host
        :param bytes: bytes to send (0 for continuous)
        :param flowId: id of the flow
        """

        # General flow info
        super(FastTCPFlow, self).__init__(source_id, dest_id, bytes, flowId)

        # RTT calculator
        self.srtt = 200
        self.brtt = 3000
        self.rtt = 200
        self.first = True
        self.newRTT = False

        # parameters for window control algorithm
        self.gamma = 1
        self.alpha = 20
        self.cwndDouble = self.cwnd

    def receiveAckPacket(self, packet, timestamp):
        """ A new ACK number means that the next packet can be sent.

        :param packet: The AckPacket received
        :param timestamp: the time this action occurs
        :return A list of new packets
        """
        assert isinstance(packet, AckPacket)
        self.active = True
        resend = []
        self.newRTT = True
        # Duplicate ACK
        if packet.index == self.lastAck:
            self.numLastAck += 1

            # Fast Retransmit/Fast Recovery
            if self.numLastAck == 4:
                resend = [DataPacket(self.source_id, self.dest_id,
                                     self.lastAck, self.flowId, timestamp)]

                self.fastrecovery = True
                self.lastRepSent = max(self.lastRepSent, self.nextSend)
            self.rtt = timestamp - packet.timestamp
            self._updateRTT(self.rtt)

        # New ACK
        elif packet.index > self.lastAck:
            if packet.index - 1 > self.lastRepSent and \
                    not self.inflight[packet.index - 1][1]:
                self.rtt = timestamp - packet.timestamp
                self._updateRTT(self.rtt)
                self.stats.addRTT(timestamp, self.srtt)

            for i in range(self.lastAck, packet.index):
                self.inflight.pop(i)

            self.lastAck = packet.index
            self.nextSend = max(self.nextSend, self.lastAck)
            self.numLastAck = 1

            # Done
            if self.lastAck == self.finalPacket:
                self.done = True

            # Exit fast recovery
            if self.fastrecovery:
                self.fastrecovery = False

        return resend + self.sendPackets(timestamp)

    def sendPackets(self, timestamp):
        """ Send packets if window size allows it

        :param timestamp: time that this occurs
        :return:  A list of new packets
        """
        newpackets = super(FastTCPFlow, self).sendPackets(timestamp)

        for p in newpackets:
            p.timestamp = timestamp

        return newpackets

    def processEvent(self, event):
        if isinstance(event, UpdateWindowEvent):
            return self._updateWindowSize(event)
        else:
            raise NotImplementedError(
                'Handling of %s not implemented' % event.__class__)

    def _updateWindowSize(self, event):
        a = .9
        self.rtt = self.srtt
        if self.newRTT:
            self.cwndDouble = (1 - a) * self.cwndDouble + (a) * (1.0 * self.brtt / self.srtt * self.cwnd + self.alpha)
        self.newRTT = False
        self.cwnd = int(self.cwndDouble)
        if not self.done:
            self.stats.updateCurrentWindowSize(event.timestamp, self.cwndDouble)
            return [UpdateWindowEvent(event.timestamp + 2 * self.srtt, self,
                                      logMessage='Updating window size on flow %s' % (self.flowId))]
        return []

    def _updateRTT(self, rtt):
        if self.first:
            self.srtt = rtt
            self.first = False
        else:
            a = min(3.0 / self.cwnd, .25)
            self.srtt = self.srtt * (1 - a) + (a) * rtt

        self.brtt = min(self.brtt, self.srtt)


class FlowRecipient(object):
    """ Class for the Flow recipient to manage the Flow. """

    def __init__(self, flowId, stats):
        """ Constructor

        :param flowId: flow's ID
        :param stats: FlowStats to use
        """
        self.flowId = flowId

        self.received = set()  # List of received packet indices
        self.lastAck = 0  # Last ack index sent (expected next packet index)
        self.stats = stats

    def receiveDataPacket(self, packet, timestamp):
        """ Note the received packet and respond with the appropriate ACK packet

        :param packet: received data packet
        :param timestamp: time that this occurs
        :return: new AckPacket
        """
        self.stats.addBytesReceived(timestamp, packet.size)
        if packet.index >= self.lastAck:
            self.received |= {packet.index}
        while self.lastAck in self.received:
            self.received.remove(self.lastAck)
            self.lastAck += 1

        return AckPacket(packet.dest, packet.source,
                         self.lastAck, packet.flowId, packet.timestamp)
