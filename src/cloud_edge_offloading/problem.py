from collections import defaultdict
import numpy as np
from mealpy import BinaryVar, WOA, Problem
import json
import yaml

class CloudToEdgeOffloadingProblem(Problem):
    def __init__(self, nodes, threshold_rtt=90, threshold_comp_euclidean_dist=10):
        # DAG Graph data
        self.nodes = nodes["nodes"]
        self.cloud_nodes = self.extract_cloud_tasks(nodes)
        self.cloud_nodes_results = defaultdict(lambda: {"links": defaultdict(dict)})
        self.edge_nodes = self.extract_edge_tasks(nodes)
        self.threshold_rtt = threshold_rtt
        self.threshold_comp_euclidean_dist = threshold_comp_euclidean_dist
        self.links = nodes["links"]

        # Penalties
        self.threshold_penalty_factor = -10

        bounds = BinaryVar(n_vars=len(self.cloud_nodes), name="cloud_offloading_var")
        super().__init__(bounds=bounds, minmax="max", save_population=True)


    @staticmethod
    def extract_cloud_tasks(nodes_data):
        return [node for node in nodes_data.get("nodes", []) if node.get("type") == "CloudTask"]

    @staticmethod
    def extract_edge_tasks(nodes_data):
        return [node for node in nodes_data.get("nodes", []) if node.get("type") == "EdgeTask"]

    @staticmethod
    def calculate_rtt(bandwidth_mbps, latency_ms, distance_km):
        distance_meters = distance_km * 1000  
        bandwidth_bps = bandwidth_mbps * 1e6 
        propagation_delay = distance_meters / 2.998e8  # Speed of light in meters per second
        transmission_delay = (8 * 1e-6) / bandwidth_bps  # 8 bits in a byte, and latency is in ms
        total_delay_ms = (propagation_delay + transmission_delay + latency_ms / 1000) * 1000
        return total_delay_ms

    @staticmethod
    def calculate_comp_euclidean_dist(cloud_task, edge_task):
        cpu_distance = abs(cloud_task["computational_requirements"]["cpu_ghz"] - edge_task["computational_capacity"]["cpu_ghz"])
        mem_distance = abs(cloud_task["computational_requirements"]["memory_gb"] - edge_task["computational_capacity"]["memory_gb"])
        ram_distance = abs(cloud_task["computational_requirements"]["ram_gb"] - edge_task["computational_capacity"]["ram_gb"])
        return np.sqrt(cpu_distance**2 + mem_distance**2 + ram_distance**2)
        
    def obj_func(self, x):
        x_decoded = self.decode_solution(x)
        offloading_var = x_decoded["cloud_offloading_var"]
        total_rtt, total_distance = 0, 0  # Initialize total RTT and distance penalties

        for i, cloud_node in enumerate(self.cloud_nodes):
            if offloading_var[i] == 1:
                relevant_links = [link for link in self.links if link["source"] == cloud_node["id"]]
                for link in relevant_links:
                    target_edge_node = [edge_node for edge_node in self.edge_nodes if edge_node['id'] == link['target']][0]
                    link_rtt = self.calculate_rtt(link["bandwidth_mbps"], link["latency_ms"], link["distance_km"])
                    link_distance = self.calculate_comp_euclidean_dist(cloud_node, target_edge_node)
                    self.cloud_nodes_results[cloud_node["id"]]["links"][target_edge_node["id"]] = {
                        'comp_euclidean_dist': link_distance,
                        'rtt': link_rtt
                    }
                    
                    # Penalty for RTT
                    if link_rtt > self.threshold_rtt:
                        total_rtt += self.threshold_penalty_factor * (link_rtt - self.threshold_rtt)
                    else:
                        total_rtt += link_rtt

                    # Penalty for eucledean distance
                    if link_distance > self.threshold_comp_euclidean_dist:
                        total_distance += self.threshold_penalty_factor * (link_distance - self.threshold_comp_euclidean_dist)
                    else:
                        total_distance += link_distance

        fitness = total_rtt + total_distance
        return fitness
    
def load_dag_graph(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def solve_cloud_to_edge_offloading(nodes_data, config_algo_data):
    problem = CloudToEdgeOffloadingProblem(nodes_data, threshold_rtt=config_algo_data['threshold_rtt'], threshold_comp_euclidean_dist=config_algo_data['threshold_comp_euclidean_dist'])
    model = WOA.HI_WOA(epoch=config_algo_data['epoch'], pop_size=config_algo_data['pop_size'])
    model.solve(problem)
    return problem, model

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

if __name__ == "__main__":
    dag_files = ["docs/dag_large/dag_model.json", "docs/dag_medium/dag_model.json", "docs/dag_small/dag_model.json"]
    for dag_file in dag_files:
        nodes_data = load_dag_graph(dag_file)
        problem, model = solve_cloud_to_edge_offloading(nodes_data)
        output_folder = f"docs/{dag_file.split('/')[1]}/algo/"
        generate_output_data(problem, model, output_folder)
        print_best_results(model)
        visualize_algorithm_charts(model, output_folder)
