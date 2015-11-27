import matplotlib.pyplot as plt
import math

def plotShit(data, sameFigure=False):
    ''' plots data 
    
    data should be a list of 3-tuples of lists for labels, x and y
    labels are lists of form [title, xlabel, ylabel]
    sameFigure: whether the plots should all be on the same page'''

    if sameFigure:
        plt.figure(1)
        rows = math.ceil(math.sqrt(len(data)))
        cols = math.ceil(len(data) / rows)

        for i in range(len(data)):
            plt.subplot(rows, cols, i)
            __plotOne(data[i])
      
      
      

        plt.show()
    
    else:
        for i in range(len(data)):
            plt.figure(i)
            __plotOne(data[i])

        plt.show()
                         
def __plotOne(datum):
    ''' plots a single plot

    data is a 3-tuple containing labels 
    [title, xlabel, ylabel],
    x data, and
    y data '''
    
    plt.plot(datum[1], datum[2])
    plt.title(datum[0][0])
    plt.xlabel(datum[0][1])
    plt.ylabel(datum[0][2])




    
