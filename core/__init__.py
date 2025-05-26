"""
Core modules for the University Timetable Generator

This package contains the core functionality for generating optimal university
timetables using genetic algorithms.

Modules:
    - config: Configuration settings and constants
    - genetic_algorithm: Main genetic algorithm implementation
    - fitness: Fitness evaluation functions
    - chromosome: Chromosome initialization and management
    - timetable_generator: Timetable formatting and display utilities
"""

from .config import Config
from .genetic_algorithm import GeneticAlgorithm
from .fitness import FitnessEvaluator
from .chromosome import ChromosomeInitializer
from .timetable_generator import TimetableGenerator

__all__ = [
    'Config',
    'GeneticAlgorithm', 
    'FitnessEvaluator',
    'ChromosomeInitializer',
    'TimetableGenerator'
]

__version__ = "1.0.0"
__author__ = "DataXplorers Team"