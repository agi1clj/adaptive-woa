from mealpy import BinaryVar, WOA, Problem
import json
import sys


class EdgeCloudOffloadingProblem(Problem):
    def __init__(self, nodes):
        self.nodes = self.extract_cloud_tasks(nodes)
        self.links = nodes["links"]
        self.eps = -10000000 # Penalty value
        self.cloud_nodes_rtt = {node["id"]: 0 for node in self.nodes}  # Dictionary to store RTT values per cloud node
        bounds = BinaryVar(n_vars=len(self.nodes), name="offloading_var")
        super().__init__(bounds=bounds, minmax="max", save_population=True)

    def extract_cloud_tasks(self, nodes_data):
        return [node for node in nodes_data.get("nodes", []) if node.get("type") == "CloudTask"]

    @staticmethod
    def calculate_rtt(bandwidth_mbps, latency_ms, distance_km):
        distance_meters = distance_km * 1000  # distance to meters
        bandwidth_bps = bandwidth_mbps * 1e6  # bandwidth to bits per second
        propagation_delay = distance_meters / 2.998e8  # Speed of light in meters per second
        transmission_delay = (8 * 1e-6) / bandwidth_bps  # 8 bits in a byte, and latency is in milliseconds
        total_delay_ms = (propagation_delay + transmission_delay + latency_ms / 1000) * 1000
        return total_delay_ms

    def obj_func(self, x):
        x_decoded = self.decode_solution(x)
        offloading_var = x_decoded["offloading_var"]
        total_rtt = 0  # Initialize the maximum round-trip time
        for i, source_node in enumerate(self.nodes):
            if offloading_var[i] == 1:
                relevant_links = [link for link in self.links if link["source"] == source_node["id"]]
                for link in relevant_links:
                    total_rtt += self.calculate_rtt(link["bandwidth"], link["latency"], link["distance"])
                average_rtt = total_rtt / len(relevant_links)
                total_rtt = average_rtt
                self.cloud_nodes_rtt[source_node["id"]] = total_rtt

        if total_rtt == 0:  # If any cloud node has 0 value, it indicates that this node is not having any edge.
            return self.eps

        # A good round-trip time (RTT) should be below 100 milliseconds for optimal performance.
        # https://aws.amazon.com/what-is/rtt-in-networking/
        if total_rtt > 100:
             return self.eps + total_rtt
           
        return total_rtt


if __name__ == "__main__":
    sys.stdout = open('docs/output.txt', 'w')
    sys.stdout = sys.__stdout__
    # Example usage for cloud offloading to edge
    with open("docs/dag_model.json", "r") as file:
        nodes_data = json.load(file)

    problem = EdgeCloudOffloadingProblem(nodes_data)
    model = WOA.HI_WOA(epoch=1000, pop_size=5)
    model.solve(problem)

    # Visualization purposes
    # You can access them all via object "history" like this:
    charts_path = "docs/algo/"
    model.history.save_global_objectives_chart(filename=f"{charts_path}goc")
    model.history.save_local_objectives_chart(filename=f"{charts_path}loc")
    model.history.save_global_best_fitness_chart(filename=f"{charts_path}gbfc")
    model.history.save_local_best_fitness_chart(filename=f"{charts_path}lbfc")
    model.history.save_runtime_chart(filename=f"{charts_path}rtc")
    model.history.save_exploration_exploitation_chart(filename=f"{charts_path}eec")
    model.history.save_diversity_chart(filename=f"{charts_path}dc")
    model.history.save_trajectory_chart(filename=f"{charts_path}tc")

    # Save prints into a file
    with open('docs/output.txt', 'w') as output_file:
        print("\n------------------- Algorithm output ---", file=output_file)
        print(f"Best agent: {model.g_best}", file=output_file)
        print(f"Best solution: {model.g_best.solution}", file=output_file)
        print(f"Best fitness: {model.g_best.target.fitness}", file=output_file)
        print(f"Best offloading configuration: {problem.decode_solution(model.g_best.solution)}", file=output_file)

        offloading_var = problem.decode_solution(model.g_best.solution)['offloading_var']

        cloud_tasks_to_shift = [node_id for i, node_id in enumerate(problem.cloud_nodes_rtt) if offloading_var[i] == 1]
        print("\n-------------------- Offloading decision ---", file=output_file)
        print(f"CloudTasks total number: {len(problem.nodes)}", file=output_file)
        print(f"CloudTasks total number to shift: {len(cloud_tasks_to_shift)}", file=output_file)
        print(f"CloudTasks to shift from cloud to edge: {cloud_tasks_to_shift}", file=output_file)
        print("\n-------------------- Offloading Debug --- ", file=output_file)
        # Display RTT values for the tasks shifted
        rtt_values_for_shifted_tasks = {node_id: problem.cloud_nodes_rtt[node_id] for node_id in cloud_tasks_to_shift}
        print("RTT values for selected Cloud tasks:", rtt_values_for_shifted_tasks, file=output_file)
        print("All RTT values for all Cloud tasks: ", problem.cloud_nodes_rtt, file=output_file)