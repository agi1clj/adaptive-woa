import networkx as nx
import random


generate_random_coordinates_decimal = lambda: (random.uniform(-90, 90), random.uniform(-180, 180))

def generate_nodes_from_config(node_names, node_type, regions, config):
    nodes = {}
    ram_values = [2, 4, 8, 16, 32]
    for node_name in node_names:
        region = random.choice(regions)
        latitude, longitude = generate_random_coordinates_decimal()
        nodes[node_name] = {
            "type": node_type,
            "region": region,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "computational_requirements": {
                "cpu_ghz": random.uniform(*config["cpu_ghz_range"]),
                "memory_gb": random.uniform(*config["memory_gb_range"]),
                "ram_gb": random.choice(ram_values),
            },
        }
    return nodes


def generate_edges_from_config(source_nodes, target_nodes, config):
    edges = []
    if target_nodes:
        target_node_keys = list(target_nodes.keys())
        for source_node in source_nodes:
            for target_node in random.sample(
                target_node_keys, random.randint(1, len(target_node_keys))
            ):
                edge = (
                    source_node,
                    target_node,
                    {
                        "latency_ms": round(random.uniform(
                            *config.get("latency_ms_range", (50, 100))
                        ), 2),
                        "bandwidth_mbps": round(random.uniform(
                            *config.get("bandwidth_mbps_range", (1, 10))
                        ), 2),
                        "distance_km": round(random.uniform(
                            *config.get("distance_km_range", (500, 1000))
                        ), 2),
                    },
                )
                edges.append(edge)
    return edges


def generate_dag_from_config(config):
    dag = nx.DiGraph()

    regions = [
        "North America",
        "Europe",
        "Asia",
        "Australia",
        "South America",
        "Africa",
        "Middle East",
    ]

    edge_node_names = [f"Edge_node_{i+1}" for i in range(config["edge"]["number"])]
    cloud_node_names = [f"Cloud_node_{i+1}" for i in range(config["cloud"]["number"])]
    fog_node_names = [f"Fog_node_{i+1}" for i in range(config["fog"]["number"])]

    edge_nodes = generate_nodes_from_config(
        node_names=edge_node_names,
        node_type="EdgeNode",
        regions=regions,
        config=config["edge"]["computational"],
    )

    cloud_nodes = generate_nodes_from_config(
        node_names=cloud_node_names,
        node_type="CloudNode",
        regions=regions,
        config=config["cloud"]["computational"],
    )

    fog_nodes = generate_nodes_from_config(
        node_names=fog_node_names,
        node_type="FogNode",
        regions=regions,
        config=config["fog"]["computational"],
    )

    dag.add_nodes_from(
        list(edge_nodes.items()) + list(cloud_nodes.items()) + list(fog_nodes.items())
    )

    # Generate edges from cloud to fog
    cloud_fog_edges = generate_edges_from_config(
        cloud_nodes, fog_nodes, config["cloud"]["links"]
    )
    dag.add_edges_from(cloud_fog_edges)

    # Generate edges from fog to edge
    fog_edge_edges = generate_edges_from_config(
        fog_nodes, edge_nodes, config["fog"]["links"]
    )
    dag.add_edges_from(fog_edge_edges)

    return dag
