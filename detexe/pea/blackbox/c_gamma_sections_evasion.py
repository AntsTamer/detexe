import copy
import random
import string

import lief
import numpy as np
from secml.array import CArray

from detexe.pea.model.c_wrapper_phi import CWrapperPhi

from .c_gamma_evasion import CGammaEvasionProblem


class CGammaSectionsEvasionProblem(CGammaEvasionProblem):
    """
    GAMMA section injection attack class
    """

    def __init__(
        self,
        section_population: list,
        model_wrapper: CWrapperPhi,
        population_size: int,
        penalty_regularizer: float,
        iterations: int,
        seed: int = None,
        is_debug: bool = False,
        hard_label: bool = False,
        threshold: float = 0.5,
        loss: str = "l1",
        random_names: bool = True,
    ):
        """
        Creates the GAMMA section injection attack

        Parameters
        ----------
        section_population : list
                a list containing all the goodware sections to inject
        model_wrapper : CWrapperPhi
                the target models, wrapped inside a CWrapperPhi
        population_size : int
                the population size generated at each round by the genetic algorithm
        penalty_regularizer: float
                the regularization parameter used for the size constraint
        iterations : int, optional, default 100
                the total number of iterations, default 100
        seed : int, optional, default None
                specifies an initialization seed for the random. None for not using determinism
        is_debug : bool, optional, default False
                if True, it prints messages while optimizing. Default is False
        hard_label : bool, optional default False
                if True, the problem will use only binary labels instead. Infinity will be used for non-evasive samples.
        threshold : float, optional, default 0
                the detection threshold. Leave 0 to test the degradation of the models until the end of the algorithm.
        loss : str, optional, default l1
                The loss function used as objective function
        random_names: bool
                Uses random names for the new sections. Default True
        """
        super(CGammaSectionsEvasionProblem, self).__init__(
            section_population,
            model_wrapper,
            population_size,
            penalty_regularizer,
            iterations,
            seed,
            is_debug,
            hard_label,
            threshold,
            loss,
        )
        self.random_names = random_names
        self.names_ = []
        self.best_names_ = []

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
        original = super().init_starting_point(x)
        self.best_names_ = []
        self.names_ = []
        return original

    def apply_feasible_manipulations(self, t, x: CArray) -> CArray:
        """
        Applies the section injection manipulation.

        Parameters
        ----------
        t : np.ndarray
                the vector of parameters specifying how much content must be included
        x : CArray
                the original malware

        Returns
        -------
        CArray
                the adversarial malware
        """
        x_adv = copy.deepcopy(x)
        x_adv = x_adv[0, :].flatten().tolist()
        lief_adv: lief.PE.Binary = lief.PE.parse(raw=x_adv)
        names = []
        for i in range(self.latent_space_size):
            content = self.section_population[i]
            content_to_append = content[: int(round(len(content) * t[i]))]
            if self.best_names_ != []:
                section_name = self.best_names_[i]
            else:
                section_name = "".join(
                    random.choice(string.ascii_letters) for _ in range(8)
                )
            names.append(section_name)
            s = lief.PE.Section(section_name)
            s.content = content_to_append
            lief_adv.add_section(s)
        self.names_.append(names)
        builder = lief.PE.Builder(lief_adv)
        builder.build()
        x_adv = CArray(builder.get_build())
        x_adv = x_adv.reshape((1, x_adv.shape[-1]))
        return x_adv

    def _export_internal_results(self, irregular=None):
        confidence, fitness, sizes = super()._export_internal_results(irregular)
        index = int(np.argmin(self.fitness_[1:]))
        self.best_names_ = self.names_[index]
        return confidence, fitness, sizes
