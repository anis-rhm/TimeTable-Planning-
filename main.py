#!/usr/bin/env python3
"""
Command-line interface for the University Timetable Generator

This script provides a simple command-line interface to generate timetables
using the genetic algorithm without the web interface.
"""

from core.genetic_algorithm import GeneticAlgorithm
from core.timetable_generator import TimetableGenerator

def main():
    """Main function to run the timetable generation"""
    print("=" * 60)
    print("University Timetable Generator - Command Line Interface")
    print("=" * 60)
    
    # Initialize the genetic algorithm with default parameters
    print("Initializing genetic algorithm...")
    ga = GeneticAlgorithm(
        generations=200, 
        population_size=150
    )
    
    # Run the genetic algorithm
    print("Running optimization...")
    best_solution, best_score = ga.run()
    
    # Display the results
    print(f"\nOptimization completed!")
    print(f"Final fitness score: {best_score}")
    
    # Generate and print the formatted timetable
    generator = TimetableGenerator()
    generator.print_solution(best_solution, best_score)
    
    print("\nFor a better experience, try the web interface:")
    print("python app.py")
    print("Then open http://localhost:5000 in your browser")

if __name__ == "__main__":
    main()
