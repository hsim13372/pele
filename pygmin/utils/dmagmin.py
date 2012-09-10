import dmagmin_ as GMIN
from pygmin.utils import rotations
from pygmin import takestep
from pygmin.optimize import quench
import crystals
import lattice
import numpy as np
from rbtools import CoordsAdapter
from pygmin.application import AppClusterBH
from pygmin.application.basinhopping_app import AppBasinHopping
from pygmin.potentials.coldfusioncheck import addColdFusionCheck
from pygmin.potentials.gminpotential import GMINPotential 
 
# compare 2 minima
def compareMinima(min1, min2):
    from pygmin.utils import rbtools
    ca1 = rbtools.CoordsAdapter(nrigid=GMIN.getNRigidBody(), nlattice=6, coords=min1.coords)
    ca2 = rbtools.CoordsAdapter(nrigid=GMIN.getNRigidBody(), nlattice=6, coords=min2.coords)
    match = crystals.compareStructures(ca1, ca2)
    return match

# generate a random crystal structure
class GenRandomCrystal(takestep.TakestepInterface):
    ''' takestep class to generate a random crystal
    
        GenRandomCrystal is a takestep class which generates a random crystal structure.
        It can be either used as a standard takestep routine to perform a random search
        or as a reseeding routine in combination with pygmin.takestep.group.Reseeding
    '''
    
    def __init__(self, coordsadapter, volume=None, shear=2., expand=4.0, expand_current=1.2, overlap=None):
        '''
        :param volume: volume bounds of the generated cell [min, max]. None to use 2* current volume
        :param shear: maximum off diagonal matrix element for lattice matrix
        :param expane: maxumum assymmetry of the cell, 0 means generate a cubic cell
        
        ''' 
        
        self.volume = volume
        self.shear = shear
        self.expand = expand
        self.coordsadapter = coordsadapter
        self.expand_current = expand_current
        self.overlap = overlap
        
    def takeStep(self, coords, **kwargs):
        ''' takeStep routine to generate random cell '''        
        ca = self.coordsadapter        
        ca.updateCoords(coords)
        
        atomistic = np.zeros(3*GMIN.getNAtoms())
        valid_configuration = False
        for i in xrange(50):
            volumeTarget = self.expand_current*lattice.volume(ca.lattice)
             
            # random box
            ca.lattice[[0,3,5]] = 1.0 + self.expand * np.random.random(3)  
            ca.lattice[[1,2,4]] = self.shear * np.random.random(3)
            
            if(self.volume != None):
                volumeTarget = self.volume[0] + (self.volume[1] - self.volume[0]) * np.random.random()
                        
            vol = lattice.volume(ca.lattice)
            ca.lattice[:] = ca.lattice * (volumeTarget / vol)**(1.0/3.0)
            GMIN.reduceCell(coords)
            
            for i in xrange(50):# first choose random positions and rotations
                for i in xrange(GMIN.getNRigidBody()):
                    ca.posRigid[i] = np.random.random()
                    ca.rotRigid[i] = rotations.random_aa()
        
                if self.overlap is None:
                    return
            
            
                GMIN.toAtomistic(atomistic, coords)
                if not crystals.has_overlap(atomistic, self.overlap):
                    return
                            
            print "Could generate valid configuration for current box, choose new box"
        raise Exception("GenRandomCrystal: failed to generate a non-overlapping configuration")
            
# special quencher for crystals
def quenchCrystal(coords, pot, **kwargs):
    ''' Special quench routine for crystals which makes sure that the final structure is a reduced cell '''
    coords, E, rms, calls = quench.lbfgs_py(coords, pot, **kwargs)
    #while(GMIN.reduceCell(coords)):
    if(GMIN.reduceCell(coords)):
        #print "Reduced cell, redo minimization"
        coords, E, rms, callsn = quench.lbfgs_py(coords, pot, **kwargs)
        calls+=callsn
    return coords, E, rms, calls

class TakestepDMAGMIN(takestep.TakestepInterface):
    def __init__(self, expand=1.0, rotate=1.6, translate=0., nmols=None, overlap_cutoff=None):
        self.expand = expand
        self.rotate = rotate
        self.translate = translate
        self.nmols=nmols
        self.overlap_cutoff = overlap_cutoff
        
    def takeStep(self, coords, **kwargs):
        from pygmin.takestep import buildingblocks as bb
        ca = CoordsAdapter(nrigid=GMIN.getNRigidBody(), nlattice=6, coords=coords)
        
        conf_ok = False
        
        while not conf_ok:        
            indices=None
            if(self.nmols):
                indices=[]
                indices = [np.random.randint(0,GMIN.getNRigidBody()) for i in xrange(self.nmols)]
            
            if(self.rotate != 0.):
                bb.rotate(self.rotate, ca.rotRigid, indices)
            if(self.translate != 0.):
                bb.uniform_displace(self.translate, ca.rotRigid, indices)
                
            #from pygmin.utils import lattice
            #bb.reduced_coordinates_displace(0.0, lattice.lowerTriangular(ca.lattice), ca.posRigid)
            ca.lattice*=1.2
            
            conf_ok = True
            print "overlap", self.overlap_cutoff
            if(self.overlap_cutoff):
                atomistic = np.zeros(3*GMIN.getNAtoms())
                GMIN.toAtomistic(atomistic, coords)                
                conf_ok = not crystals.has_overlap(coords, self.overlap_cutoff)                
              

class AppDMAGMINBH(AppClusterBH):
    overlap_cutoff = None
    displace_nmols = None
    genrandom_volume = None
    
    def __init__(self):       
        AppClusterBH.__init__(self)
        self.quenchParameters={}
        quenchParameters=self.quenchParameters
        quenchParameters["tol"]=1e-4
        quenchParameters["nsteps"]=5000
        quenchParameters["maxErise"]=2e-2
        quenchParameters["maxstep"]=0.1
        quenchParameters["M"]=100
        
        self.quenchRoutine=quenchCrystal
    
    def initial_coords(self):
        return self.create_potential().getCoords()
        
    def create_potential(self):
        return GMINPotential(GMIN)
    
    def create_takestep_step(self):
        return TakestepDMAGMIN(overlap_cutoff = self.overlap_cutoff, nmols=self.displace_nmols)

    def create_takestep_reseed(self):
        return GenRandomCrystal(CoordsAdapter(nrigid=GMIN.getNRigidBody(), nlattice=6, coords=None),
                                volume=self.genrandom_volume,
                                overlap = self.overlap_cutoff)
    
    def create_basinhopping(self):
        GMIN.initialize()    
        opt = AppClusterBH.create_basinhopping(self)
        self.database.compareMinima = compareMinima
        opt.insert_rejected = True
        addColdFusionCheck(opt)
        return opt
    
    def add_options(self):
        AppClusterBH.add_options(self)
