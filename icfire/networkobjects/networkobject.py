"""
icfire.networkobject
~~~~~~~~~~~~~~~~~~~~

This module contains the base classes for all objects in the network and
also the node objects. Network objects can process events.

"""

from icfire.event import PacketEvent
from icfire.event import Event


class NetworkObject(object):
    """abstract class for all network objects"""

    def __init__(self):
        raise NotImplementedError(
            'NetworkObject should never be instantiated.')

    def processEvent(self, event):
        """ Processes one event, depending on what the event is.

        This method should be called directly or indirectly by an EventHandler.

        :param event: Event to be processed.
        :return: list of new Events to be enqueued.
        """
        if isinstance(event, PacketEvent):
            return self._processPacketEvent(event)
        elif isinstance(event, Event):
            return self._processOtherEvent(event)
        else:
            raise AssertionError('process event should only be given an event')

    def _processPacketEvent(self, packet_event):
        """ Process a PacketEvent

        :param packet_event: PacketEvent to process
        :return: new Events to enqueue
        """
        raise NotImplementedError('This should be overriden by subclass')

    def _processOtherEvent(self, event):
        """ Process other types of Events

        :param packet_event: Event to process
        :return: new Events to enqueue
        """
        raise NotImplementedError('This should be overriden by subclass')


class Node(NetworkObject):
    """ abstract class that represents a node in a network

    This class represents a node in a network connected by edges"""

    def __init__(self, address, links=None):
        """ Constructor for Node

        :param address: unique address of this Node
        :param links: list of Links (objects) this Node is connected to
        """
        self.address = address
        if not links:
            self.links = []
        else:
            self.links = links

    def addLink(self, target):
        """ Add a link

        :param target: link to add
        """
        self.links.append(target)

    def _processPacketEvent(self, packet_event):
        """ Process a PacketEvent

        :param packet_event: PacketEvent to process
        :return: new Events to enqueue
        """
        raise NotImplementedError('This should be overriden by subclass')

    def _processOtherEvent(self, event):
        """ Process other types of Events

        :param packet_event: Event to process
        :return: new Events to enqueue
        """
        raise NotImplementedError('This should be overriden by subclass')
