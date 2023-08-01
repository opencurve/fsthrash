"""
Exececute custom commands
"""
import logging

from thrash import misc as thrash

log = logging.getLogger(__name__)

def task(ctx, config):
    """
    Execute commands on a given role

        tasks:
        - exec:
            - "echo ' ' > /sys/kernel/debug/dynamic_debug/control"
            - "echo '' > /sys/kernel/debug/dynamic_debug/control"

    It stops and fails with the first command that does not return on success. It means
    that if the first command fails, the second won't run at all.

    :param ctx: Context
    :param config: Configuration
    """
    log.info('Executing custom commands...')
    assert isinstance(config, dict), "task exec got invalid config"

    testdir = get_testdir(ctx)

    for role, ls in config.items():
        (remote,) = ctx.cluster.only(role).remotes.keys()
        log.info('Running commands on role %s host %s', role, remote.name)
        for c in ls:
            c.replace('$TESTDIR', testdir)
            remote.run(
                args=[
                    'sudo',
                    'TESTDIR={tdir}'.format(tdir=testdir),
                    'bash',
                    '-c',
                    c],
                )

