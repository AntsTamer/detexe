import copy
import os
import pickle

import lief
import magic
import numpy as np
from secml.array import CArray

from detexe.pea.model.c_wrapper_phi import CWrapperPhi

from .c_blackbox_problem import CBlackBoxProblem


class CGammaEvasionProblem(CBlackBoxProblem):
    """
    GAMMA padding attack
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
    ):
        """
        Creates the GAMMA padding attack.

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
        """
        super(CGammaEvasionProblem, self).__init__(
            model_wrapper,
            len(section_population),
            population_size,
            penalty_regularizer,
            iterations,
            seed,
            is_debug,
            hard_label,
            threshold,
            loss,
        )

        self.section_population = section_population
        self.payload_max_size = sum([len(s) for s in section_population])

    def apply_feasible_manipulations(self, t: np.ndarray, x: CArray) -> CArray:
        """
        Applies the padding manipulation.

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
        for i in range(t.shape[-1]):
            content = self.section_population[i]
            content_to_append = content[: int(round(len(content) * t[i]))]
            x_adv = x_adv.append(content_to_append)
        x_adv = x_adv.reshape((1, x_adv.shape[-1]))
        return x_adv

    @classmethod
    def create_section_population_from_list(
        cls, folder: str, what_from_who: list
    ) -> list:
        """
        Create the section population from pe_files contained in a specified folder

        Parameters
        ----------
        folder : str
                the folder containing the file to open
        what_from_who : list
                a list of file (section name, file names) that specifies what extract from who
        Returns
        -------
        list
                the section population list
        """
        section_population = []
        for entry in what_from_who:
            what, who = entry
            path = os.path.join(folder, who)
            lief_pe_file = lief.PE.parse(path)
            for s in lief_pe_file.sections:
                if s.name == what:
                    section_population.append(s.content)
        return section_population

    @classmethod
    def create_section_population_from_folder(
        cls,
        folder: str,
        how_many: int,
        sections_to_extract: list = None,
        cache_file: str = None,
        size_lower_bound: int = None,
    ) -> (list, list):
        """
        Extract sections from a given folder

        Parameters
        ----------
        folder : str
                the folder containing programs used for extracting sections
        how_many : int
                how many sections to extract in general
        sections_to_extract : list, optional, default None
                the list of section names to use. If None, it will extract only .data sections
        cache_file : str, optional, default None
                if set, it stores which section from what program has been used inside a pickled object, stored in path
        size_lower_bound : int, optional, default None
                if set, it will discard all the sections whose content length is less that such parameter

        Returns
        -------
        list, list
                the section population and what has been extracted from who
        """
        if sections_to_extract is None:
            sections_to_extract = [".data"]
        section_population = []
        counter = 0
        what_from_who = []
        if cache_file and os.path.isfile(cache_file):
            with open(cache_file, "rb") as section_file:
                file_to_consider = pickle.load(section_file)
                file_to_consider = [f[1] for f in file_to_consider]
        else:
            file_to_consider = os.listdir(folder)
        for filename in file_to_consider:
            path = os.path.join(folder, filename)
            if "PE" not in magic.from_file(path):
                continue
            lief.logging.set_level(lief.logging.LOGGING_LEVEL(5))
            lief_pe_file = lief.PE.parse(path)
            for s in lief_pe_file.sections:
                if s.name in sections_to_extract:
                    if size_lower_bound and len(s.content) < size_lower_bound:
                        continue
                    if len(s.content) == 0:
                        continue
                    section_population.append(s.content)
                    what_from_who.append((s.name, filename))
                    counter += 1
            if counter >= how_many:
                break
        section_population = section_population[:how_many]
        if cache_file and not os.path.isfile(cache_file):
            with open(cache_file, "wb") as section_file:
                pickle.dump(what_from_who, section_file)
        return section_population, what_from_who
