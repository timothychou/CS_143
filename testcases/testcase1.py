import sys
import os

sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler

if __name__ == '__main__':
    filename = 'tc1Fast.json'

    # plotting specs
    flowinterval = 40
    plotflows = ['F1']
    linkinterval = 40
    plotlinks = ['L1', 'L2']
    hostinterval = 40
    plothosts = ['H1', 'H2']

    # load network
    tc1 = Network()
    tc1.load(filename)
    tc1.draw()

    # run
    EventHandler(tc1).run(2000000)

    # plot
    tc1.plotAll(flowinterval, plotflows, linkinterval, plotlinks, hostinterval, plothosts)
