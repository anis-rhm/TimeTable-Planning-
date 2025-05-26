from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import logging
from datetime import datetime
from core.genetic_algorithm import GeneticAlgorithm
from core.timetable_generator import TimetableGenerator
from core.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('timetable_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

def validate_ga_parameters(generations, population_size):
    """Validate genetic algorithm parameters"""
    errors = []
    
    if not isinstance(generations, int) or generations < 1:
        errors.append("Generations must be a positive integer")
    elif generations > 1000:
        errors.append("Generations cannot exceed 1000 for performance reasons")
    
    if not isinstance(population_size, int) or population_size < 10:
        errors.append("Population size must be at least 10")
    elif population_size > 500:
        errors.append("Population size cannot exceed 500 for performance reasons")
    
    return errors

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {str(error)}")
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(413)
def too_large(error):
    """Handle request too large errors"""
    return jsonify({'success': False, 'error': 'Request too large'}), 413

@app.route('/')
def index():
    """Main page with timetable generation interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return render_template('error.html', error="Unable to load main page"), 500

@app.route('/generate', methods=['POST'])
def generate_timetable():
    """Generate timetable using genetic algorithm"""
    start_time = datetime.now()
    logger.info("Starting timetable generation via web form")
    
    try:
        # Get and validate parameters from form
        try:
            generations = int(request.form.get('generations', 200))
            population_size = int(request.form.get('population_size', 150))
        except (ValueError, TypeError):
            return render_template('error.html', error="Invalid parameters. Please provide valid numbers.")
        
        # Validate parameters
        validation_errors = validate_ga_parameters(generations, population_size)
        if validation_errors:
            error_msg = "Validation errors: " + "; ".join(validation_errors)
            return render_template('error.html', error=error_msg)
        
        logger.info(f"Parameters: generations={generations}, population_size={population_size}")
        
        # Initialize genetic algorithm
        ga = GeneticAlgorithm(
            generations=generations,
            population_size=population_size
        )
        
        # Run genetic algorithm
        best_solution, best_score = ga.run()
        
        if best_solution is None:
            raise ValueError("Genetic algorithm failed to find a solution")
        
        # Generate formatted timetable
        generator = TimetableGenerator()
        formatted_timetable = generator.format_solution(best_solution)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Timetable generated successfully in {execution_time:.2f} seconds with score {best_score}")
        
        return render_template('result.html', 
                             timetable=formatted_timetable,
                             score=best_score,
                             generations=generations,
                             population_size=population_size,
                             execution_time=execution_time)
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Error in timetable generation: {str(e)} (took {execution_time:.2f}s)")
        return render_template('error.html', error=f"Generation failed: {str(e)}")

@app.route('/api/generate', methods=['POST'])
def api_generate_timetable():
    """API endpoint for generating timetable"""
    start_time = datetime.now()
    logger.info("Starting timetable generation via API")
    
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Get and validate parameters
        try:
            generations = int(data.get('generations', 200))
            population_size = int(data.get('population_size', 150))
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid parameters. Generations and population_size must be integers.'
            }), 400
        
        # Validate parameters
        validation_errors = validate_ga_parameters(generations, population_size)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation errors: ' + '; '.join(validation_errors)
            }), 400
        
        logger.info(f"API Parameters: generations={generations}, population_size={population_size}")
        
        ga = GeneticAlgorithm(
            generations=generations,
            population_size=population_size
        )
        
        best_solution, best_score = ga.run()
        
        if best_solution is None:
            raise ValueError("Genetic algorithm failed to find a solution")
        
        generator = TimetableGenerator()
        formatted_timetable = generator.format_solution(best_solution)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"API timetable generated successfully in {execution_time:.2f} seconds with score {best_score}")
        
        return jsonify({
            'success': True,
            'timetable': formatted_timetable,
            'score': best_score,
            'execution_time': execution_time,
            'parameters': {
                'generations': generations,
                'population_size': population_size
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"API Error in timetable generation: {str(e)} (took {execution_time:.2f}s)")
        return jsonify({
            'success': False,
            'error': str(e),
            'execution_time': execution_time
        }), 500

@app.route('/config')
def config():
    """Configuration page"""
    try:
        config_data = {
            'days': Config.DAYS,
            'slots': Config.SLOTS,
            'rooms': Config.ROOMS,
            'topics': Config.TOPICS,
            'session_types': Config.SESSION_TYPES,
            'teachers': Config.TOPIC_TEACHERS,
            'total_sessions': len(Config.ALL_SESSIONS),
            'total_attendees': Config.TOTAL_ATTENDEES
        }
        return render_template('config.html', config=config_data)
    except Exception as e:
        logger.error(f"Error loading configuration page: {str(e)}")
        return render_template('error.html', error="Unable to load configuration"), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    logger.info("Starting timetable application")
    app.run(debug=True, host='0.0.0.0', port=5000)