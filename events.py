import logging

import heuristics


def arrival(env, service):
    # logging.debug('Processing arrival {} for policy {} load {} seed {}'.format(service.service_id, env.policy, env.load, env.seed))
    paths = env.topology.graph['ksp'][service.source, service.destination]
    if env.policy == 'SP': # shortest available path
        success, id_path = heuristics.shortest_path(env, service, paths)
    elif env.policy == 'LB': # load balancing
        success, id_path = heuristics.load_balancing(env, service, paths)
    else:
        raise ValueError('Policy was not configured correctly (value set to {})'.format(env.policy))

    if success:
        service.route = paths[id_path]
        env.provision_path(service)
    else:
        env.reject_service(service)

    env.setup_next_arrival() # schedules next arrival


def departure(env, service):
    env.release_path(service)