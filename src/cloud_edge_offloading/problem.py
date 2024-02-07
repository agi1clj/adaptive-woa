from collections import defaultdict
import numpy as np
from mealpy import BinaryVar, WOA, Problem


class CloudToEdgeOffloadingProblem(Problem):
    def __init__(
        self,
        nodes,
        threshold_rtt=90,
        threshold_comp_euclidean_dist=10,
        threshold_penalty_factor=-10,
    ):
        # DAG Graph data
        self.nodes = nodes["nodes"]
        self.cloud_nodes = self.extract_cloud_tasks(nodes)
        self.cloud_nodes_results = defaultdict(lambda: {"links": defaultdict(dict)})
        self.edge_nodes = self.extract_edge_tasks(nodes)
        self.threshold_rtt = threshold_rtt
        self.threshold_comp_euclidean_dist = threshold_comp_euclidean_dist
        self.links = nodes["links"]

        # Penalties
        self.threshold_penalty_factor = threshold_penalty_factor

        bounds = BinaryVar(n_vars=len(self.cloud_nodes), name="cloud_offloading_var")
        super().__init__(bounds=bounds, minmax="max", save_population=True)

    @staticmethod
    def extract_cloud_tasks(nodes_data):
        return [
            node
            for node in nodes_data.get("nodes", [])
            if node.get("type") == "CloudTask"
        ]

    @staticmethod
    def extract_edge_tasks(nodes_data):
        return [
            node
            for node in nodes_data.get("nodes", [])
            if node.get("type") == "EdgeTask"
        ]

    @staticmethod
    def calculate_rtt(bandwidth_mbps, latency_ms, distance_km):
        distance_meters = distance_km * 1000
        bandwidth_bps = bandwidth_mbps * 1e6
        propagation_delay = (
            distance_meters / 2.998e8
        )  # Speed of light in meters per second
        transmission_delay = (
            8 * 1e-6
        ) / bandwidth_bps  # 8 bits in a byte, and latency is in ms
        total_delay_ms = (
            propagation_delay + transmission_delay + latency_ms / 1000
        ) * 1000
        return total_delay_ms

    @staticmethod
    def calculate_comp_euclidean_dist(cloud_task, edge_task):
        cpu_distance = abs(
            cloud_task["computational_requirements"]["cpu_ghz"]
            - edge_task["computational_capacity"]["cpu_ghz"]
        )
        mem_distance = abs(
            cloud_task["computational_requirements"]["memory_gb"]
            - edge_task["computational_capacity"]["memory_gb"]
        )
        ram_distance = abs(
            cloud_task["computational_requirements"]["ram_gb"]
            - edge_task["computational_capacity"]["ram_gb"]
        )
        return np.sqrt(cpu_distance**2 + mem_distance**2 + ram_distance**2)

    def obj_func(self, x):
        x_decoded = self.decode_solution(x)
        offloading_var = x_decoded["cloud_offloading_var"]
        total_rtt, total_distance = 0, 0  # Initialize total RTT and distance penalties

        for i, cloud_node in enumerate(self.cloud_nodes):
            if offloading_var[i] == 1:
                relevant_links = [
                    link for link in self.links if link["source"] == cloud_node["id"]
                ]
                for link in relevant_links:
                    target_edge_node = [
                        edge_node
                        for edge_node in self.edge_nodes
                        if edge_node["id"] == link["target"]
                    ][0]
                    link_rtt = self.calculate_rtt(
                        link["bandwidth_mbps"], link["latency_ms"], link["distance_km"]
                    )
                    link_distance = self.calculate_comp_euclidean_dist(
                        cloud_node, target_edge_node
                    )
                    self.cloud_nodes_results[cloud_node["id"]]["links"][
                        target_edge_node["id"]
                    ] = {"comp_euclidean_dist": link_distance, "rtt": link_rtt}

                    # Penalty for RTT
                    if link_rtt > self.threshold_rtt:
                        total_rtt += self.threshold_penalty_factor * (
                            link_rtt - self.threshold_rtt
                        )
                    else:
                        total_rtt += link_rtt

                    # Penalty for euclidean distance
                    if link_distance > self.threshold_comp_euclidean_dist:
                        total_distance += self.threshold_penalty_factor * (
                            link_distance - self.threshold_comp_euclidean_dist
                        )
                    else:
                        total_distance += link_distance

        fitness = total_rtt + total_distance
        return fitness


def solve_cloud_to_edge_offloading(nodes_data, config_algo_data):
    problem = CloudToEdgeOffloadingProblem(
        nodes_data,
        threshold_rtt=config_algo_data["threshold_rtt"],
        threshold_comp_euclidean_dist=config_algo_data["threshold_comp_euclidean_dist"],
        threshold_penalty_factor=config_algo_data["threshold_penalty_factor"],
    )
    model = WOA.HI_WOA(
        epoch=config_algo_data["epoch"], pop_size=config_algo_data["pop_size"]
    )
    model.solve(problem)
    return problem, model
