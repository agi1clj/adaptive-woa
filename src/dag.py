import networkx as nx
from pyvis.network import Network
import random
import json


def generate_dag():
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

    # Add edge tasks
    edge_task_names = [f"Edge_Task_{i}" for i in range(10)]
    for task_name in edge_task_names:
        edge_provider = random.choice(
            ["Cluj-MdC-01", "Sibiu-MdC-02", "Timisoara-MdC-03"]
        )
        dag.add_node(
            task_name,
            type="EdgeTask",
            region="eu-central-1",
            provider=edge_provider,
            data_volume=random.uniform(1, 10),  # in GB
            computational_requirements={
                "CPU": random.uniform(5, 10),
                "Memory": random.uniform(10, 20),
            },  # in GHz, GB
            latency=random.uniform(1, 5),  # in ms
            bandwidth=random.uniform(5, 10),  # in Mbps
            energy_consumption=random.uniform(20, 40),
        )  # in Watts

    # Add fog tasks
    fog_task_names = [f"Fog_Task_{i}" for i in range(5)]
    for task_name in fog_task_names:
        fog_provider = random.choice(["Cluj-DC-01", "Brasov-DC-02", "Bucuresti-DC-03"])
        dag.add_node(
            task_name,
            type="FogTask",
            region="eu-central-1",
            provider=fog_provider,
            data_volume=random.uniform(10, 50),  # in GB
            computational_requirements={
                "CPU": random.uniform(10, 30),
                "Memory": random.uniform(30, 50),
            },  # in GHz, GB
            latency=random.uniform(5, 10),  # in ms
            bandwidth=random.uniform(10, 20),  # in Mbps
            energy_consumption=random.uniform(30, 60),
        )  # in Watts

    # Add cloud tasks
    cloud_task_names = [f"Cloud_Task_{i}" for i in range(5)]
    for task_name in cloud_task_names:
        region = random.choice(aws_regions)
        provider = random.choice(["AWS", "Azure", "Heroku", "GCP"])
        dag.add_node(
            task_name,
            type="CloudTask",
            region=region,
            provider=provider,
            data_volume=random.uniform(50, 100),  # in GB
            computational_requirements={
                "CPU": random.uniform(30, 50),
                "Memory": random.uniform(50, 100),
            },  # in GHz, GB
            latency=random.uniform(10, 20),  # in ms
            bandwidth=random.uniform(20, 30),  # in Mbps
            energy_consumption=random.uniform(60, 80),
        )  # in Watts

    # Connect tasks based on the architecture with selective links
    for edge_task in edge_task_names:
        # Connect edge tasks to a random subset of fog tasks
        for fog_task in random.sample(
            fog_task_names, random.randint(1, len(fog_task_names))
        ):
            dag.add_edge(edge_task, fog_task)

    for fog_task in fog_task_names:
        # Connect fog tasks to a random subset of cloud tasks
        for cloud_task in random.sample(
            cloud_task_names, random.randint(1, len(cloud_task_names))
        ):
            dag.add_edge(fog_task, cloud_task)

    return dag


# Generate the DAG
dag = generate_dag()

# Set node attributes for hover text
node_properties = {
    node: f"{node}, Type: {dag.nodes[node]['type']}, Region: {dag.nodes[node]['region']}, "
    f"Provider: {dag.nodes[node]['provider']}, "
    f"Data Volume: {dag.nodes[node]['data_volume']:.2f} GB, "
    f"CPU: {dag.nodes[node]['computational_requirements']['CPU']:.2f} GHz, "
    f"Memory: {dag.nodes[node]['computational_requirements']['Memory']:.2f} GB, "
    f"Latency: {dag.nodes[node]['latency']:.2f} ms, "
    f"Bandwidth: {dag.nodes[node]['bandwidth']:.2f} Mbps, "
    f"Energy Consumption: {dag.nodes[node]['energy_consumption']:.2f} Watts"
    for node in dag.nodes
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

for edge in dag.edges:
    g.add_edge(edge[0], edge[1])

g.show("docs/dag.html")
# Export the DAG to JSON format
dag_json = nx.node_link_data(dag)

# Save the JSON to a file
with open("docs/dag_model.json", "w") as json_file:
    json.dump(dag_json, json_file)
