# AWG7000.py class
#
# FArshad Foroughi <farshad.foroughi@neel.cnrs.fr>, 2018
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

from instrument import Instrument
import visa
import types
import logging
import numpy as np
import struct
import pyvisa.constants as vc
import ctypes
import re
import math
import itertools


################### Constants

# MARKER_QUANTUM = 2        #: quantum of marker-length and marker-offset
# _EX_DAT_MARKER_1_MASK = 0x20000000L #: the mask of marker 1 in the extra-data (32-bits) value
# _EX_DAT_MARKER_2_MASK = 0x10000000L #: the mask of marker 2 in the extra-data (32-bits) value
# _EX_DAT_M2_MASK_NICO = 0x8000
# _EX_DAT_M1_MASK_NICO = 0x4000
# octet = 8
# number_of_bits = 16
#
# Channels=(1,2,3,4)
# Mark_num = (1,2)
###### Useful functions
def _engineer_to_scienc(value):
        '''
        Function to convert a value form engineering format to scientific format

        Input:
            value (int): value to convert

        Output:
            converted value (int)
        '''
        multipliers = {'n':1e-9,'u':1e-6,'m':1e-3,'k': 1e3, 'M': 1e6, 'G': 1e9}
        return int(float(value[:-1])*multipliers[value[-1]])

class AWG7000(Instrument):
    '''
    Initializes the AWG7000
    Input:
        name (string)    : name of the instrument
        address (string) : TCPIP/GPIB address
        port (int)       :port number
        reset (bool)     : Reset to default values

    Output:
        None
    '''
    def __init__(self, name, address,reset = False):
        '''
        Initializes the AWG7000

        Input:
            name (string)    : name of the instrument
            address (string) : TCPIP/GPIB address
            port (int)       :port number
            reset (bool)     : Reset to default values

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])
        rm = visa.ResourceManager()

        self._address = address
        self.add_function('reset')
        self.msgEnd='\n'
        self.delimiter=';:'

        # since the 20th of october 2015, it seems that the complete adress of the TABOR is the IP adress plus the SOCKET...

        try:
            inst = rm.open_resource(self._address+'::4000::SOCKET')
            inst.timeout = 20000L

            inst.visalib.set_buffer(inst.session, vc.VI_READ_BUF, 4000)
            inst.visalib.set_buffer(inst.session, vc.VI_WRITE_BUF, 32000)

            inst.read_termination = '\n'
            inst.write_termination = '\n'
            inst.clear()
            self._visainstrument = inst
            logging.debug(__name__ + ' : visa session opened correctly')

        except:
            logging.debug(__name__ + ' : could not open visa session')
            raise ValueError(__name__ + ' : could not open visa session')

        if reset:
            self.reset()


    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        self.sendMessage("*RST")

    def Output(self, channel=1, state='ON'):
        '''
        Sets the state of a given channel to ON or OFF

        Input:
            channel (int): Channel ID
            state (string): 'ON' or 'OFF'

        Output:
            None
        '''

        if state in ('ON','OFF'):
            self.sendMessage('OUTPUT{}:STATE {}'.format(channel,state))


    def Amplitude(self,channel=1,amp=1):
        '''
        Sets the amplitude of the DAC

        Input:
            channel (int): Channel ID
            amp (float): less than 1 (1mv resolution)

        Output:
            None
        '''
        self.sendMessage('SOURCE{}:VOLTAGE:AMPLITUDE {}'.format(channel,amp))


    def set_SamplingRate(self,freq=12e9):
        '''
        sets the sampling rate
        Input:
            sampling frequancy in Hz
        Output:
            None
        '''

        self.sendMessage('SOURCE1:FREQUENCY {}'.format(freq))

    def DAC_res(self, channel=1, resolution=10):
        '''
        sets the DAC resolution
        Input:
        channel (int): 1 or 2
        resolution(int): 8 or 10
        Output:
        None
        '''
        self.sendMessage('SOURCE{}:DAC:RESOLUTION {}'.format(channel,resolution))

    def newWaveform(self,name,size,stringOnly=0):
        """
        Creates a new Waveform slot without data in it
        """
        msg='WLIST:WAVeform:NEW "' +name+ '", ' + str(size)+ ', REAL'
        if stringOnly==0:
            self.sendMessage(msg)
        else:
            return msg

    def transmitWaveformData(self,name,data,stringOnly=0,marker1=[],marker2=[]):
        """
        Writes the Data given into the Waveformslot 'name' created by the function newWaveform
        """
        MARKER1= 0b01000000
        MARKER2= 0b10000000
        if (marker1==[]):
            marker1=np.zeros(len(data),dtype=int)
        else:
            marker1=marker1*MARKER1

        if (marker2==[]):
            marker2=np.zeros(len(data),dtype=int)
        else:
            marker2=marker2*MARKER2
#        self.newWaveform(name,len(data))
        block_data=''
        msgStart=('WLISt:WAVeform:DATA "'+name+'",0,'+str(len(data))+',#'+str(len(str(5*len(data))))+str(5*len(data)))
        for val,m1,m2 in itertools.izip(data,marker1,marker2):
            converted_data=struct.pack('<fB',float(val),m1+m2) # or should work aswell

            block_data = block_data + converted_data
        msg=msgStart+block_data

        if stringOnly==0:
            self.sendMessage(msg)
        else:
            return msg


    def readWaveformNames(self):
        """
        Returns a List of all the Waveformnames (strings without enclosing "s)
        """
        ansr=self.query('WLIST:SIZE?')
        msg=[]
        for i in range (1,int(ansr)+1):
            msg.append('WLIST:NAME? '+str(i))
        wnames = self.query(msg)
        names=re.findall('".*?"',wnames)
        strippednames=[]
        for name in names:
            strippednames.append(name.rstrip('"').lstrip('"'))
        return strippednames

    def deleteWaveforms(self,Names):
        """
        Deletes a list of Waveforms given to the function as strings
        The names are without the enclosing "s and is compliant with the format returned by the function readWaveformNames.

        Passing a single string will try to delete only this Waveform.
        """
        if isinstance(Names, basestring):
            dlmsg='WLISt:WAVeform:DELete "'+Names+'"'
        else:
            try:
                dlmsg=[]
                for name in Names:
                    dlmsg.append('WLISt:WAVeform:DELete "'+name+'"')
            except TypeError:
                print('TypeError occourred on Waveform Names in function deleteWaveforms, please ensure that message is a string or a list of strings')
        self.sendMessage(dlmsg)

    def changeChannelDelay(self,Channel,Delay,stringOnly=0):
        """
        Changes the delay of the Channel to 'Delay' picoseconds
        """
        msg='SOURCE'+str(Channel)+':DELAY:ADJUST '+str(Delay)
        if stringOnly==0:
            self.sendMessage(msg)
        else:
            return msg

    def changeChannelPhase(self,Channel,Phase,stringOnly=0):
        """
        Changes the phase of the Channel to Phase in Degrees
        """
        msg='SOURCE'+str(Channel)+':PHASE:ADJUST '+str(Phase)
        if stringOnly==0:
            self.sendMessage(msg)
        else:
            return msg

    def changeChannelAmplitude(self,Channel,Amplitude,stringOnly=0):
        msg='SOURCE'+str(Channel)+':VOLTAGE:AMPLITUDE '+str(Amplitude)

        if stringOnly==0:
            self.sendMessage(msg)
        else:
            return msg


    def changeChannelOffset(self,Channel,Offset,stringOnly=0):
        msg='SOURCE'+str(Channel)+':VOLTAGE:OFFSET '+str(Offset)

        if stringOnly==0:
            self.sendMessage(msg)
        else:
            return msg

    def setChannelWaveformSequence(self,Channel,WaveformName,SequenceIndex=1):
        """
        Puts Waveform 'WaveformName' into Channel 'Channel'.

        If the RunMode is SEQuence, it will use the optional Argument 'SequenceIndex' to determine the element in the sequence.
        """
#SEQuence:ELEMent1:WAVeform1 "waveseq1_channel1";


        self.sendMessage('SEQuence:ELEMent'+str(SequenceIndex)+':WAVeform'+str(Channel)+' "'+WaveformName+'"')

    def setChannelWaveform(self,Channel,WaveformName):
        """
        Puts Waveform 'WaveformName' into Channel 'Channel'.

        If the RunMode is SEQuence, it will use the optional Argument 'SequenceIndex' to determine the element in the sequence.
        """
        self.sendMessage('SOUR'+str(Channel)+':WAVeform "'+ WaveformName+'"')

    def queryRunMode(self):
        return self.query("AWGControl:RMODe?")


    def setRunMode(self,RunMode): #TODO implement stringonly
        """
        Sets the runmode of the machine
        RunModes are : CONTinuous, TRIGgered, GATed, SEQuence, ENHanced
        use CONT for normal operation and SEQuence for sequence operation
        """
        self.sendMessage("AWGControl:RMODe "+RunMode)

    def createSequence(self, SequenceLength):#TODO implement stringonly
        """
        This has to be called to initialize a sequence
        """
        self.sendMessage('SEQuence:LENGth '+str(SequenceLength))

    def setSeqElementGoto(self,SequenceIndex=1,State=1,Index=1):#TODO implement stringonly
        """
        Used to set JumpMode for a sequence Element
        States are : 0(OFF) , 1(ON)
        """
        self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":GOTO:STATe "+str(State))
        if (State==1):
            self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":GOTO:INDex "+str(Index))

    def setSeqElementJump(self,SequenceIndex,Type='INDex',Index=1):#TODO implement stringonly
        """
        Used to set JumpMode for a sequence Element
        Types are : INDex , NEXT, OFF
        """
        self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":JTARget:TYPE "+str(Type))
        if (Type=='INDex'):
            self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":JTARget:INDex "+str(Index))

    def setSeqElementLooping(self,SequenceIndex=1,Repeat=1,InfiniteLoop=0):#TODO implement stringonly
        """
        Used to set JumpMode for a sequence Element
        States are : 0(OFF) , 1(ON)
        """

        if (InfiniteLoop==1):
            self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":LOOP:INFinite 1")
        else:
            self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":LOOP:INFinite 0")
            self.sendMessage("SEQuence:ELEMent"+str(SequenceIndex)+":LOOP:COUNt "+str(Repeat))

    def set_trigger(self, Source='EXT', Level=1.0, Impedance=50, Slope='NEG', Timer= 100e-3 ):
        '''
        Sets the state of a given channel to ON or OFF

        Input:
            Source (string): 'EXT' or 'INT'
            Level (float)
            Impedance (int): 50 or 1000
            Slope (String): 'POS' or 'NEG'
            Timer (float)

        Output:
            None
        '''

        if Source=='EXT':
            self.sendMessage('TRIGGER:SEQUENCE:SOURCE EXT')
            self.sendMessage('TRIGGER:SEQUENCE:SLOPE {}'.format(Slope))
            self.sendMessage('TRIGGER:SEQUENCE:LEVEL {}'.format(Level))
            self.sendMessage('TRIGGER:SEQUENCE:IMPEDANCE {}'.format(Impedance))
        elif Source=='INT':
            self.sendMessage('TRIGGER:SEQUENCE:SOURCE INT')
            self.sendMessage('TRIGGER:SEQUENCE:TIMER {}'.format(Timer))
    def RUN(self,state=1):
        '''
        run or stops the awg
        input:
            state(int): 0 or 1

        '''
        if state==1:
            self.sendMessage('AWGCONTROL:RUN:IMMEDIATE')
        elif state==0:
            self.sendMessage('AWGCONTROL:STOP:IMMEDIATE')

    def sendMessage(self,msg):

           #        if isinstance(msg, string_types):doesn't work anymore in python 3
            #            self.s.send((msg+self.msgEnd).encode('utf-8'))
        if isinstance(msg, basestring):
            self._visainstrument.write_raw(msg+self.msgEnd)



        else:
            try:

                fullMsg=''
                for msgPart in msg:
                    fullMsg=fullMsg+msgPart+self.delimiter
                fullMsg.rstrip(self.delimiter)
                self._visainstrument.write_raw(fullMsg+self.msgEnd)

            except TypeError:

                print('TypeError occourred on message text, please ensure that message is a string or a list of strings')

    def query(self,msg):
        return self._visainstrument.query(msg)
