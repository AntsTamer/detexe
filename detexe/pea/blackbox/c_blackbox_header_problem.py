import struct
from copy import deepcopy

import numpy as np
from secml.array import CArray

from detexe.pea.model.c_wrapper_phi import CWrapperPhi

from .c_blackbox_problem import CBlackBoxProblem


class CBlackBoxHeaderEvasionProblem(CBlackBoxProblem):
    """
    Blackbox attacks that perturbs the DOS header (partially or fully)
    """

    def __init__(
        self,
        model_wrapper: CWrapperPhi,
        population_size: int,
        optimize_all_dos: bool = False,
        iterations: int = 100,
        is_debug: bool = False,
        penalty_regularizer: float = 0,
        invalid_value: int = 256,
    ):
        """
        Creates the attack.

        Parameters
        ----------
        model_wrapper : CWrapperPhi
                the target models, wrapped inside a CWrapperPhi
        population_size : int
                the population size generated at each round by the genetic algorithm
        optimize_all_dos : bool
                if True, it manipulates all the DOS header. False to only manipulate only the first 58 bytes
        iterations : int, optional, default 100
                the total number of iterations, default 100
        is_debug : bool, optional, default False
                if True, it prints messages while optimizing. Default is False
        penalty_regularizer : float, optional, default 0
                the penalty regularizer for the file size constraint. Default is 0
        invalid_value : int, optional, default 256
                specifies which is the invalid value used as separator. Default is 256
        """
        super(CBlackBoxHeaderEvasionProblem, self).__init__(
            model_wrapper,
            latent_space_size=58,
            iterations=iterations,
            population_size=population_size,
            is_debug=is_debug,
            penalty_regularizer=penalty_regularizer,
        )
        self.optimize_all_dos = optimize_all_dos
        self.invalid_value = invalid_value
        self.indexes_to_perturb = list(range(2, 60))

    def init_starting_point(self, x: CArray) -> CArray:
        """
        Initialize the problem, by setting the starting point.

        Parameters
        ----------
        x : CArray
                the initial point

        Returns
        -------
        CArray
                the initial point (padded accordingly to remove trailing invalid values)
        """
        self.indexes_to_perturb = list(range(2, 60))
        if self.optimize_all_dos:
            pe_index = struct.unpack("<I", bytes(x[0, 60:64].tolist()[0]))[0]
            self.indexes_to_perturb += list(range(64, pe_index))
        self.latent_space_size = len(self.indexes_to_perturb)
        return super(CBlackBoxHeaderEvasionProblem, self).init_starting_point(x)

    def apply_feasible_manipulations(self, t: np.ndarray, x: CArray) -> CArray:
        """
        Apply the partial / full DOS practical manipulation

        Parameters
        ----------
        t : numpy array
                the vector of manipulations in [0,1]
        x : CArray
                the input space sample to perturb

        Returns
        -------
        CArray:
                the adversarial malware
        """
        byte_values = (t * 255).astype(np.int)
        x_adv = deepcopy(x)
        for i, index in enumerate(self.indexes_to_perturb):
            x_adv[0, index] = byte_values[i]
        return CArray(x_adv)
