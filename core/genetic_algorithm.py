import copy
import random
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from .config import Config
from .fitness import FitnessEvaluator
from .chromosome import ChromosomeInitializer

logger = logging.getLogger(__name__)

class GeneticAlgorithm:
    """Enhanced Genetic Algorithm implementation for timetable optimization"""
    
    def __init__(self, generations=200, population_size=150, mutation_rate=0.05, 
                 crossover_rate=0.8, elitism_rate=0.1, max_stagnation=50):
        self.generations = generations
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_count = max(1, int(population_size * elitism_rate))
        self.max_stagnation = max_stagnation
        
        self.fitness_evaluator = FitnessEvaluator()
        self.initializer = ChromosomeInitializer()
        
        # Performance tracking
        self.best_scores_history = []
        self.generation_times = []
        self.diversity_history = []
        
        # Thread safety
        self.lock = threading.Lock()
    
    def calculate_diversity(self, population):
        """Calculate population diversity to prevent premature convergence"""
        if len(population) < 2:
            return 0.0
        
        diversity_sum = 0
        comparisons = 0
        
        for i in range(min(len(population), 20)):  # Sample for performance
            for j in range(i + 1, min(len(population), 20)):
                diff_count = 0
                total_genes = 0
                
                for key in Config.ALL_SESSIONS:
                    if key in population[i] and key in population[j]:
                        sessions_i = population[i][key]
                        sessions_j = population[j][key]
                        
                        for idx in range(min(len(sessions_i), len(sessions_j))):
                            total_genes += 1
                            if sessions_i[idx] != sessions_j[idx]:
                                diff_count += 1
                
                if total_genes > 0:
                    diversity_sum += diff_count / total_genes
                    comparisons += 1
        
        return diversity_sum / comparisons if comparisons > 0 else 0.0

    def crossover(self, parent1, parent2):
        """Enhanced crossover with adaptive probability"""
        if random.random() > self.crossover_rate:
            return copy.deepcopy(parent1)
        
        child = {}
        
        # Two-point crossover for better genetic mixing
        crossover_points = sorted(random.sample(range(len(Config.ALL_SESSIONS)), 2))
        sessions_list = list(Config.ALL_SESSIONS)
        
        for i, key in enumerate(sessions_list):
            if crossover_points[0] <= i < crossover_points[1]:
                child[key] = copy.deepcopy(parent2.get(key, []))
            else:
                child[key] = copy.deepcopy(parent1.get(key, []))
        
        # Repair conflicts after crossover
        child = self._repair_conflicts(child)
        
        return child

    def _repair_conflicts(self, chromosome):
        """Repair room and teacher conflicts in chromosome"""
        time_room_assignments = {}
        time_teacher_assignments = {}
        
        for (topic, stype), sessions in chromosome.items():
            new_sessions = []
            for (d, s, r, teacher) in sessions:
                # Check and resolve room conflicts
                time_key = (d, s)
                if time_key in time_room_assignments and r in time_room_assignments[time_key]:
                    # Find alternative room
                    available_rooms = [room for room in Config.ROOM_LIST 
                                     if room not in time_room_assignments.get(time_key, set())]
                    if available_rooms:
                        r = random.choice(available_rooms)
                    else:
                        # Find alternative time slot
                        d, s = Config.random_slot()
                        time_key = (d, s)
                
                # Check and resolve teacher conflicts
                if time_key in time_teacher_assignments and teacher in time_teacher_assignments[time_key]:
                    # Assign different teacher for this topic
                    teacher = Config.random_teacher_for_topic(topic)
                
                # Record assignments
                if time_key not in time_room_assignments:
                    time_room_assignments[time_key] = set()
                if time_key not in time_teacher_assignments:
                    time_teacher_assignments[time_key] = set()
                
                time_room_assignments[time_key].add(r)
                time_teacher_assignments[time_key].add(teacher)
                
                new_sessions.append((d, s, r, teacher))
            
            chromosome[(topic, stype)] = new_sessions
        
        return chromosome

    def adaptive_mutation(self, chromosome, generation, diversity):
        """Apply adaptive mutation based on generation and diversity"""
        # Increase mutation rate if diversity is low
        adaptive_rate = self.mutation_rate
        if diversity < 0.3:
            adaptive_rate *= 2
        elif diversity > 0.7:
            adaptive_rate *= 0.5
        
        # Increase mutation rate in later generations if stagnating
        if generation > self.generations * 0.7:
            adaptive_rate *= 1.5
        
        for key in Config.ALL_SESSIONS:
            if random.random() < adaptive_rate:
                mutation_type = random.choice(['time', 'room', 'teacher', 'full'])
                
                if mutation_type == 'time' and chromosome[key]:
                    # Mutate time slot only
                    idx = random.randint(0, len(chromosome[key]) - 1)
                    d, s, r, t = chromosome[key][idx]
                    d, s = Config.random_slot()
                    chromosome[key][idx] = (d, s, r, t)
                
                elif mutation_type == 'room' and chromosome[key]:
                    # Mutate room only
                    idx = random.randint(0, len(chromosome[key]) - 1)
                    d, s, r, t = chromosome[key][idx]
                    r = random.choice(Config.ROOM_LIST)
                    chromosome[key][idx] = (d, s, r, t)
                
                elif mutation_type == 'teacher' and chromosome[key]:
                    # Mutate teacher only
                    idx = random.randint(0, len(chromosome[key]) - 1)
                    d, s, r, t = chromosome[key][idx]
                    t = Config.random_teacher_for_topic(key[0])
                    chromosome[key][idx] = (d, s, r, t)
                
                else:
                    # Full reassignment
                    day, slot = Config.random_slot()
                    rooms = Config.ROOM_LIST[:]
                    random.shuffle(rooms)
                    chosen_rooms = rooms[:Config.N_INSTANCES_PER_SESSION]
                    new_assignments = [
                        (day, slot, chosen_rooms[i], Config.random_teacher_for_topic(key[0]))
                        for i in range(Config.N_INSTANCES_PER_SESSION)
                    ]
                    chromosome[key] = new_assignments
        
        return chromosome

    def tournament_selection(self, population, scores, tournament_size=3):
        """Tournament selection with configurable tournament size"""
        selected = []
        pop_size = len(population)
        
        for _ in range(pop_size):
            tournament_indices = random.sample(range(pop_size), 
                                             min(tournament_size, pop_size))
            best_idx = min(tournament_indices, key=lambda i: scores[i])
            selected.append(copy.deepcopy(population[best_idx]))
        
        return selected

    def evaluate_population_parallel(self, population):
        """Evaluate population fitness in parallel for better performance"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            scores = list(executor.map(self.fitness_evaluator.fitness, population))
        return scores

    def run(self):
        """Run the enhanced genetic algorithm with convergence detection"""
        logger.info(f"Starting enhanced GA with {self.generations} generations, "
                   f"population size {self.population_size}")
        
        # Initialize population with diversity
        population = []
        max_attempts = self.population_size * 2
        
        for _ in range(max_attempts):
            if len(population) >= self.population_size:
                break
            
            candidate = self.initializer.initialize_chromosome()
            # Ensure some diversity in initial population
            if not population or self._is_sufficiently_different(candidate, population):
                population.append(candidate)
        
        # Fill remaining slots if needed
        while len(population) < self.population_size:
            population.append(self.initializer.initialize_chromosome())
        
        best = None
        best_score = float('inf')
        stagnation_counter = 0
        
        for gen in range(self.generations):
            # Evaluate fitness
            scores = self.evaluate_population_parallel(population)
            current_best_score = min(scores)
            current_best_idx = scores.index(current_best_score)
            current_best = population[current_best_idx]
            
            # Calculate diversity
            diversity = self.calculate_diversity(population)
            self.diversity_history.append(diversity)
            
            # Track best solution
            if current_best_score < best_score:
                best_score = current_best_score
                best = copy.deepcopy(current_best)
                stagnation_counter = 0
                logger.info(f"Generation {gen}: New best score = {best_score:.2f}, "
                           f"diversity = {diversity:.3f}")
            else:
                stagnation_counter += 1
            
            self.best_scores_history.append(best_score)
            
            # Early termination conditions
            if best_score == 0:
                logger.info("Optimal solution found!")
                break
            
            if stagnation_counter >= self.max_stagnation:
                logger.info(f"Terminating due to stagnation after {stagnation_counter} generations")
                break
            
            # Selection with elitism
            sorted_indices = sorted(range(len(population)), key=lambda i: scores[i])
            
            # Keep best individuals (elitism)
            elite = [copy.deepcopy(population[i]) for i in sorted_indices[:self.elitism_count]]
            
            # Tournament selection for the rest
            selected = self.tournament_selection(population, scores)
            
            # Crossover and mutation
            next_pop = elite[:]
            
            while len(next_pop) < self.population_size:
                p1 = random.choice(selected)
                p2 = random.choice(selected)
                
                child1 = self.crossover(p1, p2)
                child1 = self.adaptive_mutation(child1, gen, diversity)
                next_pop.append(child1)
                
                if len(next_pop) < self.population_size:
                    child2 = self.crossover(p2, p1)
                    child2 = self.adaptive_mutation(child2, gen, diversity)
                    next_pop.append(child2)
            
            population = next_pop[:self.population_size]
            
            # Log progress every 20 generations
            if gen % 20 == 0:
                logger.info(f"Generation {gen}: Best = {best_score:.2f}, "
                           f"Current = {current_best_score:.2f}, "
                           f"Diversity = {diversity:.3f}")
        
        logger.info(f"GA completed. Final best score: {best_score}, "
                   f"Total generations: {gen + 1}")
        
        return best, best_score

    def _is_sufficiently_different(self, candidate, population, threshold=0.3):
        """Check if candidate is sufficiently different from existing population"""
        if not population:
            return True
        
        for individual in population[-5:]:  # Check against last 5 individuals
            similarity = self._calculate_similarity(candidate, individual)
            if similarity > (1 - threshold):
                return False
        return True

    def _calculate_similarity(self, ind1, ind2):
        """Calculate similarity between two individuals"""
        total_genes = 0
        same_genes = 0
        
        for key in Config.ALL_SESSIONS:
            if key in ind1 and key in ind2:
                sessions1 = ind1[key]
                sessions2 = ind2[key]
                
                for i in range(min(len(sessions1), len(sessions2))):
                    total_genes += 1
                    if sessions1[i] == sessions2[i]:
                        same_genes += 1
        
        return same_genes / total_genes if total_genes > 0 else 0.0