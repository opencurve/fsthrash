import logging
import time
import pipes
import os
import re
import shlex


from thrash import misc
from thrash.parallel import parallel

log = logging.getLogger(__name__)

def task(ctx, config):
    """
    example::
        tasks:
        - aitraining:
            clients:
              dir.1:
                - max_epochs:5

    """
    try:
        timeout = config.get('timeout', '3h')
        log.info("ctx is %s,config is %s"%(ctx,config))
        dir_list = {}
        testdir = ctx['testdir']
        i = 1
        for t in testdir:
            dir_name = 'dir.' + str(i)
            dir_list[dir_name] = t
            i += 1
        log.info("ctx testdir is %s"%testdir)
        log.info('dir_list is  %s', dir_list)
        clients = config['clients']
        log.info("clients is %s"%clients)
        for role in clients.keys():
            assert isinstance(role, str)
            log.info("role is %s"%role)
            if role == "all":
                continue
    except:
        raise
    log.info('**************************************************')
    log.info('Started task test -- %s' % ctx['summary']['description'])
    log.info('**************************************************')
#    with parallel() as p:
#        for role, cfg in clients.items():
#            p.spawn(_run_training, ctx, role, cfg,
#                        basedir=ctx.get('basedir','workunits'),
#                        testpath=dir_list[role],
#                        timeout=timeout)
    for role, cfg in clients.items():
        _run_training(ctx, role, cfg,basedir=ctx.get('basedir','workunits'),testpath=dir_list[role])

def _run_training(ctx,  role, cfg, basedir, testpath, timeout=None):
    try:
        epochs = cfg.get('max_epochs',5)
        cmd = 'cd ' + testpath + ' && ' + 'rm -rf ai' + '&&' + ' virtualenv ai'
        misc.sh(cmd)
        spec = 'training.py'
        srcfile = '{basedir}/{spec}'.format(basedir=basedir,spec=spec)
        des = '{testpath}/ai'.format(testpath=testpath)
        cmd = 'cp ' + srcfile + ' ' + des
        misc.sh(cmd)
        cmd = 'cd ' + des + ' && ' + 'source bin/activate' + ' && pip3 install torch torchvision --timeout 3600'
        misc.sh(cmd)
        cmd = 'cd ' + des + ' && ' + 'source bin/activate' + ' && ' +'python3 training.py ' + str(epochs)
        misc.sh(cmd)
    finally:
        log.info('Stopping training on %s...', role)
