from instrument import Instrument
import instruments
import numpy
import types
import logging
import datetime
from datetime import datetime
 

class virtual_temperatures(Instrument):
    '''
    This is the driver for the virtual instrument which can create a microwave pulse

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'virtual_afg_burst_pulse', afg='name_afg', mwsrc='name_microwave_generator')
    '''
    
    def __init__(self, name):
        '''
            Initialize the virtual instruments
                
                Input:
                    - name: Name of the virtual instruments
                    - afg: Name of the tektronix AFG3252
                    - mwsrc: Name given to the microwave_generator
                    - live_update (bool): The microwave pulse will be update at each setting or not
                    
                
                Output:
                    None
        '''
        
        Instrument.__init__(self, name, tags=['virtual'])
        
        #Parameters
        self.add_parameter('temp_ch1', flags=Instrument.FLAG_GET, units='K', type=types.FloatType)
        self.add_parameter('temp_ch2', flags=Instrument.FLAG_GET, units='K', type=types.FloatType)
        self.add_parameter('temp_ch5', flags=Instrument.FLAG_GET, units='K', type=types.FloatType)
        self.add_parameter('temp_ch6', flags=Instrument.FLAG_GET, units='K', type=types.FloatType)
        
        self.get_all()


    def get_all(self):
        '''
            Get all parameters of the virtual device
            
            Input:
                None
            
            Output:
                None
        '''
        
        self.get_temp_ch1()
        self.get_temp_ch2()
        self.get_temp_ch5()
        self.get_temp_ch6()
        
   

#########################################################
#
#                       Temperatures
#
#########################################################

    def do_get_temp_ch1(self):
        '''
        Get the temp of ch1 from file

        Input:
            None

        Output:
            T (float) : in K
        '''
#        i = datetime.datetime.now()
        i = datetime.now()
#        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s-0%s-0%s/CH1 T %s-0%s-0%s.log' %(i.year-2000,i.month,i.day,i.year-2000,i.month,i.day))
        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s/CH1 T %s.log' %(i.strftime('%y-%m-%d'),i.strftime('%y-%m-%d')))
        tdats=tempdata.read()
        tdats=tdats.split(',')
        self.temp_ch1=float(tdats[len(tdats)-1]) 
        tempdata.close()
        return self.temp_ch1


    def do_get_temp_ch2(self):
        '''
        Get the temp of ch1 from file

        Input:
            None

        Output:
            T (float) : in K
        '''
#        i = datetime.datetime.now()
        i = datetime.now()
#        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s-%s-%s/CH2 T %s-%s-%s.log' %(i.year-2000,i.month,i.day,i.year-2000,i.month,i.day))		
        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s/CH2 T %s.log' %(i.strftime('%y-%m-%d'),i.strftime('%y-%m-%d')))
        tdats=tempdata.read()
        tdats=tdats.split(',')
        self.temp_ch2=float(tdats[len(tdats)-1]) 
        tempdata.close()
        return self.temp_ch2


    def do_get_temp_ch5(self):
        '''
        Get the temp of ch1 from file

        Input:
            None

        Output:
            T (float) : in K
        '''
#        i = datetime.datetime.now()
        i = datetime.now()		
#        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s-%s-%s/CH5 T %s-%s-%s.log' %(i.year-2000,i.month,i.day,i.year-2000,i.month,i.day))
        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s/CH5 T %s.log' %(i.strftime('%y-%m-%d'),i.strftime('%y-%m-%d')))
        tdats=tempdata.read()
        tdats=tdats.split(',')
        self.temp_ch5=float(tdats[len(tdats)-1]) 
        tempdata.close()
        return self.temp_ch5


    def do_get_temp_ch6(self):
        '''
        Get the temp of ch1 from file

        Input:
            None

        Output:
            T (float) : in K
        '''
#        i = datetime.datetime.now()
        i = datetime.now()
#        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s-%s-%s/CH6 T %s-%s-%s.log' %(i.year-2000,i.month,i.day,i.year-2000,i.month,i.day))		
        tempdata=open('//WIN-KRIOSTA/Users/wiebke.guichard/Desktop/Bluefors/Log/Temperature/%s/CH6 T %s.log' %(i.strftime('%y-%m-%d'),i.strftime('%y-%m-%d')))
        tdats=tempdata.read()
        tdats=tdats.split(',')
        self.temp_ch6=float(tdats[len(tdats)-1]) 
        tempdata.close()
        return self.temp_ch6

