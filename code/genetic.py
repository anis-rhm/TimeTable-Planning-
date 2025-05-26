import copy
import random
from code.fitness import fitness
from code.utilities import random_slot, ALL_SESSIONS, ROOM_LIST, N_INSTANCES_PER_SESSION, random_teacher_for_topic
from code.initialization import initialize_chromosome

def crossover(parent1, parent2):
    """Perform uniform crossover on two parents to produce a child chromosome."""
    child = {}
    for key in ALL_SESSIONS:
        # Randomly choose sessions from either parent1 or parent2
        if random.random() < 0.5:
            child[key] = copy.deepcopy(parent1.get(key, []))
        else:
            child[key] = copy.deepcopy(parent2.get(key, []))
    
    # Introduce a small probability to inject new random sessions for diversity
    if random.random() < 0.2:
        random_key = random.choice(ALL_SESSIONS)
        day, slot = random_slot()
        rooms = ROOM_LIST[:]
        random.shuffle(rooms)
        chosen_rooms = rooms[:N_INSTANCES_PER_SESSION]
        child[random_key] = [
            (day, slot, chosen_rooms[i], random_teacher_for_topic(random_key[0]))
            for i in range(N_INSTANCES_PER_SESSION)
        ]
    
    return child





def mutation(chromosome, mutation_rate=0.05):
    """Apply mutation by randomly changing assignments for some sessions."""
    for key in ALL_SESSIONS:
        if random.random() < mutation_rate:
            # Choose between partial mutation or full reassignment
            if random.random() < 0.5:
                # Partial mutation: Change only one session
                if chromosome[key]:
                    idx = random.randint(0, len(chromosome[key]) - 1)
                    day, slot = random_slot()
                    room = random.choice(ROOM_LIST)
                    teacher = random_teacher_for_topic(key[0])
                    chromosome[key][idx] = (day, slot, room, teacher)
            else:
                # Full reassignment
                day, slot = random_slot()
                rooms = ROOM_LIST[:]
                random.shuffle(rooms)
                chosen_rooms = rooms[:N_INSTANCES_PER_SESSION]
                new_assignments = [
                    (day, slot, chosen_rooms[i], random_teacher_for_topic(key[0]))
                    for i in range(N_INSTANCES_PER_SESSION)
                ]
                chromosome[key] = new_assignments
    return chromosome



def selection(population, scores):
    """Select parents based on their fitness scores (tournament selection)."""
    selected = []
    pop_size = len(population)
    for _ in range(pop_size):
        a = random.randint(0, pop_size-1)
        b = random.randint(0, pop_size-1)
        if scores[a] < scores[b]:
            selected.append(copy.deepcopy(population[a]))
        else:
            selected.append(copy.deepcopy(population[b]))
    
    return selected


def print_chromosomes(population):
    """Print the chromosomes in the population for inspection."""
    print("\nInitial Chromosomes (Before GA Begins):")
    for i, chromosome in enumerate(population):
        print(f"\nChromosome {i+1}:")
        for key, sessions in chromosome.items():
            print(f"  {key}: {sessions}")
    print("=" * 50)


def run_ga(generations=200, population_size=50, print_initial_chromosomes=False):
    """Run the genetic algorithm for a specified number of generations."""
    # Initialize population
    population = [initialize_chromosome() for _ in range(population_size)]

    # Print the initial population if the parameter is True
    if print_initial_chromosomes:
        print_chromosomes(population)

    best = None
    best_score = float('inf')
    previous_best = None  # To track if the chromosome has changed

    for gen in range(generations):
        scores = [fitness(ind) for ind in population]
        current_best_score = min(scores)
        best_individual = population[scores.index(current_best_score)]
        
        # Check if the best individual has changed from the previous generation
        if current_best_score < best_score:
            best_score = current_best_score
            best = copy.deepcopy(best_individual)
            has_changed = True
        else:
            has_changed = False

        # Print the best score and whether the chromosome has changed
        print(f"Gen {gen} Best Score: {best_score}")
        if has_changed:
            print("Best chromosome has changed in this generation.")
        else:
            print("Best chromosome has NOT changed in this generation.")

        # If the best score is 0 (optimal solution found), break early
        if best_score == 0:
            print("Optimal solution found!")
            break

        # Selection, crossover, and mutation for the next generation
        population = selection(population, scores)

        next_pop = []
        for i in range(0, population_size, 2):
            p1 = population[i]
            p2 = population[(i+1) % population_size]
            child1 = crossover(p1, p2)
            child2 = crossover(p2, p1)
            next_pop.append(child1)
            next_pop.append(child2)

        population = [mutation(ind) for ind in next_pop]

    return best, best_score
