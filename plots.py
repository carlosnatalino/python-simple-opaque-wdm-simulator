import time
import datetime
import logging
import numpy as np
# mpl.use('agg') #TODO: for use in the command-line-only (no GUI) server
from matplotlib import rcParams
# rcParams['font.family'] = 'sans-serif'
# rcParams['font.sans-serif'] = ['Times New Roman', 'Times']
# rcParams['font.size'] = 24

import matplotlib.pyplot as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)


def plot_simulation_progress(env):
    """
    Plots results for a particular configuration.
    """
    plt.figure(figsize=(10, 4))

    plt.subplot(1, 2, 1)
    if any(i > 0 for i in env.tracked_results['request_blocking_ratio']):
        plt.semilogy([x * env.track_stats_every for x in range(1, len(env.tracked_results['request_blocking_ratio'])+1)],
                 env.tracked_results['request_blocking_ratio'])
    plt.xlabel('Arrival')
    plt.ylabel('Req. blocking ratio')

    plt.subplot(1, 2, 2)
    plt.plot([x * env.track_stats_every for x in range(1, len(env.tracked_results['average_link_usage'])+1)],
                 env.tracked_results['average_link_usage'])
    plt.xlabel('Arrival')
    plt.ylabel('Avg. link usage')

    plt.tight_layout()
    # plt.show()
    for format in env.plot_formats:
        plt.savefig('./results/{}/progress_{}_{}_{}.{}'.format(env.output_folder,
                                                               env.policy, env.load, env.id_simulation, format))
    plt.close()


def plot_final_results(env, results, start_time):
    """
    Consolidates the statistics and plots it periodically and at the end of all simulations.
    """
    fig = plt.figure(figsize=(10, 4))
    markers = ['', 'x']

    plt.subplot(1, 2, 1)
    for idp, policy in enumerate(results):
        if any(results[policy][load][x]['request_blocking_ratio'] > 0 for load in results[policy] for x in range(len(results[policy][load]))):
            plt.semilogy([load for load in results[policy]],
            [np.mean([results[policy][load][x]['request_blocking_ratio'] for x in range(len(results[policy][load]))])
             for load in results[policy]], label=policy, marker=markers[idp])
    plt.xlabel('Load [Erlang]')
    plt.ylabel('Req. blocking ratio')

    plt.subplot(1, 2, 2)
    has_data = False
    for idp, policy in enumerate(results):
        if any(results[policy][load][x]['average_link_usage'] > 0 for load in results[policy] for x in range(len(results[policy][load]))):
            has_data = True
            plt.plot([load for load in results[policy]],
                [np.mean([results[policy][load][x]['average_link_usage'] for x in range(len(results[policy][load]))]) for
                load in results[policy]], label=policy, marker=markers[idp])
    plt.xlabel('Load [Erlang]')
    plt.ylabel('Avg. link usage')
    if has_data:
        plt.legend(loc=2)

    plt.tight_layout()

    total_simulations = np.sum([1 for p in results for l in results[p]]) * env.num_seeds
    performed_simulations = np.sum([len(results[p][l]) for p in results for l in results[p]])
    plt.text(0.01, 0.02, 'Progress: {} out of {} ({:.3f} %) / {}'.format(performed_simulations,
                                                         total_simulations,
                                                         float(performed_simulations) / float(
                                                             total_simulations) * 100.,
                                                        datetime.timedelta(seconds=(time.time() - start_time))),
                                                        transform=fig.transFigure,
                                                        fontsize=rcParams['font.size'] - 6.)

    for format in env.plot_formats:
        plt.savefig('./results/{}/final_results.{}'.format(env.output_folder, format))
    plt.close()