class Node(Network_object):
    '''Represents a node in a network

    This class represents a node in a network connected by edges'''

    def __init__(self, links, id):
        '''initialized a Node

        links - list of links
        id - id of Node'''
        self.links = links
        self.id = id

