from collections import defaultdict
import numpy as np
from mealpy import BinaryVar, WOA, Problem
import json

class CloudToEdgeOffloadingProblem(Problem):
    def __init__(self, nodes):
        # DAG Graph data
        self.nodes = nodes["nodes"]
        self.cloud_nodes = self.extract_cloud_tasks(nodes)
        self.edge_nodes = self.extract_edge_tasks(nodes)
        self.links = nodes["links"]
        self.cloud_nodes_results = defaultdict(lambda: {"links": defaultdict(dict), "average_rtt": 0, "average_euclidean_distance": 0})

        # Penalties
        self.eps = -1e10
        self.threshold_penalty_factor = -10

        # Thresholds
        self.threshold_rtt = 100
        self.threshold_euclidean_distance = 10

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
        distance_meters = distance_km * 1000  # distance to meters
        bandwidth_bps = bandwidth_mbps * 1e6  # bandwidth to bits per second
        propagation_delay = distance_meters / 2.998e8  # Speed of light in meters per second
        transmission_delay = (8 * 1e-6) / bandwidth_bps  # 8 bits in a byte, and latency is in milliseconds
        total_delay_ms = (propagation_delay + transmission_delay + latency_ms / 1000) * 1000
        return total_delay_ms

    @staticmethod
    def calculate_euclidean_distance(cloud_task, edge_task):
        cpu_distance = abs(cloud_task["computational_requirements"]["cpu_ghz"] - edge_task["computational_capacity"]["cpu_ghz"])
        mem_distance = abs(cloud_task["computational_requirements"]["memory_gb"] - edge_task["computational_capacity"]["memory_gb"])
        ram_distance = abs(cloud_task["computational_requirements"]["ram_gb"] - edge_task["computational_capacity"]["ram_gb"])
        return np.sqrt(cpu_distance**2 + mem_distance**2 + ram_distance**2)

    def obj_func(self, x):
        x_decoded = self.decode_solution(x)
        offloading_var = x_decoded["cloud_offloading_var"]
        total_rtt = 0  # Initialize the maximum round-trip time
        total_distance = 0  # Initialize the total distance penalty
        for i, cloud_node in enumerate(self.cloud_nodes):
            if offloading_var[i] == 1:
                relevant_links = [link for link in self.links if link["source"] == cloud_node["id"]]
                relevant_links_rtt = 0
                relevant_links_distance = 0

                for link in relevant_links:
                    link_rtt = self.calculate_rtt(link["bandwidth_mbps"], link["latency_ms"], link["distance_km"])
                    relevant_links_rtt += link_rtt

                    target_edge_node = [edge_node for edge_node in self.edge_nodes if edge_node['id'] == link['target']][0]
                    link_distance = self.calculate_euclidean_distance(cloud_node, target_edge_node)
                    relevant_links_distance  += link_distance
                    self.cloud_nodes_results[cloud_node["id"]]["links"][target_edge_node["id"]] = {
                        'euclidean_distance': link_distance,
                        'rtt': link_rtt
                        }
                    
                    # Penalty for eucledean distance
                    if link_distance > self.threshold_euclidean_distance:
                        total_distance += self.threshold_penalty_factor * (link_distance - self.threshold_euclidean_distance)

                    # Penalty for RTT
                    if link_rtt > self.threshold_rtt:
                        total_rtt += self.threshold_penalty_factor * (link_rtt - self.threshold_rtt)


                average_relevant_links_rtt = relevant_links_rtt / len(relevant_links)
                average_relevant_link_distance = relevant_links_distance / len(relevant_links)

                total_rtt += average_relevant_links_rtt
                total_distance += average_relevant_link_distance


                self.cloud_nodes_results[cloud_node["id"]]["total_rtt"] = relevant_links_rtt
                self.cloud_nodes_results[cloud_node["id"]]["total_euclidean_distance"] = relevant_links_distance
                self.cloud_nodes_results[cloud_node["id"]]["average_rtt"] = average_relevant_links_rtt
                self.cloud_nodes_results[cloud_node["id"]]["average_euclidean_distance"] = average_relevant_link_distance
                

        if total_rtt == 0:  # If any cloud node has 0 value, it indicates that this node is not having any edge.
            return self.eps

        return total_rtt + total_distance


if __name__ == "__main__":
    # Load the input DAG graph for cloud to edge offloading
    with open("docs/dag_model.json", "r") as file:
        nodes_data = json.load(file)

    problem = CloudToEdgeOffloadingProblem(nodes_data)
    model = WOA.HI_WOA(epoch=1000, pop_size=20)
    model.solve(problem)

    # Output results from the problem into JSON
    cloud_offloading_var = problem.decode_solution(model.g_best.solution)['cloud_offloading_var']
    cloud_tasks_to_shift = [cloud_node['id'] for i, cloud_node in enumerate(problem.cloud_nodes) if cloud_offloading_var[i] == 1]
    output_data = {
    "offloading_decision": {
        "cloud_tasks_total_number": len(problem.nodes),
        "cloud_tasks_total_number_to_shift": len(cloud_tasks_to_shift),
        "cloud_tasks_to_shift_from_cloud_to_edge": cloud_tasks_to_shift
    },
    "offloading_debug": problem.cloud_nodes_results
    }
    
    with open('docs/cloud_offloading_results.json', 'w') as results_file:
        json.dump(output_data, results_file, indent=2)

    print(f"Best agent: {model.g_best}")
    print(f"Best solution: {model.g_best.solution}")
    print(f"Best fitness: {model.g_best.target.fitness}")
    print(f"Best parameters: {model.problem.decode_solution(model.g_best.solution)}")

    # Algorithm charts Visualization
    charts_path = "docs/algo/"
    model.history.save_global_objectives_chart(filename=f"{charts_path}goc")
    model.history.save_local_objectives_chart(filename=f"{charts_path}loc")
    model.history.save_global_best_fitness_chart(filename=f"{charts_path}gbfc")
    model.history.save_local_best_fitness_chart(filename=f"{charts_path}lbfc")
    model.history.save_runtime_chart(filename=f"{charts_path}rtc")
    model.history.save_exploration_exploitation_chart(filename=f"{charts_path}eec")
    model.history.save_diversity_chart(filename=f"{charts_path}dc")
    model.history.save_trajectory_chart(filename=f"{charts_path}tc")
