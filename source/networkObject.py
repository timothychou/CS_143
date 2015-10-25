class Network_object(object):
    '''abstract class for all network objects'''

    def processEvent(self, events):
        '''Processes events

        Input: list of events from the event processor
        Output: list of new events to enqueu in event processor'''

        raise NotImplementedError('subclasses should override processEvent')
