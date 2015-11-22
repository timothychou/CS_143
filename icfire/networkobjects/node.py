from packet import *
from eventhandler import *
import logger


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
        self.links.append(target)

    def _processPacketEvent(self, packet_event):
        raise NotImplementedError('This should be overriden by subclass')

    def _processOtherEvent(self, event):
        raise NotImplementedError('This should be overriden by subclass')
