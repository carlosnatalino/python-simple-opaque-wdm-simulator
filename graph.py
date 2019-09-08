from itertools import islice
import math
from xml.dom.minidom import parse
import xml.dom.minidom
import networkx as nx
import numpy as np
import logging
logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.DEBUG)


def get_k_shortest_paths(G, source, target, k, weight=None):
    """
    Method from https://networkx.github.io/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.shortest_simple_paths.html#networkx.algorithms.simple_paths.shortest_simple_paths
    """
    return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))


def get_path_weight(graph, path, weight='length'):
    return np.sum([graph[path[i]][path[i+1]][weight] for i in range(len(path) - 1)])


class Path:

    def __init__(self, node_list, length):
        self.node_list = node_list
        self.length = length
        self.hops = len(node_list) - 1


def calculate_geographical_distance(latlong1, latlong2):
    R = 6373.0

    lat1 = math.radians(latlong1[0])
    lon1 = math.radians(latlong1[1])
    lat2 = math.radians(latlong2[0])
    lon2 = math.radians(latlong2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    length = R * c
    return length


def read_topology_file(file):
    with open(file, 'r') as nodes_lines:
        for idx, line in enumerate(nodes_lines):
            if line.replace("\n", "") == "1":
                return read_txt_file("topologies/" + file)


def read_txt_file(file):
    graph = nx.Graph()
    num_nodes = 0
    num_links = 0
    with open(file, 'r') as nodes_lines:
        for idx, line in enumerate(nodes_lines):
            if 2 < idx <= num_nodes + 2: # skip title line
                info = line.replace("\n", "").replace(",", ".").split("\t")
                graph.add_node(info[0], name=info[1], pos=(float(info[2]), float(info[3])))
            elif 2 + num_nodes < idx <= 2 + num_nodes + num_links: # skip title line
                info = line.replace("\n", "").split("\t")
                graph.add_edge(info[1], info[2], id=int(info[0]), weight=int(info[3]))
            elif idx == 1:
                num_nodes = int(line)
            elif idx == 2:
                num_links = int(line)

    return graph


def read_simmons_txt(file):
    graph = nx.Graph()
    topology_name = file.split(".")[0]
    nNodes = 0
    nLinks = 0
    with open(file, 'r') as nodes_lines:
        for idx, line in enumerate(nodes_lines):
            if idx > 1 and idx <= nNodes + 1:  # skip title line
                info = line.replace("\n", "").replace(",", ".").split("\t")
                graph.add_node(info[0], name=info[0], pos=(float(info[2]), float(info[1])))
            elif idx > 1 + nNodes and idx <= 1 + nNodes + nLinks:  # skip title line
                info = line.replace("\n", "").split("\t")
                graph.add_edge(info[0], info[1], weight=float(info[2]))
            elif idx == 0:
                nNodes = int(line)
            elif idx == 1:
                nLinks = int(line)
    # printer.print_default_topology(graph, topology_name, axis=False, scale=True)
    return graph


def read_sndlib_topology(file):
    graph = nx.Graph()

    with open('config/topologies/' + file) as file:
        tree = xml.dom.minidom.parse(file)
        document = tree.documentElement

        graph.graph["coordinatesType"] = document.getElementsByTagName("nodes")[0].getAttribute("coordinatesType")

        nodes = document.getElementsByTagName("node")
        for node in nodes:
            x = node.getElementsByTagName("x")[0]
            y = node.getElementsByTagName("y")[0]
            # print(node['id'], x.string, y.string)
            graph.add_node(node.getAttribute("id"), pos=((float(x.childNodes[0].data), float(y.childNodes[0].data))))
        # print("Total nodes: ", graph.number_of_nodes())
        links = document.getElementsByTagName("link")
        for idx, link in enumerate(links):
            source = link.getElementsByTagName("source")[0]
            target = link.getElementsByTagName("target")[0]

            if graph.graph["coordinatesType"] == "geographical":
                length = np.around(calculate_geographical_distance(graph.nodes[source.childNodes[0].data]["pos"], graph.nodes[target.childNodes[0].data]["pos"]), 3)
            else:
                latlong1 = graph.nodes[source.childNodes[0].data]["pos"]
                latlong2 = graph.nodes[target.childNodes[0].data]["pos"]
                length = np.around(math.sqrt((latlong1[0] - latlong2[0]) ** 2 + (latlong1[1] - latlong2[1]) ** 2), 3)

            weight = 1.0
            graph.add_edge(source.childNodes[0].data, target.childNodes[0].data,
                           id=link.getAttribute("id"), weight=weight, length=length, index=idx)
            # print("Edge: ", source.childNodes[0].data, " -> ", target.childNodes[0].data, "\tattrs", graph[source.childNodes[0].data][target.childNodes[0].data])
        # print("Total edges: ", graph.number_of_edges())
    graph.graph["node_indices"] = []
    for idx, node in enumerate(graph.nodes()):
        graph.graph["node_indices"].append(node)
    # for idx, node in enumerate(graph.graph["nodeIndices"]):
    #     print('{} - {}'.format(idx, node))

    # bc = nx.edge_betweenness_centrality(graph)
    # print(bc)

    return graph


def get_topology(args):
    k_shortest_paths = {}
    if args.topology_file.endswith(".xml"):
        topology = read_sndlib_topology(args.topology_file)
    else:
        raise ValueError("Supplied topology is unknown")

    for idn1, n1 in enumerate(topology.nodes()):
        for idn2, n2 in enumerate(topology.nodes()):
            if idn1 < idn2:
                paths = get_k_shortest_paths(topology, n1, n2, args.k_paths)
                # print(n1, n2, len(paths))
                lengths = [get_path_weight(topology, path) for path in paths]
                objs = []
                for path, length in zip(paths, lengths):
                    objs.append(Path(path, length))
                # both directions have the same paths, i.e., bidirectional symetrical links
                k_shortest_paths[n1, n2] = objs
                k_shortest_paths[n2, n1] = objs
                # print(k_shortest_paths[n1,n2])
                # exit(0)
    # exit(0)
    topology.graph["ksp"] = k_shortest_paths
    return topology