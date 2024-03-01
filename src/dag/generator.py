import networkx as nx
import random


def generate_tasks_from_config(task_names, task_type, regions, config):
    tasks = {}
    ram_values = [2, 4, 8, 16, 32]
    for task_name in task_names:
        region = random.choice(regions)
        tasks[task_name] = {
            "type": task_type,
            "region": region,
            "computational_requirements": {
                "cpu_ghz": random.uniform(*config["cpu_ghz_range"]),
                "memory_gb": random.uniform(*config["memory_gb_range"]),
                "ram_gb": random.choice(ram_values),
            },
        }
    return tasks


def generate_edges_from_config(source_tasks, target_tasks, config):
    edges = []
    if target_tasks:
        target_task_keys = list(target_tasks.keys())
        for source_task in source_tasks:
            for target_task in random.sample(
                target_task_keys, random.randint(1, len(target_task_keys))
            ):
                edge = (
                    source_task,
                    target_task,
                    {
                        "latency_ms": random.uniform(
                            *config.get("latency_ms_range", (50, 100))
                        ),
                        "bandwidth_mbps": random.uniform(
                            *config.get("bandwidth_mbps_range", (1, 10))
                        ),
                        "distance_km": random.uniform(
                            *config.get("distance_km_range", (500, 1000))
                        ),
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

    edge_task_names = [f"Edge_Task_{i+1}" for i in range(config["edge"]["number"])]
    cloud_task_names = [f"Cloud_Task_{i+1}" for i in range(config["cloud"]["number"])]
    fog_task_names = [f"Fog_Task_{i+1}" for i in range(config["fog"]["number"])]

    edge_tasks = generate_tasks_from_config(
        task_names=edge_task_names,
        task_type="EdgeTask",
        regions=regions,
        config=config["edge"]["computational"],
    )

    cloud_tasks = generate_tasks_from_config(
        task_names=cloud_task_names,
        task_type="CloudTask",
        regions=regions,
        config=config["cloud"]["computational"],
    )

    fog_tasks = generate_tasks_from_config(
        task_names=fog_task_names,
        task_type="FogTask",
        regions=regions,
        config=config["fog"]["computational"],
    )

    dag.add_nodes_from(list(edge_tasks.items()) + list(cloud_tasks.items()) + list(fog_tasks.items()))

    # Generate edges from cloud to fog
    cloud_fog_edges = generate_edges_from_config(cloud_tasks, fog_tasks, config['cloud']['links'])
    dag.add_edges_from(cloud_fog_edges)

    # Generate edges from fog to edge
    fog_edge_edges = generate_edges_from_config(fog_tasks, edge_tasks, config['fog']['links'])
    dag.add_edges_from(fog_edge_edges)

    return dag