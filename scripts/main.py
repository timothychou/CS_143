from packet import Packet
from eventhandler import *
from networkobject import *
from network import Network

def main():
    """
    1. Input parser constructs the network.
    2. Event handler is constructed, initial events loaded.
    3. Begin simulation
    """

    # Input parser
    N = Network()
    N.load('testfile.json')
    N.draw()
    # Event handler

    # Begin simulation
    pass


if __name__ == '__main__':
    main()
