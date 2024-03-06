from collections import defaultdict
import numpy as np
from mealpy import BinaryVar, WOA, Problem


class OffloadingProblem(Problem):
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
        self.nodes_results = defaultdict(lambda: {"links": defaultdict(dict)})
        self.edge_nodes = self.extract_edge_tasks(nodes)
        self.fog_nodes = self.extract_fog_tasks(nodes)
        self.threshold_rtt = threshold_rtt
        self.threshold_comp_euclidean_dist = threshold_comp_euclidean_dist
        self.links = nodes["links"]
        self.total_distance = 0
        self.total_rtt = 0

        # Penalties
        self.threshold_penalty_factor = threshold_penalty_factor

        bounds = BinaryVar(
            n_vars=len(self.cloud_nodes + self.fog_nodes), name="offloading_var"
        )
        super().__init__(bounds=bounds, minmax="max", save_population=True, obj_weights=[0.5, 0.5]  )

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
    def extract_fog_tasks(nodes_data):
        return [
            node
            for node in nodes_data.get("nodes", [])
            if node.get("type") == "FogTask"
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
    def calculate_comp_euclidean_dist(source_task, target_task):
        cpu_distance = abs(
            source_task["computational_requirements"]["cpu_ghz"]
            - target_task["computational_requirements"]["cpu_ghz"]
        )
        mem_distance = abs(
            source_task["computational_requirements"]["memory_gb"]
            - target_task["computational_requirements"]["memory_gb"]
        )
        ram_distance = abs(
            source_task["computational_requirements"]["ram_gb"]
            - target_task["computational_requirements"]["ram_gb"]
        )
        return np.sqrt(cpu_distance**2 + mem_distance**2 + ram_distance**2)

    def calculate_offloading(
        self, offloading_var, offloading_nodes, target_nodes
    ):
        local_total_rtt, local_total_distance = 0, 0
        for i, offloading_node in enumerate(offloading_nodes):
            if offloading_var[i] == 1:
                relevant_links = [
                    link
                    for link in self.links
                    if link["source"] == offloading_node["id"]
                ]           
                for link in relevant_links:
                    target_nodes_local = [
                        target_node
                        for target_node in target_nodes
                        if target_node["id"] == link["target"]
                    ][0]
                    link_rtt = self.calculate_rtt(
                        link["bandwidth_mbps"], link["latency_ms"], link["distance_km"]
                    )
                    link_distance = self.calculate_comp_euclidean_dist(
                        offloading_node, target_nodes_local
                    )
                    self.nodes_results[offloading_node["id"]]["links"][
                        target_nodes_local["id"]
                    ] = {"comp_euclidean_dist": link_distance, "rtt": link_rtt}

                    # Penalty for RTT
                    if link_rtt > self.threshold_rtt:
                        local_total_rtt += self.threshold_penalty_factor * (
                            link_rtt - self.threshold_rtt
                        )
                    else:
                        local_total_rtt += link_rtt

                    # Penalty for euclidean distance
                    if link_distance > self.threshold_comp_euclidean_dist:
                        local_total_distance += self.threshold_penalty_factor * (
                            link_distance - self.threshold_comp_euclidean_dist
                        )
                    else:
                        local_total_distance += link_distance
        return local_total_rtt, local_total_distance    
    
    def obj_func(self, x):
        x_decoded = self.decode_solution(x)
        offloading_var = x_decoded["offloading_var"]
        # Cloud to Fog Offloading
        cloud_total_rtt, cloud_total_distance = self.calculate_offloading(
            offloading_var, self.cloud_nodes, self.fog_nodes
        )

        # Fog to Edge offloading
        fog_total_rtt, fog_total_distance = self.calculate_offloading(
            offloading_var, self.fog_nodes, self.edge_nodes,
        )

        return [cloud_total_rtt + cloud_total_distance, fog_total_rtt + fog_total_distance]


def offloading(nodes_data, config_algo_data):
    problem = OffloadingProblem(
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
