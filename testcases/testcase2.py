import sys
import os

sys.path.append(os.path.dirname(os.getcwd()))

from icfire.network import Network
from icfire.eventhandler import EventHandler

if __name__ == '__main__':
    filename = 'tc2Fast.json'

    # plotting specs
    flowinterval = 40
    plotflows = ['F1', 'F2', 'F3']
    linkinterval = 40
    plotlinks = ['L1', 'L2', 'L3']
    hostinterval = 40
    plothosts = ['S1', 'S2', 'S3', 'T1', 'T2', 'T3']

    # load network
    tc2 = Network()
    tc2.load(filename)
    tc2.draw()

    # run
    EventHandler(tc2).run(2000000)

    # plot
    tc2.plotAll(flowinterval, plotflows, linkinterval, plotlinks, hostinterval, plothosts)
