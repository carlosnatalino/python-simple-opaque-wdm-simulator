import abc
import numpy as np


class RoutingPolicy(abc.ABC):

    def __init__(self):
        self.env = None
        self.name = None

    @abc.abstractclassmethod
    def route(self, service, paths):
        pass


class ShortestAvailablePath(RoutingPolicy):

    def __init__(self):
        super().__init__()
        self.name = 'SAP'

    def route(self, service, paths):
        """
        Remember that this function considers that the list of paths is ordered by distance, i.e., first path is shortest
        """
        for idp, path in enumerate(paths):
            if is_path_free(self.env.topology, path, service.number_units):
                return True, idp
        return False, self.env.k_paths  # returns false and an index out of bounds if no path is available


class LoadBalancing(RoutingPolicy):

    def __init__(self):
        super().__init__()
        self.name = 'LB'

    def route(self, service, paths):
        """
        Implements load balacing, i.e., selects the path that has the minimum usage.
        """
        selected_path = self.env.k_paths  # initialize the path to an out of bounds, i.e., non-existent
        least_load = np.finfo(0.0).max  # initializes load to the maximum value of a float
        for idp, path in enumerate(paths):
            if is_path_free(self.env.topology, path, service.number_units) and \
                    get_max_usage(self.env.topology, path) < least_load:
                least_load = get_max_usage(self.env.topology, path)
                selected_path = idp
        return selected_path < self.env.k_paths, selected_path


# below we have the helper functions

def is_path_free(topology, path, number_units):
    for i in range(len(path.node_list) - 1):
        if topology[path.node_list[i]][path.node_list[i + 1]]['available_units'] < number_units:
            return False
    return True


def get_max_usage(topology, path):
    """
    Obtains the maximum usage of resources among all the links forming the path
    """
    max_usage = np.finfo(0.0).min
    for i in range(len(path.node_list) - 1):
        max_usage = max(max_usage, topology[path.node_list[i]][path.node_list[i + 1]]['total_units'] - topology[path.node_list[i]][path.node_list[i + 1]]['available_units'])
    return max_usage