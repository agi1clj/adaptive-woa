import networkx as nx
from pyvis.network import Network
import random
import json

def generate_tasks(task_names, task_type, regions, providers, data_volume_range, computational_requirements_range, energy_consumption_range):
    tasks = {}
    for task_name in task_names:
        region = random.choice(regions)
        provider = random.choice(providers)
        tasks[task_name] = {
            "type": task_type,
            "region": region,
            "provider": provider,
            "data_volume": random.uniform(*data_volume_range),
            "computational_requirements": {
                "cpu": random.uniform(*computational_requirements_range),
                "memory": random.uniform(*computational_requirements_range),
            },
            "energy_consumption": random.uniform(*energy_consumption_range),
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
            "latency": random.uniform(*latency_range),
            "bandwidth": random.uniform(*bandwidth_range),
            "distance": random.uniform(*distance_range)
        })
    return inner

def generate_dag(fog_layer=True):
    dag = nx.DiGraph()

    aws_regions = [
        "eu-west-1",
        "eu-west-2",
        "eu-central-1",
        "eu-west-3",
        "eu-north-1",
        "eu-south-1",
        "eu-west-2",
    ]

    edge_task_names = [f"Edge_Task_{i}" for i in range(35)]
    fog_task_names = [f"Fog_Task_{i}" for i in range(5)] if fog_layer else []
    cloud_task_names = [f"Cloud_Task_{i}" for i in range(100)]

    edge_tasks = generate_tasks(
        edge_task_names,
        "EdgeTask",
        aws_regions,
        ["MdC-01", "MdC-02", "MdC-03"],
        (1, 10),
        (5, 10),
        (20, 40)
    )

    fog_tasks = generate_tasks(
        fog_task_names,
        "FogTask",
        aws_regions,
        ["DC-01", "DC-02", "DC-03"],
        (10, 50),
        (10, 30),
        (30, 60)
    ) if fog_layer else {}

    cloud_tasks = generate_tasks(
        cloud_task_names,
        "CloudTask",
        aws_regions,
        ["AWS", "Azure", "Heroku", "GCP"],
        (50, 100),
        (30, 50),
        (60, 80)
    )

    dag.add_nodes_from(list(edge_tasks.items()) + list(fog_tasks.items()) + list(cloud_tasks.items()))

    if fog_layer:
        edge_func_edge_to_fog = edge_func_latency_bandwidth((1, 5), (5, 10), (1, 100))
        edge_edges = generate_edges(edge_tasks, fog_tasks, edge_func_edge_to_fog)
        dag.add_edges_from(edge_edges)

        edge_func_fog_to_cloud = edge_func_latency_bandwidth((5, 10), (10, 20), (100, 150))
        fog_edges = generate_edges(fog_tasks, cloud_tasks, edge_func_fog_to_cloud)
        dag.add_edges_from(fog_edges)
    else:
        edge_func_edge_to_cloud = edge_func_latency_bandwidth((50, 100), (1, 10), (500, 1000))
        edge_edges = generate_edges(cloud_tasks, edge_tasks, edge_func_edge_to_cloud)
        dag.add_edges_from(edge_edges)

    return dag

# Generate the DAG
dag = generate_dag(fog_layer=False)

# Set node attributes for hover text
node_properties = {
    node: f"{node}, Type: {dag.nodes[node]['type']}, Region: {dag.nodes[node]['region']}, "
    f"Provider: {dag.nodes[node]['provider']}, "
    f"Data Volume: {dag.nodes[node]['data_volume']:.2f} GB, "
    f"CPU: {dag.nodes[node]['computational_requirements']['cpu']:.2f} GHz, "
    f"Memory: {dag.nodes[node]['computational_requirements']['memory']:.2f} GB, "
    f"Energy Consumption: {dag.nodes[node]['energy_consumption']:.2f} Watts"
    for node in dag.nodes
}

edge_properties = {
    (edge[0], edge[1]): f"Latency: {dag.edges[edge]['latency']:.2f} ms, "
                       f"Bandwidth: {dag.edges[edge]['bandwidth']:.2f} Mbps, "
                       f"Distance: {dag.edges[edge]['distance']:.2f} km"
    for edge in dag.edges
}

# Create Pyvis network
g = Network(notebook=True)

# Set physics options to avoid overlap
g.force_atlas_2based()

# Add nodes and edges
for node, properties in node_properties.items():
    node_type = dag.nodes[node]["type"]
    color = (
        "green"
        if node_type == "EdgeTask"
        else "blue"
        if node_type == "FogTask"
        else "purple"
    )
    g.add_node(node, title=properties, color=color)

for edge, properties in edge_properties.items():
    g.add_edge(edge[0], edge[1], title=properties)

g.show("docs/dag.html")

# Export the DAG to JSON format
dag_json = nx.node_link_data(dag)

# Save the JSON to a file
with open("docs/dag_model.json", "w") as json_file:
    json.dump(dag_json, json_file)
