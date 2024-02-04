import networkx as nx
from pyvis.network import Network
import random
import json

def generate_tasks(task_names, task_type, regions, providers, cpu_ghz_range, memory_gb_range):
    tasks = {}
    ram_values = [2, 4, 8, 16, 32]
    for task_name in task_names:
        region = random.choice(regions)
        provider = random.choice(providers)
        is_cloud_task = task_type == "CloudTask"
        tasks[task_name] = {
            "type": task_type,
            "region": region,
            "provider": provider,
            "computational_requirements" if is_cloud_task else "computational_capacity": {
                "cpu_ghz": random.uniform(*cpu_ghz_range),
                "memory_gb": random.uniform(*memory_gb_range),
                "ram_gb": random.choice(ram_values)
            },
        }
    return tasks

def generate_edges(source_tasks, target_tasks, edge_func):
    edges = []
    if target_tasks:
        target_task_keys = list(target_tasks.keys())
        for source_task in source_tasks:
            for target_task in random.sample(target_task_keys, random.randint(1, len(target_task_keys))):
                edges.append(edge_func(source_task, target_task))
    return edges

def edge_func_latency_bandwidth(latency_range, bandwidth_range, distance_range):
    def inner(source, target):
        return (source, target, {
            "latency_ms": random.uniform(*latency_range),
            "bandwidth_mbps": random.uniform(*bandwidth_range),
            "distance_km": random.uniform(*distance_range)
        })
    return inner

def generate_dag():
    dag = nx.DiGraph()

    regions = [
        "eu-west-1",
        "eu-west-2",
        "eu-central-1",
        "eu-west-3",
        "eu-north-1",
        "eu-south-1",
        "eu-west-2",
    ]

    edge_task_names = [f"Edge_Task_{i}" for i in range(5)]
    cloud_task_names = [f"Cloud_Task_{i}" for i in range(12)]

    edge_tasks = generate_tasks(
        task_names=edge_task_names,
        task_type="EdgeTask",
        regions=regions,
        providers=["MdC-01", "MdC-02", "MdC-03"],
        cpu_ghz_range=(30, 50),
        memory_gb_range=(8, 32),
    )

    cloud_tasks = generate_tasks(
        task_names=cloud_task_names,
        task_type="CloudTask",
        regions=regions,
        providers=["AWS", "Azure", "Heroku", "GCP"],
        cpu_ghz_range=(30, 50),
        memory_gb_range=(8, 32)
    )

    dag.add_nodes_from(list(edge_tasks.items()) + list(cloud_tasks.items()))
    edge_func_edge_to_cloud = edge_func_latency_bandwidth((50, 100), (1, 10), (500, 1000))
    edge_edges = generate_edges(cloud_tasks, edge_tasks, edge_func_edge_to_cloud)
    dag.add_edges_from(edge_edges)

    return dag

# Generate the DAG
dag = generate_dag()

# Set node attributes for hover text
node_properties = {
    node: (
        f"{node}, Type: {dag.nodes[node]['type']}, Region: {dag.nodes[node]['region']}, "
        f"Provider: {dag.nodes[node]['provider']}, "
        f"CPU: {dag.nodes[node]['computational_requirements']['cpu_ghz']:.2f} GHz, "
        f"Memory: {dag.nodes[node]['computational_requirements']['memory_gb']:.2f} GB, "
        f"Ram: {dag.nodes[node]['computational_requirements']['ram_gb']:.2f} GB"
    )
    if dag.nodes[node]['type'] == 'CloudTask'
    else (
        f"{node}, Type: {dag.nodes[node]['type']}, Region: {dag.nodes[node]['region']}, "
        f"Provider: {dag.nodes[node]['provider']}, "
        f"CPU: {dag.nodes[node]['computational_capacity']['cpu_ghz']:.2f} GHz, "
        f"Memory: {dag.nodes[node]['computational_capacity']['memory_gb']:.2f} GB, "
        f"Ram: {dag.nodes[node]['computational_capacity']['ram_gb']:.2f} GB"
    )
    for node in dag.nodes
}

edge_properties = {
    (edge[0], edge[1]): f"Latency: {dag.edges[edge]['latency_ms']:.2f} ms, "
                       f"Bandwidth: {dag.edges[edge]['bandwidth_mbps']:.2f} Mbps, "
                       f"Distance: {dag.edges[edge]['distance_km']:.2f} km"
    for edge in dag.edges
}

g = Network(notebook=True)
g.force_atlas_2based()

# Add nodes and edges
for node, properties in node_properties.items():
    node_type = dag.nodes[node]["type"]
    color = (
        "green"
        if node_type == "EdgeTask"
        else "blue"
    )
    g.add_node(node, title=properties, color=color)

for edge, properties in edge_properties.items():
    g.add_edge(edge[0], edge[1], title=properties)

g.show("docs/dag.html")

# Export the DAG to JSON format
dag_json = nx.node_link_data(dag)

# Save the JSON to a file
with open("docs/dag_model.json", "w") as json_file:
    json.dump(dag_json, json_file, indent=2)
