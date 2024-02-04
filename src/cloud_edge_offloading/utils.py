import json
from collections import defaultdict

def load_dag_graph(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def generate_output_data(problem, model, output_folder):
    cloud_offloading_var = problem.decode_solution(model.g_best.solution)['cloud_offloading_var']
    cloud_tasks_to_shift = [cloud_node['id'] for i, cloud_node in enumerate(problem.cloud_nodes) if cloud_offloading_var[i] == 1]

    output_data = {
        "offloading_decision": {
            "cloud_tasks_total_number": len(problem.cloud_nodes),
            "cloud_tasks_total_number_to_shift": len(cloud_tasks_to_shift),
            "cloud_tasks_to_shift_from_cloud_to_edge": cloud_tasks_to_shift
        },
        "offloading_debug": problem.cloud_nodes_results
    }

    with open(f'{output_folder}cloud_offloading_results.json', 'w') as results_file:
        json.dump(output_data, results_file, indent=2)

def print_best_results(model):
    print(f"Best agent: {model.g_best}")
    print(f"Best solution: {model.g_best.solution}")
    print(f"Best fitness: {model.g_best.target.fitness}")
    print(f"Best parameters: {model.problem.decode_solution(model.g_best.solution)}")

def visualize_algorithm_charts(model, output_folder):
    model.history.save_global_objectives_chart(filename=f"{output_folder}goc")
    model.history.save_local_objectives_chart(filename=f"{output_folder}loc")
    model.history.save_global_best_fitness_chart(filename=f"{output_folder}gbfc")
    model.history.save_local_best_fitness_chart(filename=f"{output_folder}lbfc")
    model.history.save_runtime_chart(filename=f"{output_folder}rtc")
    model.history.save_exploration_exploitation_chart(filename=f"{output_folder}eec")
    model.history.save_diversity_chart(filename=f"{output_folder}dc")
    model.history.save_trajectory_chart(filename=f"{output_folder}tc")

def initialize_results_structure():
    return defaultdict(lambda: {"links": defaultdict(dict)})
