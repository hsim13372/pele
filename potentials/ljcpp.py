from math import *
import numpy as np
import cpp.ljcpp_ as ljc

class LJ:
    """binary lennard jones potential with smooth cutoff"""
    def __init__(self):
        print "using lenard jones cpp implementation"
        # self.natoms = natoms

    def getEnergy(self, coords):
        print "getting energy only"
        E = ljc.energy(coords)
        return E

    def getEnergyGradient(self, coords):
        grad=np.zeros(coords.shape[0], np.float64)
        E = ljc.gradient(coords, grad)
        #print E
        #print coords
        #print grad
        return E, grad 