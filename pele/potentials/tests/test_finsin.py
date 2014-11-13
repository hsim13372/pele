import unittest
import numpy as np

from pele.potentials._fin_sin import FinSin

import _base_test


_x = np.array([-3.1087118812, 2.0914934169, -7.6825567576,
               -1.9765871358, 3.5382030176, -5.6461789915,
               -0.6208417634, 1.4214260282, -6.7428644722,
               -2.7688176114, 1.0768082863, -5.3038691133,
               -0.6117758995, 1.7963343075, -4.0260886340,
               -2.4289231791, 0.0621232184, -2.9251814309,
               -0.9004007963, -0.7269093509, -5.0611955579,
               -4.6372342882, 2.8805261001, -5.5465425942,
               -3.0940429240, 2.6981077448, -3.2867211449,
               -3.5610479356, -1.3845864295, -4.9615591735,
               -2.4435920592, -0.5444911052, -7.3210170309,
               -4.9167933218, 0.7321906313, -3.8648735710,
               -4.9258592162, 0.3572823833, -6.5816495352])


class TestFinSin(_base_test._TestConfiguration):
    def setUp(self):
        self.pot = FinSin()
        self.x0 = _x.copy()
        self.e0 = -67.3508424130


if __name__ == "__main__":
    unittest.main()
