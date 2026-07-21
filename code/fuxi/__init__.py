"""A computational formalization of the Fuxi Earlier Heaven hexagram system.

Modules
-------
encoding      bottom-up bit encoding, the doubling method, Boolean lattice
automaton     changing lines as XOR; the DFA and its group structure
yarrow        the da yan shi fa divination procedure as a probability model
markov        the two competing transition kernels and their spectra
topology      hypercube metrics of the state-transition graph
information   entropy and mutual information
genetic       the binary structure of the 64-codon genetic code
"""

__version__ = "1.0.0"

from . import automaton, encoding, genetic, information, markov, topology, yarrow

__all__ = [
    "encoding",
    "automaton",
    "yarrow",
    "markov",
    "topology",
    "information",
    "genetic",
]
