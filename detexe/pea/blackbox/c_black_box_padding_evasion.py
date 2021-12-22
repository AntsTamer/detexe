import numpy as np
from secml.array import CArray

from detexe.pea.model.c_wrapper_phi import CWrapperPhi

from .c_blackbox_problem import CBlackBoxProblem


class CBlackBoxPaddingEvasionProblem(CBlackBoxProblem):
    """
    Padding black-box problem
    """

    def __init__(
        self,
        model_wrapper: CWrapperPhi,
        population_size: int,
        how_many_padding_bytes: int,
        iterations: int = 100,
        is_debug: bool = False,
        penalty_regularizer: float = 0,
        invalid_value: int = 256,
    ):
        """
        Creates the Padding attack problem for the black-box engine.

        Parameters
        ----------
        model_wrapper : CWrapperPhi
                the target models, wrapped inside a CWrapperPhi
        population_size : int
                the population size generated at each round by the genetic algorithm
        how_many_padding_bytes : int
                the number of padding bytes to append
        iterations : int, optional, default 100
                the total number of iterations, default 100
        is_debug : bool, optional, default False
                if True, it prints messages while optimizing. Default is False
        penalty_regularizer : float, optional, default 0
                the penalty regularizer for the file size constraint. Default is 0
        invalid_value : int, optional, default 256
                specifies which is the invalid value used as separator. Default is 256
        """
        super(CBlackBoxPaddingEvasionProblem, self).__init__(
            model_wrapper,
            latent_space_size=how_many_padding_bytes,
            iterations=iterations,
            population_size=population_size,
            is_debug=is_debug,
            penalty_regularizer=penalty_regularizer,
        )

        self.invalid_value = invalid_value
        self.indexes_to_perturb = list(range(how_many_padding_bytes))

    def apply_feasible_manipulations(self, t, x: CArray) -> CArray:
        """
        Apply the padding practical manipulation on the input sample
        Parameters
        ----------
        t : CArray
                the vector of manipulations in [0,1]
        x : CArray
                the input space sample to perturb

        Returns
        -------
        CArray:
                the adversarial malware
        """
        byte_values = (t * 255).astype(np.int)
        x_adv = x.append(byte_values)
        return x_adv
