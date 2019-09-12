# -*- coding: utf-8 -*-
# Vaunix_attenuator if a driver for the tunnable vaunix attenuator using dll file VNX_atten
# written by Sébastien Léger, 2019
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

from ctypes import *
from instrument import Instrument
import logging
import types


class Vaunix_phase_shifter(Instrument): 

    def __init__(self,name,serial_number):
    
        Instrument.__init__(self, name, tags=['physical'])
        self._serial_number = serial_number
        logging.info( '{}: Initializing attenuator'.format(serial_number))
        
        
        self.add_parameter('phase_shift', 
                            flags  = Instrument.FLAG_GETSET, 
                            units  = 'dB', 
                            minval = 0,
                            maxval = 360,
                            type = types.IntType)

        self._vnx = cdll.VNX_dps
        DeviceIDArray = c_int * 64
        self._Devices = DeviceIDArray()
        self._vnx.fnLPS_GetNumDevices()
        self._vnx.fnLPS_GetDevInfo(self._Devices)
        
        
        self._device_number = 0  
        while self._vnx.fnLPS_GetSerialNumber(self._Devices[self._device_number]) != serial_number:
            self._device_number +=1
         
        self._vnx.fnLPS_InitDevice(self._Devices[self._device_number])
        self._vnx.fnLPS_SetPhaseAngle(self._Devices[self._device_number], 0)
        
    def do_set_phase_shift(self, value): 
        logging.info( '{} : Setting the attenuation at {}'.format(self._serial_number, value))
        self._vnx.fnLPS_SetPhaseAngle(self._Devices[self._device_number],value) 
        
    def do_get_phase_shift(self): 
        phase_shift = self._vnx.fnLPS_GetPhaseAngle(self._Devices[self._device_number]) 
        return phase_shift
