# University Timetable Generator

An AI-powered web application that generates optimal university timetables using genetic algorithms. This system automatically schedules classes while respecting constraints like room availability, teacher assignments, and time preferences.

## Features

- **Genetic Algorithm Optimization**: Uses evolutionary computation to find optimal timetable solutions
- **Web Interface**: Modern, responsive Flask web application
- **Constraint Handling**: Automatically handles room conflicts, teacher availability, and scheduling preferences
- **Real-time Generation**: Interactive timetable generation with progress feedback
- **Multiple Session Types**: Supports Theory, Practical, History, and Test sessions
- **Flexible Configuration**: Easy to modify rooms, teachers, and scheduling parameters

## Project Structure

```
TimeTable-planning-main_DataXplorers/
├── app.py                 # Flask web application
├── main.py               # Command-line interface
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── core/                # Core algorithm modules
│   ├── __init__.py
│   ├── config.py        # Configuration settings
│   ├── genetic_algorithm.py  # Main GA implementation
│   ├── fitness.py       # Fitness evaluation
│   ├── chromosome.py    # Chromosome initialization
│   └── timetable_generator.py  # Output formatting
├── templates/           # HTML t# Acknowledgments

- Genetic algorithm implementation inspired by evolutionary computation principles
- Web interface built with Bootstrap and modern web standardsemplates
│   ├── index.html       # Main page
│   ├── result.html      # Results display
│   ├── config.html      # Configuration view
│   └── error.html       # Error handling
├── static/             # Static web assets
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── app.js       # JavaScript functionality
└── code/               # Legacy code (kept for reference)
```





## Authors

- DataXplorers Team
- AI Quest 2025
