from eventhandler import PacketEvent
from eventhandler import Event


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
        raise NotImplementedError('This should be overriden by subclass')

    def _processOtherEvent(self, event):
        raise NotImplementedError('This should be overriden by subclass')
