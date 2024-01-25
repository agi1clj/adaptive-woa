import numpy as np
from mealpy import PermutationVar, WOA, Problem
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s, %(levelname)s, %(name)s: %(message)s",
    datefmt="%Y/%m/%d %I:%M:%S %p",
)
logger = logging.getLogger(__name__)


class TaskShiftingProblem(Problem):
    def __init__(self, bounds=None, minmax="min", data=None, name="TaskShifting", **kwargs):
        """
        Task Shifting Multi-objective Optimization Problem.

        Parameters:
            bounds (PermutationVar): Permutation bounds for the task assignment order.
            minmax (str): "min" for minimization problem.
            data (dict): Problem data containing node and link information.
            obj_weights (list): List of weights corresponding to each objective function.
            name (str): Name of the problem.
            **kwargs: Additional keyword arguments for the superclass constructor.
        """
        self.data = data
        super().__init__(bounds, minmax, name=name, **kwargs)

    def objective_min_energy_consumption(self, tasks):
        """
        Objective 1: Minimize energy consumption.

        This objective aims to minimize the total energy consumption of the selected tasks.

        Parameters:
            tasks (list): List of task indices representing the assignment order.

        Returns:
            float: Total energy consumption for the selected tasks.
        """
        tasks_list = tasks.astype(int).tolist()
        energy_consumption = sum(self.data["nodes"][task]["energy_consumption"] for task in tasks_list)
        return energy_consumption

    def objective_min_latency(self, tasks):
        """
        Objective: Minimize total latency.

        This objective aims to find the optimal deployment location based on minimizing the total latency of the selected tasks.

        Parameters:
            tasks (list): List of task indices representing the assignment order.

        Returns:
            float: Optimal deployment location based on minimizing latency.
        """
        tasks_list = tasks.astype(int).tolist()
        latencies = [self.data["nodes"][task]["latency"] for task in tasks_list]
        total_latency = sum(latencies)
        optimal_location = total_latency / len(tasks)  # Simple example, can be more complex
        return optimal_location

    def objective_find_deployment_location_data_volume(self, tasks):
        """
        Objective: Find optimal deployment location based on data volume.

        This objective aims to find the optimal deployment location based on the total data volume of the selected tasks.

        Parameters:
            tasks (list): List of task indices representing the assignment order.

        Returns:
            float: Optimal deployment location based on data volume.
        """
        tasks_list = tasks.astype(int).tolist()
        data_volumes = [self.data["nodes"][task]["data_volume"] for task in tasks_list]
        total_data_volume = sum(data_volumes)
        optimal_location = total_data_volume / len(tasks)  # Simple example, can be more complex
        return optimal_location

    def obj_func(self, tasks):
        """
        Multi-objective function to be minimized.

        Parameters:
            tasks (numpy.ndarray): Decoded solution containing the assignment order of tasks.

        Returns:
            list: Objective function values.
        """
        return [
            self.objective_min_energy_consumption(tasks),
            self.objective_min_latency(tasks),
            self.objective_find_deployment_location_data_volume(tasks),
        ]


def load_task_shifting_data(file_path):
    """Load task shifting data from a JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)


def main():
    # Load task shifting data
    task_shifting_data = load_task_shifting_data("docs/dag_model.json")

    # Extract necessary information from the loaded data
    n_tasks = len(task_shifting_data["nodes"])

    # Define permutation bounds
    task_bounds = PermutationVar(valid_set=list(range(n_tasks)), name="per_var")

    # Define objectives weights
    weights = [0.4, 0.1, 0.5]

    # Create the TaskShiftingProblem instance
    task_shifting_problem_multi = TaskShiftingProblem(
        bounds=task_bounds, minmax="min", data=task_shifting_data, obj_weights=weights
    )

    # Solve the problem using WOA algorithm
    model = WOA.OriginalWOA(epoch=1000, pop_size=20)
    model.solve(problem=task_shifting_problem_multi)

    # Visualization purposes
    # You can access them all via object "history" like this:
    model.history.save_global_objectives_chart(filename="docs/algo/goc")
    model.history.save_local_objectives_chart(filename="docs/algo/loc")
    model.history.save_global_best_fitness_chart(filename="docs/algo/gbfc")
    model.history.save_local_best_fitness_chart(filename="docs/algo/lbfc")
    model.history.save_runtime_chart(filename="docs/algo/rtc")
    model.history.save_exploration_exploitation_chart(filename="docs/algo/eec")
    model.history.save_diversity_chart(filename="docs/algo/dc")

    # Print results
    best_solution = task_shifting_problem_multi.decode_solution(model.g_best.solution)
    logger.info(f"Best solution: {best_solution}")
    logger.info(f"Best fitness: {model.g_best.target.fitness}")


if __name__ == "__main__":
    main()
