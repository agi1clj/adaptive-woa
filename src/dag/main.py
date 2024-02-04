from pyvis.network import Network
import json
from generator import generate_dag_from_config
import networkx as nx
import os
import yaml 

def load_configuration(file_path):
    with open(file_path, 'r') as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

def set_node_properties(dag):
    return {
        node: (
            f"{node}, Type: {dag.nodes[node]['type']}, Region: {dag.nodes[node]['region']}, "
            f"CPU: {dag.nodes[node]['computational_requirements']['cpu_ghz']:.2f} GHz, "
            f"Memory: {dag.nodes[node]['computational_requirements']['memory_gb']:.2f} GB, "
            f"Ram: {dag.nodes[node]['computational_requirements']['ram_gb']:.2f} GB"
        )
        if dag.nodes[node]['type'] == 'CloudTask'
        else (
            f"{node}, Type: {dag.nodes[node]['type']}, Region: {dag.nodes[node]['region']}, "
            f"CPU: {dag.nodes[node]['computational_capacity']['cpu_ghz']:.2f} GHz, "
            f"Memory: {dag.nodes[node]['computational_capacity']['memory_gb']:.2f} GB, "
            f"Ram: {dag.nodes[node]['computational_capacity']['ram_gb']:.2f} GB"
        )
        for node in dag.nodes
    }

def set_edge_properties(dag):
    return {
        (edge[0], edge[1]): f"Latency: {dag.edges[edge]['latency_ms']:.2f} ms, "
                           f"Bandwidth: {dag.edges[edge]['bandwidth_mbps']:.2f} Mbps, "
                           f"Distance: {dag.edges[edge]['distance_km']:.2f} km"
        for edge in dag.edges
    }

def add_nodes_to_graph(g, node_properties):
    for node, properties in node_properties.items():
        node_type = dag.nodes[node]["type"]
        color = "green" if node_type == "EdgeTask" else "blue"
        g.add_node(node, title=properties, color=color)

def add_edges_to_graph(g, edge_properties):
    for edge, properties in edge_properties.items():
        g.add_edge(edge[0], edge[1], title=properties)

def visualize_graph(g, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    g.show(os.path.join(output_folder, "dag.html"))

def export_json(dag, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    dag_json = nx.node_link_data(dag)
    with open(os.path.join(output_folder, "dag_model.json"), "w") as json_file:
        json.dump(dag_json, json_file, indent=2)

# Load configuration files
config_files = ['src/dag/config/dag_small.yaml', 'src/dag/config/dag_medium.yaml', 'src/dag/config/dag_large.yaml']

for config_file in config_files:
    config = load_configuration(config_file)

    # Generate the DAG
    dag = generate_dag_from_config(config)

    # Set node attributes for hover text
    node_properties = set_node_properties(dag)
    edge_properties = set_edge_properties(dag)

    g = Network(notebook=True)
    g.force_atlas_2based()

    # Add nodes and edges
    add_nodes_to_graph(g, node_properties)
    add_edges_to_graph(g, edge_properties)

    # Visualize the graph and export JSON
    output_folder = os.path.join("docs", os.path.splitext(os.path.basename(config_file))[0])
    visualize_graph(g, output_folder)
    export_json(dag, output_folder)