from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.widgets.RemoteGraphicsView
import pyqtgraph.multiprocess as mp
import numpy as np
import time
from multiprocessing import Queue

def plot_test(queue_treatment, finish, parameters):

    pg.mkQApp()

        # Create remote process with a plot window
    proc    = mp.QtProcess()
    rpg     = proc._import('pyqtgraph')
    plotwin = rpg.plot()
    curve   = plotwin.plot([], [])

    plotwin.setLabels(left=('Board signal', 'Volt'),
                      bottom=('Time', 'us'))


    y = np.zeros(parameters['acquired_samples'])
    sleep_time = 0.5 # In second
    while True:
        start_time = time.time()
        temp = np.array([])

        while True:
            try :
                temp = np.concatenate((queue_treatment.get(block=False)))
            except Queue.Empty:
                break

        # counter = 0
        # while not queue_treatment.empty() and len(temp) == 0:
        #     temp = np.concatenate((temp, queue_treatment.get()))
        #     print counter
        #     counter += 1

        temp = np.reshape(temp, (len(temp)/parameters['acquired_samples'],
                                 parameters['acquired_samples']))
        print temp.shape
        y += np.mean(temp, axis=0)
        x = np.arange(len(y))/parameters['samplerate']
        curve.setData(x=x, y=y, _callSync='off')

        elasped_time = time.time() - start_time

        if elasped_time < sleep_time :
            time.sleep(sleep_time - elasped_time)
