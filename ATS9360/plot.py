from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.widgets.RemoteGraphicsView
import pyqtgraph.multiprocess as mp
import matplotlib.pyplot as plt
plt.ion()

class AtsPlot(object):

    def __init__(self):


        self.fig, self.ax = plt.subplots(nrows=1,
                                           ncols=1,
                                           sharex=True)


        self.ax.grid()

        self.curve, = self.ax.plot([], [])






    def update(self, x, y):

        self.curve.set_xdata(x)
        self.curve.set_ydata(y)

        #We update limits
        self.ax.relim()
        self.ax.autoscale_view(True,True,True)

        plt.draw()
