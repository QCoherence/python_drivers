from instrument import Instrument
import urllib2
import logging
import types
from numpy import pi


class RCDAT(Instrument):

    def __init__(self, name, address, reset = False):
        Instrument.__init__(self, name, tags=['physical'])
        self.address = address
