import logging
logging.basicConfig(format='%(asctime)s\t%(name)-12s\t%(threadName)s\t%(message)s', level=logging.DEBUG)

import argparse
import copy
import pickle
import datetime
import time
import os
import numpy as np
from multiprocessing import Pool
from multiprocessing import Manager

import core
import graph
import plots


def run(args):
    start_time = time.time()

    topology = graph.get_topology(args)
    env = core.Environment(args, topology=topology)

    logger = logging.getLogger('run')

    # in this case, a configuration changes only the load of the network
    policies = ['SP', 'LB']
    loads = [x for x in range(args.min_load, args.max_load + 1, args.load_step)]

    if not os.path.isdir('./results/' + env.output_folder):
        os.makedirs('./results/' + env.output_folder)
        logger.debug(f'creating folder {env.output_folder}')

    manager = Manager()
    results = manager.dict()
    for policy in policies: # runs the simulations for two policies
        results[policy] = {load: manager.list() for load in loads}

    envs = []
    for policy in policies: # runs the simulations for two policies
        for load in loads:
            env_topology = copy.deepcopy(topology) # makes a deep copy of the topology object
            env_t = core.Environment(args,
                                     topology=env_topology,
                                     results=results,
                                     load=load,
                                     policy=policy,
                                     seed=len(policies) * load)
            envs.append(env_t)
            # code for debugging purposes -- it runs without multithreading
            # if load == 10 and policy == 'LB':
            #     core.run_simulation(env_t)

    logger.debug(f'Starting pool of simulators with {args.threads} threads')
    # use the code above to keep updating the final plot as the simulation progresses
    with Pool(processes=args.threads) as p:
        result_pool = p.map_async(core.run_simulation, envs)
        p.close()

        done = False
        while not done:
            if result_pool.ready():
                done = True
            else:
                time.sleep(args.temporary_plot_every)
                plots.plot_final_results(env, results, start_time)

    # if you do not want periodical updates, you can use the following code
    # with Pool(processes=args.threads) as p:
    #     p.map(core.run_simulation, envs)
    #     p.close()
    #     p.join()
    #     logging.debug("Finished the threads")

    # consolidating statistics
    plots.plot_final_results(env, results, start_time)

    with open('./results/{}/results-final.h5'.format(env.output_folder), 'wb') as file:
        results = dict(results)
        for k,v in results.items():
            results[k] = dict(v);
            for k2,v2 in results[k].items():
                results[k][k2] = list(v2)
        pickle.dump(results, file)

    logger.debug('Finishing simulation after {}'.format(datetime.timedelta(seconds=(time.time() - start_time))))


if __name__ == '__main__':
    env = core.Environment()

    parser = argparse.ArgumentParser()
    parser.add_argument('-tf', '--topology_file', default=env.topology_file, help='Network topology file to be used')
    parser.add_argument('-a', '--num_arrivals', type=int, default=env.num_arrivals,
                        help='Number of arrivals per episode to be generated (default={})'.format(env.num_arrivals))
    parser.add_argument('-k', '--k_paths', type=int, default=env.k_paths,
                        help='Number of k-shortest-paths to be considered (default={})'.format(env.k_paths))
    parser.add_argument('-t', '--threads', type=int, default=env.threads,
                        help='Number of threads to be used to run the simulations (default={})'.format(
                            env.threads))
    parser.add_argument('--min_load', type=int, default=400,
                        help='Load in Erlangs of the traffic generated (mandatory)')
    parser.add_argument('--max_load', type=int, default=1000,
                        help='Load in Erlangs of the traffic generated (mandatory)')
    parser.add_argument('--load_step', type=int, default=150,
                        help='Load in Erlangs of the traffic generated (default: {})'.format(100))
    parser.add_argument('-s', '--seed', type=int, default=env.seed,
                        help='Seed of the random numbers (default={})'.format(env.seed))
    parser.add_argument('-ns', '--num_seeds', type=int, default=env.num_seeds,
                        help='Number of seeds to run for each configuration (default={})'.format(env.num_seeds))
    te = 20
    parser.add_argument('-te', '--temporary_plot_every', type=int, default=te, #TODO: adjust for your needs
                        help='Time interval for plotting intermediate statistics of the simulation in seconds (default={})'.format(te))
    parser.add_argument('-o', '--output_dir', default=env.output_folder,
                        help='Output folder inside results (default={})'.format(env.output_folder))
    args = parser.parse_args()
    run(args)
