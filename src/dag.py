import networkx as nx
from pyvis.network import Network
import random
import json


def generate_dag():
    # Create a directed acyclic graph (DAG)
    dag = nx.DiGraph()

    aws_regions = ['eu-west-1', 'eu-west-2', 'eu-central-1', 'eu-west-3', 'eu-north-1', 'eu-south-1', 'eu-west-2']
    azure_regions = ['North Europe', 'West Europe', 'East Europe', 'West US', 'North Central US']


    # Add IoT devices
    num_iot_devices = 5
    for i in range(num_iot_devices):
        dag.add_node(f'IoT_{i}', type='IoT', location='Marcesti, Cluj',
                     data_volume=random.uniform(1, 10),  # in GB
                     computational_requirements={'CPU': random.uniform(0.5, 1), 'Memory': random.uniform(1, 5)},  # in GHz, GB
                     latency=random.uniform(1, 10),  # in ms
                     bandwidth=random.uniform(1, 5),  # in Mbps
                     energy_consumption=random.uniform(10, 50))  # in Watts

    # Add edge devices
    num_edge_devices = 3
    for i in range(num_edge_devices):
        dag.add_node(f'Edge_Server_{i}', type='EdgeServer', location='Marcesti, Cluj',
                     data_volume=random.uniform(10, 50),  # in GB
                     computational_requirements={'CPU': random.uniform(5, 10), 'Memory': random.uniform(10, 20)},  # in GHz, GB
                     latency=random.uniform(5, 15),  # in ms
                     bandwidth=random.uniform(5, 10),  # in Mbps
                     energy_consumption=random.uniform(20, 70))  # in Watts

    # Add fog nodes in a data center
    num_fog_nodes = 2
    for i in range(num_fog_nodes):
        dag.add_node(f'Fog_Openshift_{i}', type='FogNode', location='Cluj-Napoca, Romania',
                     data_volume=random.uniform(50, 100),  # in GB
                     computational_requirements={'CPU': random.uniform(20, 50), 'Memory': random.uniform(50, 100)},  # in GHz, GB
                     latency=random.uniform(10, 30),  # in ms
                     bandwidth=random.uniform(10, 20),  # in Mbps
                     energy_consumption=random.uniform(30, 80))  # in Watts

    # Add cloud nodes from AWS (using EC2 terminology)
    num_aws_cloud_nodes = 2
    for i in range(num_aws_cloud_nodes):
        region = random.choice(aws_regions)
        dag.add_node(f'AWS_Kubernetes_{i}', type='Cloud', provider='AWS', location=region,
                     data_volume=random.uniform(100, 200),  # in GB
                     computational_requirements={'CPU': random.uniform(100, 200), 'Memory': random.uniform(200, 500)},  # in GHz, GB
                     latency=random.uniform(20, 50),  # in ms
                     bandwidth=random.uniform(30, 50),  # in Mbps
                     energy_consumption=random.uniform(50, 100))  # in Watts

    # Add cloud nodes from Azure
    num_azure_cloud_nodes = 2
    for i in range(num_azure_cloud_nodes):
        region = random.choice(azure_regions)
        dag.add_node(f'Azure_Kubernetes_{i}', type='Cloud', provider='Azure', location=region,
                     data_volume=random.uniform(100, 200),  # in GB
                     computational_requirements={'CPU': random.uniform(100, 200), 'Memory': random.uniform(200, 500)},  # in GHz, GB
                     latency=random.uniform(25, 45),  # in ms
                     bandwidth=random.uniform(25, 40),  # in Mbps
                     energy_consumption=random.uniform(45, 90))  # in Watts

    # Add VMs for each fog node
    for fog_node in [f'Fog_Openshift_{i}' for i in range(num_fog_nodes)]:
        num_vms = 5
        for j in range(num_vms):
            dag.add_node(f'{fog_node}_VM_{j}', type='FogNode', location=fog_node,
                         data_volume=random.uniform(10, 30),  # in GB
                         computational_requirements={'CPU': random.uniform(5, 20), 'Memory': random.uniform(10, 50)},  # in GHz, GB
                         latency=random.uniform(5, 15),  # in ms
                         bandwidth=random.uniform(5, 15),  # in Mbps
                         energy_consumption=random.uniform(15, 40))  # in Watts

    # Add containers for each cloud node
    for cloud_node in [f'AWS_Kubernetes_{i}' for i in range(num_aws_cloud_nodes)] + [f'Azure_Kubernetes_{i}' for i in range(num_azure_cloud_nodes)]:
        num_servers = random.randint(5, 10)
        for k in range(num_servers):
            dag.add_node(f'{cloud_node}_Container_{k}', type='Container', location=cloud_node,
                         data_volume=random.uniform(30, 50),  # in GB
                         computational_requirements={'CPU': random.uniform(50, 100), 'Memory': random.uniform(100, 200)},  # in GHz, GB
                         latency=random.uniform(15, 30),  # in ms
                         bandwidth=random.uniform(20, 40),  # in Mbps
                         energy_consumption=random.uniform(40, 80))  # in Watts

    # Connect nodes based on the architecture (edges represent communication links)
    for i in range(num_iot_devices):
        for j in range(num_edge_devices):
            dag.add_edge(f'IoT_{i}', f'Edge_Server_{j}')

    for i in range(num_edge_devices):
        for j in range(num_fog_nodes):
            dag.add_edge(f'Edge_Server_{i}', f'Fog_Openshift_{j}')

    for i in range(num_fog_nodes):
        for j in range(num_aws_cloud_nodes):
            dag.add_edge(f'Fog_Openshift_{i}', f'AWS_Kubernetes_{j}')

    for i in range(num_fog_nodes):
        for j in range(num_azure_cloud_nodes):
            dag.add_edge(f'Fog_Openshift_{i}', f'Azure_Kubernetes_{j}')

    for fog_node in [f'Fog_Openshift_{i}' for i in range(num_fog_nodes)]:
        for vm in [node for node in dag.nodes if 'VM' in node and fog_node in node]:
            dag.add_edge(fog_node, vm)

    for cloud_node in [f'AWS_Kubernetes_{i}' for i in range(num_aws_cloud_nodes)] + [f'Azure_Kubernetes_{i}' for i in range(num_azure_cloud_nodes)]:
        for server in [node for node in dag.nodes if 'Container' in node and cloud_node in node]:
            dag.add_edge(cloud_node, server)

    return dag

# Generate the DAG
dag = generate_dag()
print(dag)

# Set node attributes for hover text
node_properties = {node: f"{node}, Type: {dag.nodes[node]['type']}, Location: {dag.nodes[node]['location']}, "
                              f"Data Volume: {dag.nodes[node]['data_volume']:.2f} GB, "
                              f"CPU: {dag.nodes[node]['computational_requirements']['CPU']:.2f} GHz, "
                              f"Memory: {dag.nodes[node]['computational_requirements']['Memory']:.2f} GB, "
                              f"Latency: {dag.nodes[node]['latency']:.2f} ms, "
                              f"Bandwidth: {dag.nodes[node]['bandwidth']:.2f} Mbps, "
                              f"Energy Consumption: {dag.nodes[node]['energy_consumption']:.2f} Watts"
                   for node in dag.nodes}

# Create Pyvis network
g = Network(notebook=True)

# Set physics options to avoid overlap
g.force_atlas_2based()

# Add nodes and edges
for node, properties in node_properties.items():
    node_type = dag.nodes[node]['type']
    color = 'red' if node_type == 'IoT' else 'green' if node_type == 'EdgeServer' else 'blue' if node_type == 'FogNode' else 'purple'
    g.add_node(node, title=properties, color=color)

for edge in dag.edges:
    g.add_edge(edge[0], edge[1])

g.show("static/dag.html")
# Export the DAG to JSON format
dag_json = nx.node_link_data(dag)

# Save the JSON to a file
with open('static/dag_model.json', 'w') as json_file:
    json.dump(dag_json, json_file)