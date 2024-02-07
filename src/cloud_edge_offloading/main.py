from utils import (
    load_dag_graph,
    generate_output_data,
    print_best_results,
    visualize_algorithm_charts,
)
from problem import solve_cloud_to_edge_offloading
import os
import yaml


def load_configuration(file_path):
    with open(file_path, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config


if __name__ == "__main__":
    config_files = [
        "src/cloud_edge_offloading/config/dag_small.yaml",
        "src/cloud_edge_offloading/config/dag_medium.yaml",
        "src/cloud_edge_offloading/config/dag_large.yaml",
    ]
    for config_file in config_files:
        config_yaml = load_configuration(config_file)
        dag_file_path = config_yaml["dag"]["file_path"]
        nodes_data = load_dag_graph(dag_file_path)
        config_algo_data = config_yaml["algo"]
        problem, model = solve_cloud_to_edge_offloading(nodes_data, config_algo_data)
        folder_name = dag_file_path.split("/")[1]
        output_folder = f"docs/{folder_name}/algo/"
        os.makedirs(output_folder, exist_ok=True)
        generate_output_data(problem, model, output_folder)
        print_best_results(model)
        visualize_algorithm_charts(model, output_folder)
