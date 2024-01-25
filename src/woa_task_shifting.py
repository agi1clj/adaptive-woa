import numpy as np
from mealpy import PermutationVar, WOA, Problem
import json

def objective_min_energy_consumption(problem, tasks):
    """
    Objective 1: Minimize energy consumption.

    This objective aims to minimize the total energy consumption of the selected tasks.

    Parameters:
        problem (TaskShiftingProblem): The optimization problem instance.
        tasks (list): List of task indices representing the assignment order.

    Returns:
        float: Total energy consumption for the selected tasks.
    """
    energy_consumption = sum(problem.data["nodes"][task]["energy_consumption"] for task in tasks)
    return energy_consumption


def objective_min_latency(problem, tasks):
    """
    Objective: Minimize total latency.

    This objective aims to find the optimal deployment location based on minimizing the total latency of the selected tasks.

    Parameters:
        problem (TaskShiftingProblem): The optimization problem instance.
        tasks (list): List of task indices representing the assignment order.

    Returns:
        float: Optimal deployment location based on minimizing latency.
    """
    latencies = [problem.data["nodes"][task]["latency"] for task in tasks]
    total_latency = sum(latencies)
    optimal_location = total_latency / len(tasks)  # Simple example, can be more complex
    print(optimal_location)
    return optimal_location

def objective_find_deployment_location_data_volume(problem, tasks):
    """
    Objective: Find optimal deployment location based on data volume.

    This objective aims to find the optimal deployment location based on the total data volume of the selected tasks.

    Parameters:
        problem (TaskShiftingProblem): The optimization problem instance.
        tasks (list): List of task indices representing the assignment order.

    Returns:
        float: Optimal deployment location based on data volume.
    """
    data_volumes = [problem.data["nodes"][task]["data_volume"] for task in tasks]
    total_data_volume = sum(data_volumes)
    optimal_location = total_data_volume / len(tasks)  # Simple example, can be more complex
    print(optimal_location)

    return optimal_location

class TaskShiftingProblem(Problem):
    def __init__(self, bounds=None, minmax="min", data=None, objectives=None, weights=None, **kwargs):
        """
        Task Shifting Multi-objective Optimization Problem.

        Parameters:
            bounds (PermutationVar): Permutation bounds for the task assignment order.
            minmax (str): "min" for minimization problem.
            data (dict): Problem data containing node and link information.
            objectives (list): List of objective functions to be minimized.
            weights (list): List of weights corresponding to each objective function.
            **kwargs: Additional keyword arguments for the superclass constructor.
        """
        self.data = data
        self.objectives = objectives
        self.weights = weights
        super().__init__(bounds, minmax, **kwargs)

    def obj_func(self, x):
        """
        Multi-objective function to be minimized.

        Parameters:
            x (numpy.ndarray): Decoded solution containing the assignment order of tasks.

        Returns:
            float: Weighted sum of objective function values.
        """
        x_decoded = self.decode_solution(x)
        tasks = x_decoded["per_var"]

        objectives_values = [objective(self, tasks) for objective in self.objectives]
        fitness = np.dot(self.weights, objectives_values)

        return fitness


with open('static/dag_model.json', 'r') as file:
    task_shifting_data = json.load(file)

# Define objectives and their weights
objectives = [objective_min_energy_consumption, objective_min_latency, objective_find_deployment_location_data_volume]
weights = [0.4, 0.1, 0.4]

# Extract necessary information from the loaded data
n_tasks = len(task_shifting_data["nodes"])

'''
The permutation represents a task sequence, 
and the optimization algorithm determines the 
best assignment order to computing nodes (Edge, Fog, Cloud) 
based on defined objectives and constraints.
'''
task_bounds = PermutationVar(valid_set=list(range(n_tasks)), name="per_var")

# Create the TaskShiftingProblem instance
task_shifting_problem = TaskShiftingProblem(bounds=task_bounds, minmax="min", data=task_shifting_data,
                                             objectives=objectives, weights=weights)

# Solve the problem using WOA algorithm
model = WOA.OriginalWOA(epoch=100, pop_size=20)
model.solve(task_shifting_problem)

# Print results
best_solution = task_shifting_problem.decode_solution(model.g_best.solution)
print(f"Best solution: {best_solution}")
print(f"Best fitness: {model.g_best.target.fitness}")
