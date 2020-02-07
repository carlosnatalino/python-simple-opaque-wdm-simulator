import logging


def arrival(env, service):
    # logging.debug('Processing arrival {} for policy {} load {} seed {}'.format(service.service_id, env.policy, env.load, env.seed))
    paths = env.topology.graph['ksp'][service.source, service.destination]
    success, id_path = env.policy.route(service, paths)

    if success:
        service.route = paths[id_path]
        env.provision_path(service)
    else:
        env.reject_service(service)

    env.setup_next_arrival() # schedules next arrival


def departure(env, service):
    env.release_path(service)