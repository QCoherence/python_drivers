# This Python file uses the following encoding: utf-8
# ATS9360_NPT.py driver for The aquisition board Alzar ATS9360
# Etienne Dumur <etienne.dumur@neel.cnrs.fr> 2015
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import numpy as np
import time
import multiprocessing as mp
import scipy.signal as scisig

class DataTreatment(object):
    """
        Canvas for data treatment class.
        Should only be used as parent class
    """


    @staticmethod
    def data_in_volt(data):
        """
            Get raw data coming from the board and transform them in V.
        """

        # Parameters of the board (are fixed).
        # bitshift         = 4  # Sould be int
        # bits_per_sample  = 12 # Sould be int
        # inputRange_volts = 400e-3 # Fixed for the ats9360

        # Right-shift 16-bit sample value by 4 to get 12-bit sample code
        data = data >> 4

        # AlazarTech digitizers are calibrated as follows
        # codeZero  = (1 << (bits_per_sample - 1)) - 0.5
        # codeRange = (1 << (bits_per_sample - 1)) - 0.5
        # Following this a proportionality of 2047.5 is applied
        # The calcul is inputRange_volts*(data - codeZero) / codeRange

        return 0.4*(data - 2047.5)/2047.5



    @staticmethod
    def data_2D(data, parameters):
        """
            From the data returned by the board,
            the method makes a 2D array of them knowing the board's parameters.
        """

        # We reshape them in 2D-array to enhance the averaging
        # print type(parameters['records_per_buffer'])
        # print type(parameters['samplesPerRecord'])
        # print parameters['records_per_buffer']
        # print parameters['samplesPerRecord']


        return np.reshape(data, (parameters['records_per_buffer'],parameters['samplesPerRecord']))



    def mean_averaging(self, current_average, new_data):
        # print self.treated_sequance

        return (self.treated_sequance*current_average + new_data)\
              /(self.treated_sequance + 1.)



    @staticmethod
    def bitwise(data):
        """
            Right-shift 16-bit sample value by 4 to get 12-bit sample code
        """
        return data >> 4



    def std_averaging(self, current_std, new_std):

        return np.sqrt((self.treated_sequance*current_std**2. + new_std**2.)\
                      /(self.treated_sequance + 1.))



    def many_sequences_per_buffer(self, data, queue_treatment, parameters):
        """
            Organise data when the number of acquired sequences are smaller
            than the number of records per buffer.
        """

        # For the first buffer, we initialize the data stored attribute
        # witht the correct shape
        if self.treated_buffer == 0:
            self.data_stored = np.array([]).reshape(parameters['nb_sequence'], 0)
        # If there are data stored from previous buffer
        elif self.data_stored.shape[0] != parameters['nb_sequence']:

            # Data used correspond to the data saved previously and
            # data coming from the new buffer. We build an array combining
            # these two sources of data.
            self.process(np.vstack((self.data_stored,\
                                   data[:parameters['nb_sequence'] - self.data_stored.shape[0]])),\
                        queue_treatment, parameters)

        # We iterate to empty the buffer by sending data in package
        # corresponding to a whole sequence.
        i = 0
        while (i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0] <= parameters['records_per_buffer']:

            self.process(data[(i + 1)*parameters['nb_sequence'] - self.data_stored.shape[0]\
                            :(i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0]],\
                        queue_treatment, parameters)
            i += 1

        # If there is data left but not enough to send a package, we store
        # them for the next buffer.
        i -= 1
        if (i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0] != data.shape[0]:

            self.data_stored = data[(i + 2)*parameters['nb_sequence'] - self.data_stored.shape[0]:]
        # If not, we reinitialize the data stored attribute with an empty
        # array
        else:
            self.data_stored = np.array([]).reshape(parameters['nb_sequence'], 0)



    def less_sequence_per_buffer(self, data, queue_treatment, parameters):
        """
            Organise data when the number of acquired sequences are greater
            than the number of records per buffer.
        """

        # For the first buffer, we initialize the data stored attribute
        if self.treated_buffer == 0:
            self.data_stored = data
        else:

            # If the new data are not enough to reach the number of sequence
            # we store the whole measured buffer
            if self.data_stored.shape[0] + data.shape[0] < parameters['nb_sequence']:

                self.data_stored  = np.vstack((self.data_stored, data))
            # Otherwise, only a part of the buffer is use to store.
            # The other part is stored for the next buffer
            else:
                self.process(np.vstack((self.data_stored,\
                                        data[:parameters['nb_sequence']\
                                        - self.data_stored.shape[0]])),\
                            queue_treatment, parameters)

                self.data_stored = data[parameters['nb_sequence'] - self.data_stored.shape[0]:]
                self.treated_sequance += 1



    def treat_data(self, queue_data, queue_treatment, parameters):
        """
            Launch a loop to treat all the buffers acquired by the board.
            At each iteration, the method call "process" which should be
            defined in a child class.
        """

        start_time = time.time()
        self.treated_buffer = 0
        self.treated_sequance = 0

        # We acquire as many buffer as the board has acquired
        while parameters['measured_buffers'] is None or \
              self.treated_buffer < parameters['measured_buffers']:

            # We obtain the data in a 2D array (acquired_sample, records)
            data = self.data_2D(queue_data.get(), parameters)

            # If the number of sequence is equal to the number of records per buffer
            # Then we can treat data immediately
            if data.shape[0] == parameters['nb_sequence']:

                self.process(data, queue_treatment, parameters)
                self.treated_sequance += 1
            # If the number of sequence is smaller than the  number of acquired buffer
            # We have to treat data per package, each package corresponding to
            # a sequence.
            elif data.shape[0] > parameters['nb_sequence']:

                self.many_sequences_per_buffer(data, queue_treatment, parameters)
                self.treated_sequance += 1
            # If the number of sequence is larger than the number of records per
            # buffer
            else:
                self.less_sequence_per_buffer(data, queue_treatment, parameters)


            # Each loop implies a treatment of one buffer
            self.treated_buffer += 1

        # Return information about the data treatment
        elapsed_time = time.time() - start_time
        acquired_samples = parameters['samplesPerRecord']*parameters['records_per_buffer']\
                          *parameters['measured_buffers']
        acquired_bytes   = acquired_samples*2 # 2 bytes per sample

        parameters['message'] += 'Treatment completed in %f sec\n' % elapsed_time
        parameters['message'] += 'Treated %d bytes (%f Mbytes per sec)\n' %\
                                 (acquired_bytes, acquired_bytes/elapsed_time/1024**2)
        parameters['message'] += 'Treated %d samples (%f Ms per sec)\n' %\
                                 (acquired_samples, acquired_samples/elapsed_time/1e6)

        # Once the data are finished to be processed, we close the shared memory
        queue_data.close()
        queue_treatment.close()

        # Inform the parent process that the data treatment is finished
        if parameters['safe_treatment'][0]:
            parameters['safe_treatment'][1] = True
        else:
            parameters['safe_treatment'][0] = True


class Raw(DataTreatment):
    """
        Return the raw data without any treatment except the bitwise of 4 bits.
    """

    def __init__(self):

        self.data = np.array([])

    def process(self, data, queue_treatment, parameters):

        self.data = np.append(self.data, data)
        queue_treatment.put(self.data)


class Average(DataTreatment):
    """
        Class performing the average of the acquired data.
    """

    def __init__(self):

        self.mean = 0.
        self.std  = 0.

    def process(self, data, queue_treatment, parameters):
        """
            Calculate the average of the current buffer and average it with
            the previous measured data.
            Return the data in the memory buffer as the following:
            (data, std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # We obtain the current averaging for both and save them for
        # the next iteration

        # self.mean = self.mean_averaging(self.mean, data)
        # self.std  = self.std_averaging(self.std, data)
        self.mean = self.mean_averaging(self.mean, np.mean(data, axis=0))
        self.std  = self.std_averaging(self.std, np.std(data, axis=0))

        # print 'data', np.shape(data)
        # Send the result with the amplitude in V
        queue_treatment.put((self.mean, self.std))


class Average_time(DataTreatment):
    """
        Class performing the average of the acquired data.
    """

    def __init__(self):
    # __init__(self,acquisition_time, samplerate):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
        """
        # length=int(acquisition_time*samplerate)

        # We initialize np.array with the right dimension
        # self.mean = np.zeros(length)
        # self.std  = np.zeros(length)
        self.mean = 0.
        self.std  = 0.

    def process(self, data, queue_treatment, parameters):
        """
            Calculate the average of the current buffer and average it with
            the previous measured data.
            Return the data in the memory buffer as the following:
            (data, std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.mean = self.mean_averaging(self.mean, data)
        self.std  = self.std_averaging(self.std, data)

        # Send the result with the amplitude in V
        queue_treatment.put((self.mean, self.std))
        # queue_treatment.put((self.mean))


class AmplitudePhase(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in V and the phase in rad
    """



    def __init__(self, acquisition_time, samplerate, frequency):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in V and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # Obtain amplitude and phase
        amp   = 2.*np.sqrt(cos**2. + sin**2.)
        phase = np.angle(cos + 1j*sin)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.amp_mean = self.mean_averaging(self.amp_mean, np.mean(amp, axis=0))
        self.amp_std  = self.std_averaging(self.amp_std, np.std(amp, axis=0))

        self.phase_mean = self.mean_averaging(self.phase_mean, np.mean(phase, axis=0))
        self.phase_std  = self.std_averaging(self.phase_std, np.std(phase, axis=0))

        # We send the result
        queue_treatment.put((self.amp_mean, self.amp_std,\
                             self.phase_mean, self.phase_std))


class DBPhase(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the amplitude in dB and the phase in rad
    """



    def __init__(self, acquisition_time, samplerate, frequency, input_power,
                 impedance = 50.):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
                - input_power (float): in dBm
                - impedance (float): by default 50 ohm
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.

        self.impedance = impedance

        # We save the input power in V
        self.set_input_power(input_power)



    def set_input_power(self, input_power):
        """
            Set the input power.
            Input:
                - input_power (float): in dBm
        """

        # We save the input power in V
        self.input_amplitude = np.sqrt(1e-3*10**(input_power/10.)\
                                       *self.impedance)



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the amplitude in dB and the phase in rad as
            (amp_mean, amp_std, phase_mean, phase_std)
        """

        # Data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # Obtain amplitude and phase
        amp   = 2.*np.sqrt(cos**2. + sin**2.)
        phase = np.angle(cos + 1j*sin)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.amp_mean = self.mean_averaging(self.amp_mean, np.mean(amp, axis=0))
        self.amp_std  = self.std_averaging(self.amp_std, np.std(amp, axis=0))

        self.phase_mean = self.mean_averaging(self.phase_mean, np.mean(phase, axis=0))
        self.phase_std  = self.std_averaging(self.phase_std, np.std(phase, axis=0))

        queue_treatment.put((20.*np.log10(self.amp_mean/self.input_amplitude),\
                             20.*self.amp_std/self.amp_mean/np.log(10.),\
                             self.phase_mean, self.phase_std))


class RealImag(DataTreatment):
    """
        Return the amplitude and the phase of the acquired oscillations by
        using the cos, sin method.
        Return the real and imaginary part.
    """



    def __init__(self, acquisition_time, samplerate, frequency):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.real_mean = 0.
        self.real_std  = 0.
        self.imag_mean = 0.
        self.imag_std  = 0.



    def process(self, data, queue_treatment, parameters):
        """
            Return the amplitude and the phase of the acquired oscillations by
            using the cos, sin method.
            Return the real part and imaginary part in rad as
            (real_mean, real_std, imag_mean, imag_std)
        """

        # Data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        real = 2.*np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        imag = 2.*np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.real_mean = self.mean_averaging(self.real_mean, np.mean(real, axis=0))
        #self.real_std  = self.std_averaging(self.real_std, np.std(real, axis =0))

        self.imag_mean = self.mean_averaging(self.imag_mean, np.mean(imag, axis=0))
        #self.imag_std  = self.std_averaging(self.imag_std, np.std(imag, axis=0))

        # queue_treatment.put((self.real_mean, self.real_std,\
        #                      self.imag_mean, self.imag_std))

        queue_treatment.put((self.real_mean, self.imag_mean))


class AmplitudePhasePerSequence(DataTreatment):
    """
        Return the amplitude and the phase of the acquired sequences by
        using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the amplitude in V and the phase in rad
    """


    def __init__(self, acquisition_time, samplerate, frequency,nb_sequence):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # We initialize np.array with the right dimension
        self.amp_mean = np.zeros(nb_sequence)
        self.amp_std  = np.zeros(nb_sequence)

        self.phase_mean = np.zeros(nb_sequence)
        self.phase_std  = np.zeros(nb_sequence)

        #self.amp_mean = 0.
        #self.amp_std  = 0.

        #self.phase_mean = 0.
        #self.phase_std  = 0.



    def process(self, data, queue_treatment, parameters):

        # Data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        amp      = 2.*np.sqrt(cos**2. + sin**2.)
        amp_mean = self.mean_averaging(self.amp_mean, amp)

        phase      = np.angle(cos + 1j*sin)
        phase_mean = self.mean_averaging(self.phase_mean, phase)

        if self.treated_buffer < 2:

            self.amp_std   = amp_mean
            self.phase_std = phase_mean
        else:
            self.amp_std = np.sqrt((self.treated_buffer - 1.)*self.amp_std**2.\
                                     /self.treated_buffer
                                     + (amp - self.amp_mean)**2.\
                                    /(self.treated_buffer + 1.))

            self.phase_std = np.sqrt((self.treated_buffer - 1.)*self.phase_std**2.\
                                     /self.treated_buffer
                                     + (phase - self.phase_mean)**2.\
                                    /(self.treated_buffer + 1.))

        self.amp_mean   = amp_mean
        self.phase_mean = phase_mean

        # We send the result with the amplitude in V
        queue_treatment.put((self.amp_mean, self.amp_std,\
                             self.phase_mean, self.phase_std))


class AmplitudePhasePerSequencedB(DataTreatment):
    """
        Return the amplitude and the phase of the acquired sequences by
        using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the amplitude in dB and the phase in rad
    """
    def __init__(self, acquisition_time, samplerate, frequency, input_power,
                 impedance = 50.):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
                - input_power (float): in dBm
                - impedance (float): by default 50 ohm
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.amp_mean = 0.
        self.amp_std  = 0.
        self.phase_mean = 0.
        self.phase_std  = 0.

        self.impedance = impedance

        # We save the input power in V
        self.set_input_power(input_power)


    def set_input_power(self, input_power):
        """
            Set the input power.
            Input:
                - input_power (float): in dBm
        """

        # We save the input power in V
        self.input_amplitude = np.sqrt(1e-3*10**(input_power/10.)\
                                       *self.impedance)


    def process(self, data, queue_treatment, parameters):

        # Data in volt
        data = self.data_in_volt(data)

        # Build cos and sin
        cos = np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        sin = np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        amp      = 2.*np.sqrt(cos**2. + sin**2.)
        amp_mean = self.mean_averaging(self.amp_mean, amp)

        phase      = np.angle(cos + 1j*sin)
        phase_mean = self.mean_averaging(self.phase_mean, phase)

        if self.treated_buffer < 2:

            self.amp_std   = amp_mean
            self.phase_std = phase_mean
        else:
            self.amp_std = np.sqrt((self.treated_buffer - 1.)*self.amp_std**2.\
                                     /self.treated_buffer
                                     + (amp - self.amp_mean)**2.\
                                    /(self.treated_buffer + 1.))

            self.phase_std = np.sqrt((self.treated_buffer - 1.)*self.phase_std**2.\
                                     /self.treated_buffer
                                     + (phase - self.phase_mean)**2.\
                                    /(self.treated_buffer + 1.))

        self.amp_mean   = amp_mean
        self.phase_mean = phase_mean

        # We send the result with the amplitude in dB
        queue_treatment.put((20.*np.log10(self.amp_mean/self.input_amplitude),\
                             20.*self.amp_std/self.amp_mean/np.log(10.),\
                             self.phase_mean, self.phase_std))


class RealImagPerSequence(DataTreatment):
    """
        By using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the real part and the imaginary part in rad
    """


    def __init__(self, acquisition_time, samplerate, frequency, t_ro = None):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
                - t_ro (float): in second
        """

        # We need an integer number of oscillations
        if t_ro == None:
            # here there is relevant signal on all the acquired data set
            nb_oscillations = int(frequency*acquisition_time)
        else:
            # here there is relevant signal on only the t_ro part of the acquired data set
            nb_oscillations = int(frequency*t_ro)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        self.real_mean = 0.
        self.real_std  = 0.
        self.imag_mean = 0.
        self.imag_std  = 0.


    def process(self, data, queue_treatment, parameters):

            # Data in volt
            data = self.data_in_volt(data)

            # Build cos and sin
            real = 2.*np.mean(data[:,:self.nb_points]*self.cos, axis=1)
            imag = 2.*np.mean(data[:,:self.nb_points]*self.sin, axis=1)

            # We obtain the current averaging for both
            real_mean = self.mean_averaging(self.real_mean, real)
            imag_mean = self.mean_averaging(self.imag_mean, imag)


            self.real_mean = real_mean
            self.imag_mean = imag_mean

            #queue_treatment.put((self.real_mean, self.real_std, self.imag_mean, self.imag_std))
            queue_treatment.put((self.real_mean, self.imag_mean))


class RealImag_raw(DataTreatment):
    """
        Return the raw real and imaginary parts (ie not averaged over N) of the acquired oscillations by
        using the cos, sin method.
    """

    def __init__(self, acquisition_time, samplerate, frequency):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
        """

        # We need an integer number of oscillations
        nb_oscillations = int(frequency*acquisition_time)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # Data save
        self.real_raw = []
        self.imag_raw = []




    def process(self, data, queue_treatment, parameters):
        """
            Return the raw real and imaginary parts (ie not averaged) of the acquired oscillations by
            using the cos, sin method.
            Real and imaginary parts will be array of length=averaging
        """

        # Data in volt
        data = self.data_in_volt(data)
        # Build cos and sin
        real = 2.*np.mean(data[:,:self.nb_points]*self.cos, axis=1)
        imag = 2.*np.mean(data[:,:self.nb_points]*self.sin, axis=1)

        # We obtain the current averaging for both and save them for
        # the next iteration
        self.real_raw =  real
        self.imag_raw = imag

        # self.real_raw = np.concatenate((self.real_raw, real))
        # self.imag_raw = np.concatenate((self.imag_raw, imag))
        #self.real_std  = self.std_averaging(self.real_std, np.std(real, axis =0))

        # self.imag_mean = self.mean_averaging(self.imag_mean, np.mean(imag, axis=0))
        #self.imag_std  = self.std_averaging(self.imag_std, np.std(imag, axis=0))

        # queue_treatment.put((self.real_mean, self.real_std,\
        #                      self.imag_mean, self.imag_std))

        queue_treatment.put((self.real_raw, self.imag_raw))


class Average_IQ(DataTreatment):
    """
        Class performing the average of the acquired data.
    """

    def __init__(self, acquisition_time, samplerate, frequency, f_cutoff, order=1):

        # We obtain the number of point in these oscillations
        self.nb_points = int(samplerate*acquisition_time)

        # print 'size:', self.nb_points
        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        # self.mat = np.zeros((self.nb_points, self.nb_points))


        beta = f_cutoff/samplerate
        # alpha = 1. - beta

        # for i in np.arange(self.nb_points):
                # for j in np.arange(self.nb_points):
                #     if j<i or j==i:
                #         self.mat[i,j] = alpha**(i-j)

        # self.mat = self.mat*beta
        # for i in np.arange(order-1):
        #     print i
        #     self.mat = np.dot(self.mat, self.mat)

        # if order == 0:
        #     self.mat = np.identity(self.nb_points)
        self.B, self.A = scisig.butter(order, beta, btype='low' )
        # Data save
        self.real = np.zeros(self.nb_points)

        self.imag = np.zeros(self.nb_points)


    def process(self, data, queue_treatment, parameters):
        """
            Calculate the average of the current buffer and average it with
            the previous measured data.
            Return the data in the memory buffer as the following:
            (data, std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)

        real = 2.*data*self.cos
        imag = 2.*data*self.sin
        # print 'dt real',np.shape(real)

        # we filter the 2 omega
        # real_filtered = np.dot(self.mat, real)
        # imag_filtered = np.dot(self.mat, imag)
        # real_filtered = scisig.filtfilt(self.B, self.A, real)
        # imag_filtered = scisig.filtfilt(self.B, self.A, imag)

        real_filtered = scisig.lfilter(self.B, self.A, real)
        imag_filtered = scisig.lfilter(self.B, self.A, imag)
        # print 'dt real filtered',np.shape(real_filtered)

        # # We obtain the current averaging for both
        real = self.mean_averaging(self.real, real_filtered)
        imag = self.mean_averaging(self.imag, imag_filtered)

        # print np.shape(real)
        # print type(real)
        self.real = real
        self.imag = imag

        # Send the result with the real and imaginary parts in V
        queue_treatment.put((self.real, self.imag))

################################################################################
# Test Remy 2017_11_21
################################################################################

class SeveralRealImagPerSequence(DataTreatment):
    """
        By using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the real part and the imaginary part in V
    """


    def __init__(self, acquisition_time, samplerate, frequency, N, *args):
        """
        To BE tested!
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
                - N (int): number of acquisition pulses
                - *args : sequence in the form ((t_RO_1_start, t_RO_1_stop),
                    (t_RO_2_start, t_RO_2_stop),...., (t_RO_N_start, t_RO_N_stop))
        """

        if len(args) != N:
            raise ValueError('The number of time tuple should be equal to N')

        # We need an integer number of oscillations
        # if t_ro == None:
        #     # here there is relevant signal on all the acquired data set
        #     nb_oscillations = int(frequency*acquisition_time)
        # else:
        #     # here there is relevant signal on only the t_ro part of the acquired data set
        #     nb_oscillations = int(frequency*t_ro)
        #
        # if nb_oscillations < 1:
        #     raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points = np.reshape(np.zeros(2*N), (N,2))
        for i in np.arange(N):
            self.nb_points[i,0]  = int( int(frequency*(arg[i][0])) /frequency*samplerate)
            self.nb_points[i,1]  = int( int(frequency*(arg[i][1])) /frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points[-1, 1])/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        self.real_mean = np.zeros(N)
        self.real  =  np.zeros(N)
        self.imag_mean =  np.zeros(N)
        self.imag =  np.zeros(N)

        self.N = N


    def process(self, data, queue_treatment, parameters):

            # Data in volt
            data = self.data_in_volt(data)

            # Build cos and sin
            for i in np.arange(self.N):
                self.real[i] = 2.*np.mean(data[:,self.nb_points[i,0]:self.nb_points[i,1]]*self.cos, axis=1)
                self.imag[i] = 2.*np.mean(data[:,self.nb_points[i,0]:self.nb_points[i,1]]*self.sin, axis=1)

            # We obtain the current averaging for both
            self.real_mean  = self.mean_averaging(self.real_mean, self.real)
            self.imag_mean = self.mean_averaging(self.imag_mean, self.imag)


            #queue_treatment.put((self.real_mean, self.real_std, self.imag_mean, self.imag_std))
            queue_treatment.put((self.real_mean, self.imag_mean))

################################################################################
# reset
################################################################################

class RealImagPerSequence_reset(DataTreatment):
    """
        By using the cos, sin method.
        Take into account an integer number of oscillations (bigest one) for the
        calculation.
        Return the real part and the imaginary part in rad
    """


    def __init__(self, acquisition_time, samplerate, frequency, t_ro = None):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - frequency (float): in hertz
                - t_ro (float): in second
        """

        # We need an integer number of oscillations
        if t_ro == None:
            # here there is relevant signal on all the acquired data set
            nb_oscillations = int(frequency*acquisition_time)
        else:
            # here there is relevant signal on only the t_ro part of the acquired data set
            nb_oscillations = int(frequency*t_ro)

        if nb_oscillations < 1:
            raise ValueError('The number of acquired oscillations must be larger than 1')

        # We obtain the number of point in these oscillations
        self.nb_points  = int(nb_oscillations/frequency*samplerate)

        # We calculate the sin and cos
        time = np.arange(self.nb_points)/samplerate

        self.cos = np.cos(2.*np.pi*frequency*time)
        self.sin = np.sin(2.*np.pi*frequency*time)

        self.real= 0.
        self.imag = 0.


    def process(self, data, queue_treatment, parameters):

            # Data in volt
            data = self.data_in_volt(data)

            # Build cos and sin
            self.real = 2.*np.mean(data[:,:self.nb_points]*self.cos, axis=1)
            self.imag = 2.*np.mean(data[:,:self.nb_points]*self.sin, axis=1)


            queue_treatment.put((self.real, self.imag))


################################################################################

class HomodyneRealImagPerSequence(DataTreatment):
    """
        By using the homodyne method.
        Return the real part and the imaginary part in V
    """


    def __init__(self, pulse_time, samplerate, delta_t):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
                - t_ro (float): in second
        """

        # We need an integer number of oscillations

        self.nb_points = int(samplerate*pulse_time)
        self.nb_points2 = int(samplerate*(pulse_time+delta_t))
        print self.nb_points, self.nb_points2
        if self.nb_points < 1:
            raise ValueError('The number of acquired points must be larger than 1')


        self.data_mean_sig = 0.
        self.data_mean_no_sig = 0.


    def process(self, data, queue_treatment, parameters):

            # Data in volt
            data = self.data_in_volt(data)
            # print np.shape(data)
            # print self.nb_points

            # Build cos and sin
            data_sig = np.mean(data[:,:self.nb_points], axis=1)
            data_no_sig = np.mean(data[:,self.nb_points2:], axis=1)
            # print np.shape(data)
            # We obtain the current averaging for both
            data_mean_sig = self.mean_averaging(self.data_mean_sig, data_sig)
            data_mean_no_sig = self.mean_averaging(self.data_mean_no_sig, data_no_sig)


            self.data_mean_sig = data_mean_sig
            self.data_mean_no_sig = data_mean_no_sig

            queue_treatment.put((self.data_mean_sig, self.data_mean_no_sig))

class HomodyneRealImag_raw(DataTreatment):
    """
        Return the raw real and imaginary parts (ie not averaged over N) of the acquired oscillations by
        using the cos, sin method.
    """

    def __init__(self, pulse_time, samplerate, delta_t):
        """
            Input:
                - pulse_time (float): in second
                - samplerate (float): in sample per second

        """


        # We obtain the number of point in these oscillations
        self.nb_points  = int(pulse_time*samplerate)
        self.nb_points2 = int((pulse_time+delta_t)*samplerate)

        # Data save
        self.data_pulse_raw = []
        self.data_nopulse_raw = []




    def process(self, data, queue_treatment, parameters):
        """
            Return the raw real and imaginary parts (ie not averaged) of the acquired oscillations by
            using the cos, sin method.
            Real and imaginary parts will be array of length=averaging
        """

        # Data in volt
        data = self.data_in_volt(data)

        self.data_pulse_raw = np.mean(data[:,:self.nb_points], axis=1)
        self.data_nopulse_raw = np.mean(data[:,self.nb_points2:], axis=1)


        queue_treatment.put((self.data_pulse_raw, self.data_nopulse_raw))

class HomodyneRealImag_raw_sevRO(DataTreatment):
    """
        Return the raw real and imaginary parts (ie not averaged over N) of the acquired oscillations by
        using the cos, sin method.
    """

    def __init__(self, pulse_time1, t1_start, pulse_time2, t2_start, samplerate, delta_t):
        """
            Input:
                - pulse_time (float): in second
                - samplerate (float): in sample per second

        """


        # We obtain the number of point in these oscillations
        self.nb_points_start1 = int(t1_start*samplerate)
        self.nb_points_end1   = int((t1_start+pulse_time1)*samplerate)

        self.nb_points_start2 = int(t2_start*samplerate)
        self.nb_points_end2   = int((t2_start+pulse_time2)*samplerate)
        self.nb_points_stop = self.nb_points_end2 + int(delta_t*samplerate)

        # Data save
        self.data_pulse_raw1 = []
        self.data_pulse_raw2 = []
        self.data_nopulse_raw = []




    def process(self, data, queue_treatment, parameters):
        """
            Return the raw real and imaginary parts (ie not averaged) of the acquired oscillations by
            using the cos, sin method.
            Real and imaginary parts will be array of length=averaging
        """

        # Data in volt
        data = self.data_in_volt(data)

        self.data_pulse_raw1 = np.mean(data[:,self.nb_points_start1:self.nb_points_end1], axis=1)
        self.data_pulse_raw2 = np.mean(data[:,self.nb_points_start2:self.nb_points_end2], axis=1)
        self.data_nopulse_raw = np.mean(data[:,self.nb_points_stop:], axis=1)

        # self.data_pulse_raw1 -= self.data_nopulse_raw
        # self.data_pulse_raw2 -= self.data_nopulse_raw
        queue_treatment.put((self.data_pulse_raw1, self.data_pulse_raw2, self.data_nopulse_raw))


class HomodyneRealImag_Nraw(DataTreatment):
    """
        By using the homodyne method.
        Return the real part and the imaginary part in V
    """


    def __init__(self, pulse_time, samplerate, delta_t, N):
        """
            Input:
                - acquisition_time (float): in second
                - samplerate (float): in sample per second
        """

        # We need an integer number of oscillations
        self.N = N
        self.nb_points = int(samplerate*pulse_time)
        self.nb_points_tot = N*self.nb_points
        self.nb_points2 =  int((N*pulse_time+delta_t)*samplerate)

        self.data_pulse_raw = []
        for i in np.arange(N):
            self.data_pulse_raw.append([])
        self.data_nopulse_raw = 0.


    def process(self, data, queue_treatment, parameters):

            # Data in volt
            data = self.data_in_volt(data)

            for i in np.arange(self.N):
                self.data_pulse_raw[i][:] = np.mean(data[:,i*self.nb_points:(i+1)*self.nb_points], axis=1)

            self.data_nopulse_raw = np.mean(data[:,self.nb_points2:], axis=1)

            # self.data_pulse_raw -= self.data_nopulse_raw

            queue_treatment.put((self.data_pulse_raw, self.data_nopulse_raw) )

# class Homodyne_Tchebytchev(DataTreatment):
#     """
#         Class performing the Tchebytchev data.
#     """
#
#     def __init__(self, acquisition_time, samplerate, tau, t0):
#
#         # We obtain the number of point in these oscillations
#         self.nb_points = int(samplerate*acquisition_time)
#         self.N_tau = int(samplerate*tau)
#         self.nb_points0 = int(samplerate*t0)
#
#         # Data save
#         self.data = np.reshape(np.zeros(4*self.nb_points), (4, self.nb_points))
#         self.data_old = np.reshape(np.zeros(4*self.nb_points), (4, self.nb_points))
#
#     def process(self, data, queue_treatment, parameters):
#         """
#             Calculate the average of the current buffer and average it with
#             the previous measured data.
#             Return the data in the memory buffer as the following:
#             (data, std)
#         """
#
#         # We obtain the data in volt
#         data = self.data_in_volt(data)
#         # print np.shape(data)
#         data0 = np.mean(data[:,:self.nb_points0], axis=1)
#
#         # imag_filtered = scisig.filtfilt(self.B, self.A, imag)
#         for i in np.arange(len(data[:,0])):
#             # print i
#             self.data[i,:] = np.convolve(data[i,:]- data0[i], np.ones(self.N_tau)/self.N_tau, mode='same')
#
#         # # We obtain the current averaging for both
#         # self.data = data_filtered
#         # self.data_old = self.mean_averaging(self.data_old, self.data)
#
#
#         # Send the result with the real and imaginary parts in V
#         queue_treatment.put((self.data_old))

class Homodyne_Tchebytchev(DataTreatment):
    """
        Class performing the Tchebytchev data.
    """

    def __init__(self, acquisition_time, samplerate, f_cutoff, r_dB, order, doweaverage):

        # We obtain the number of point
        self.nb_points = int(samplerate*acquisition_time)
        self.doweaverage = doweaverage
        beta = f_cutoff/samplerate

        self.B, self.A = scisig.cheby2(order, r_dB, beta, btype='low' )
        # Data save
        self.data = np.zeros(self.nb_points)

    def process(self, data, queue_treatment, parameters):
        """
            Calculate the average of the current buffer and average it with
            the previous measured data.
            Return the data in the memory buffer as the following:
            (data, std)
        """

        # We obtain the data in volt
        data = self.data_in_volt(data)
        # print np.shape(data)
        data_filtered = scisig.lfilter(self.B, self.A, data,  axis=1)
        # print np.shape(data_filtered)

        if self.doweaverage:
            self.data = self.mean_averaging(self.data, data_filtered)
        else:
            self.data = data_filtered

        queue_treatment.put((self.data))


class HomodyneRealImagPerSequenceWeighted(DataTreatment):
    """
        By using the homodyne method.
        Return the real part and the imaginary part in V
    """


    def __init__(self, acquisition_time, pulse_time, samplerate, delta_t, tau, t_start=0.):
        """
            Input:
                - pulse_time (float): in second
                - samplerate (float): in sample per second
                - delta_t (float): in second
                - tau (float): cavity raising time in second
        """

        self.nb_points_tot = int(samplerate*acquisition_time)

        self.time = np.arange(self.nb_points_tot)/samplerate

        Heavi1 = np.piecewise(self.time-t_start,
            [(self.time-t_start)<0, (self.time-t_start) == 0, (self.time-t_start)>0],
            [0., 0.5, 1.] )
        t_stop = t_start + pulse_time
        Heavi2 = np.piecewise(self.time-t_stop,
            [(self.time-t_stop)<0, (self.time-t_stop) == 0, (self.time-t_stop) >0],
            [0., 0.5, 1.] )
        self.ideal_pulse = (1.-np.exp(-(self.time-t_start)/tau))*Heavi1 - Heavi2*(1.-np.exp(-(self.time-t_stop)/tau))

        self.nb_points = int(samplerate*pulse_time)
        self.nb_points2 = int(samplerate*(pulse_time+delta_t))
        # print self.nb_points, self.nb_points2
        if self.nb_points < 1:
            raise ValueError('The number of acquired points must be larger than 1')


        self.data_mean_sig = 0.
        self.data_mean_no_sig = 0.


    def process(self, data, queue_treatment, parameters):

            # Data in volt
            data = self.data_in_volt(data)

            # Build cos and sin
            data_sig = np.mean(self.ideal_pulse[:self.nb_points]*data[:,:self.nb_points], axis=1)#/np.mean(self.ideal_pulse)
            data_no_sig = np.mean(data[:,self.nb_points2:], axis=1)
            # print np.shape(data)
            # We obtain the current averaging for both
            data_mean_sig = self.mean_averaging(self.data_mean_sig, data_sig)
            data_mean_no_sig = self.mean_averaging(self.data_mean_no_sig, data_no_sig)


            self.data_mean_sig = data_mean_sig
            self.data_mean_no_sig = data_mean_no_sig

            queue_treatment.put((self.data_mean_sig, self.data_mean_no_sig))

class HomodyneRealImag_rawWeighted(DataTreatment):
    """
        Return the raw real and imaginary parts (ie not averaged over N) of the acquired oscillations by
        using the cos, sin method.
    """

    def __init__(self, acquisition_time, pulse_time, samplerate, delta_t, tau, t_start=0.):
        """
            Input:
                - pulse_time (float): in second
                - samplerate (float): in sample per second

        """

        self.nb_points_tot = int(samplerate*acquisition_time)
        # We obtain the number of point in these oscillations
        self.nb_points  = int(pulse_time*samplerate)
        self.nb_points2 = int((pulse_time+delta_t)*samplerate)

        self.time = np.arange(self.nb_points_tot)/samplerate
        Heavi1 = np.piecewise(self.time-t_start,
            [(self.time-t_start)<0, (self.time-t_start) == 0, (self.time-t_start)>0],
            [0., 0.5, 1.] )
        t_stop = t_start + pulse_time
        Heavi2 = np.piecewise(self.time-t_stop,
            [(self.time-t_stop)<0, (self.time-t_stop) == 0, (self.time-t_stop) >0],
            [0., 0.5, 1.] )
        self.ideal_pulse = (1.-np.exp(-(self.time-t_start)/tau))*Heavi1 - Heavi2*(1.-np.exp(-(self.time-t_stop)/tau))

        # Data save
        self.data_pulse_raw = []
        self.data_nopulse_raw = []




    def process(self, data, queue_treatment, parameters):
        """
            Return the raw real and imaginary parts (ie not averaged) of the acquired oscillations by
            using the cos, sin method.
            Real and imaginary parts will be array of length=averaging
        """

        # Data in volt
        data = self.data_in_volt(data)

        # self.data_pulse_raw = np.mean(data[:,:self.nb_points], axis=1)
        self.data_pulse_raw = np.mean(self.ideal_pulse[None, :self.nb_points]*data[:,:self.nb_points], axis=1)#\
                            #/np.mean(self.ideal_pulse)
        self.data_nopulse_raw = np.mean(data[:,self.nb_points2:], axis=1)


        queue_treatment.put((self.data_pulse_raw, self.data_nopulse_raw))


class HomodyneRealImag_raw_sevROWeighted(DataTreatment):
    """
        Return the raw real and imaginary parts (ie not averaged over N) of the acquired oscillations by
        using the cos, sin method.
    """

    def __init__(self, acquisition_time, pulse_time1, t1_start, pulse_time2,
                                t2_start, samplerate, delta_t, tau):
        """
            Input:
                - pulse_time (float): in second
                - samplerate (float): in sample per second

        """

        self.nb_points_tot = int(samplerate*acquisition_time)
        self.time = np.arange(self.nb_points_tot)/samplerate

        # We obtain the number of point in these oscillations
        self.nb_points_start1 = int(t1_start*samplerate)
        self.nb_points_end1   = int((t1_start+pulse_time1)*samplerate)
        Heavi1 = np.piecewise(self.time-t1_start,
            [(self.time-t1_start)<0, (self.time-t1_start) == 0, (self.time-t1_start)>0],
            [0., 0.5, 1.] )
        t_stop = t1_start + pulse_time1
        Heavi2 = np.piecewise(self.time-t_stop,
            [(self.time-t_stop)<0, (self.time-t_stop) == 0, (self.time-t_stop) >0],
            [0., 0.5, 1.] )
        self.ideal_pulse1 = (1.-np.exp(-(self.time-t1_start)/tau))*Heavi1 - Heavi2*(1.-np.exp(-(self.time-t_stop)/tau))


        self.nb_points_start2 = int(t2_start*samplerate)
        self.nb_points_end2   = int((t2_start+pulse_time2)*samplerate)
        Heavi1 = np.piecewise(self.time-t2_start,
            [(self.time-t2_start)<0, (self.time-t2_start) == 0, (self.time-t2_start)>0],
            [0., 0.5, 1.] )
        t_stop = t2_start + pulse_time2
        Heavi2 = np.piecewise(self.time-t_stop,
            [(self.time-t_stop)<0, (self.time-t_stop) == 0, (self.time-t_stop) >0],
            [0., 0.5, 1.] )
        self.ideal_pulse2 = (1.-np.exp(-(self.time-t2_start)/tau))*Heavi1 - Heavi2*(1.-np.exp(-(self.time-t_stop)/tau))
        print np.mean(self.ideal_pulse1), np.mean(self.ideal_pulse2)


        self.nb_points_stop = self.nb_points_end2 + int(delta_t*samplerate)

        # Data save
        self.data_pulse_raw1 = []
        self.data_pulse_raw2 = []
        self.data_nopulse_raw = []




    def process(self, data, queue_treatment, parameters):
        """
            Return the raw real and imaginary parts (ie not averaged) of the acquired oscillations by
            using the cos, sin method.
            Real and imaginary parts will be array of length=averaging
        """

        # Data in volt
        data = self.data_in_volt(data)

        # self.data_pulse_raw1 = np.mean(data[:,self.nb_points_start1:self.nb_points_end1], axis=1)

        self.data_pulse_raw1 = np.mean(self.ideal_pulse1[None,self.nb_points_start1:self.nb_points_end1]\
                    *data[:,self.nb_points_start1:self.nb_points_end1], axis=1)#\
                    # /np.mean(self.ideal_pulse1)

        self.data_pulse_raw2 =  np.mean(self.ideal_pulse2[None,self.nb_points_start2:self.nb_points_end2]\
                    *data[:,self.nb_points_start2:self.nb_points_end2], axis=1)#\
                    # /np.mean(self.ideal_pulse2)
        # np.mean(data[:,self.nb_points_start2:self.nb_points_end2], axis=1)

        self.data_nopulse_raw = np.mean(data[:,self.nb_points_stop:], axis=1)

        # self.data_pulse_raw1 -= self.data_nopulse_raw
        # self.data_pulse_raw2 -= self.data_nopulse_raw
        queue_treatment.put((self.data_pulse_raw1, self.data_pulse_raw2, self.data_nopulse_raw))
