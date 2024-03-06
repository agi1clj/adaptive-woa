import json
from collections import defaultdict


def load_dag_graph(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def generate_output_data(problem, model, output_folder):
    offloading_var = problem.decode_solution(model.g_best.solution)["offloading_var"]
    tasks_to_shift = [
        offloading_node["id"]
        for i, offloading_node in enumerate(problem.cloud_nodes + problem.fog_nodes)
        if offloading_var[i] == 1
    ]


    tasks_to_shift_details = []

    for task_id in tasks_to_shift:
        task_links = problem.nodes_results.get(task_id, {}).get("links", {})
        # Find the best edge node based on both comp euclidean dist and rtt
        best_node = min(
            task_links.keys(),
            key=lambda task: (
                task_links[task]["comp_euclidean_dist"],
                task_links[task]["rtt"],
            ),
        )

        tasks_to_shift_details.append(
            {
                "task_id": task_id,
                "best_node": best_node,
                "details": task_links[best_node],
            }
        )

    output_data = {
        "offloading_decision": {
            "tasks_total_number": len(problem.cloud_nodes + problem.fog_nodes),
            "tasks_number_to_offload": len(tasks_to_shift),
            "tasks_to_offload": tasks_to_shift,
            "tasks_to_offload_details": tasks_to_shift_details,
        },
        "offloading_debug": problem.nodes_results,
    }

    with open(f"{output_folder}offloading_results.json", "w") as results_file:
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
