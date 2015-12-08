import sys
import os

sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler

if __name__ == '__main__':
    filename = 'tc0Fast.json'

    # plotting specs
    flowinterval = 40
    plotflows = ['F1']
    linkinterval = 40
    plotlinks = ['L1']
    hostinterval = 40
    plothosts = ['H1', 'H2']

    # load network
    tc0 = Network()
    tc0.load(filename)

    # run
    EventHandler(tc0).run(2000000)
    tc0.draw()

    # plot
    tc0.plotAll(flowinterval, plotflows, linkinterval, plotlinks,
                hostinterval, plothosts, "Fast for TC0")
