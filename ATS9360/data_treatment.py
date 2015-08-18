from __future__ import division
import numpy as np
import atsapi as ats

import matplotlib.pyplot as plt


def data_average_cha_chb(data_cha, data_chb, current_iteration):
    """
        Perform the averaging of acquired data following the number of
        iteration at which the averaging is done.
        The return averaging is then always the arithmetic averaging of
        the measured data.

        current_iteration must start from 0.
    """
    # For the first iteration, the averaging is just an addition
    if current_iteration == 0.:
        data_cha += data_cha
        data_chb += data_chb
    # For all other iterations, we perform the averaging
    else:
        data_cha = data_cha*current_iteration/(current_iteration + 1.)\
                   + data_cha/(current_iteration + 1.)
        data_chb = data_chb*current_iteration/(current_iteration + 1.)\
                   + data_chb/(current_iteration + 1.)

    return data_cha, data_chb



def data_cha_chb(data_volt, parameters):
    """
        From the data returned by the board and transormed in data_volt,
        the method splits data coming from the two channels and make the
        averaging on one buffer.
    """

    # We split the two channels
    data_cha = data_volt[0::2]
    data_chb = data_volt[1::2]


    records_per_buffer = parameters['records_per_buffer']
    acquired_samples   = parameters['acquired_samples']
    # We reshape them in 2D-array to enhance the averaging
    data_cha = np.reshape(data_cha, (records_per_buffer,
                                     acquired_samples))
    data_chb = np.reshape(data_chb, (records_per_buffer,
                                     acquired_samples))

    # We average along the axis of the repetitions
    data_cha = np.mean(data_cha, axis = 0)
    data_chb = np.mean(data_chb, axis = 0)

    return data_cha, data_chb



def data_in_volt(data):
    """
        Get raw data coming from the board and transform them in V.
    """

    # Parameters of the board (are fixed).
    bitshift         = 4  # Sould be int
    bits_per_sample  = 12 # Sould be int
    inputRange_volts = 400e-3

    # Right-shift 16-bit sample value by 4 to get 12-bit sample code
    sampleCode = data >> bitshift

    # AlazarTech digitizers are calibrated as follows
    codeZero  = (1 << (bits_per_sample - 1)) - 0.5
    codeRange = (1 << (bits_per_sample - 1)) - 0.5

    # Simple proportionality
    sampleVolts = inputRange_volts*(sampleCode - codeZero) / codeRange

    return sampleVolts


def hum(queue_data, treat_data, parameters, finish, iteration):

    for i in range(int(parameters['buffers_per_acquisition']\
                       /parameters['nb_process_data_treatment'])):

        # We get data from the queue
        data = queue_data.get()

        # We transform data in volt.
        # data_volt = data
        data_volt          = data_in_volt(data)
        # We obtain the current averaging of channel A and B data
        data_cha, data_chb = data_cha_chb(data_volt, parameters)

        # We "save" the total averaging in the data attributes.
        # data_cha, data_chb = data_average_cha_chb(data_cha,
        #                                           data_chb,
        #                                           iteration)
        fig, ax = plt.subplots(1, 1)
        ax.plot(data[::2][:10240])
        plt.show()

        treat_data = np.frombuffer(treat_data)
        treat_data += data_cha
        # if i ==2:
        #     print treat_data
        # queue_treat_data.put(treat_data + data_cha)

        # if i == int(parameters['buffers_per_acquisition']\
        #                    /parameters['nb_process_data_treatment'])-1:
        #     treat_data.put(data)

    # We inform the main loop that the process of data treatment is finished
    finish[iteration] = True
