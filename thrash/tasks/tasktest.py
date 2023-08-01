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
    Task that just displays information when it is create and when it is
    destroyed/cleaned up.  This task was used to test parallel and
    sequential task options.

    example::

        tasks:
        - sequential:
            - tasktest:
                - id: 'foo'
            - tasktest:
                - id: 'bar'
                - delay:5
        - tasktest:

    The above yaml will sequentially start a test task named foo and a test
    task named bar.  Bar will take 5 seconds to complete.  After foo and bar
    have finished, an unidentified tasktest task will run.
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
    with parallel() as p:
        for role, tests in clients.items():
            p.spawn(_run_tests, ctx, role, tests,
                        basedir=ctx.get('basedir','workunits'),
                        testpath=dir_list[role],
                        timeout=timeout)

def _run_tests(ctx,  role, tests, basedir, testpath, timeout=None):
    try:
        assert isinstance(tests, list)
        for spec in tests:
            srcfile = '{testpath}/{basedir}/{spec}'.format(testpath=testpath,basedir=basedir,spec=spec)
            srcdir = os.path.split(srcfile)[0]
            srcfile = os.path.split(srcfile)[1]
#            cmd = 'cp -r {basedir} {testpath}'.format(basedir=basedir,testpath=testpath)
#            misc.sh(cmd)
            cmd = 'cd ' + srcdir + ' && ' + ' chmod +x ' + srcfile + ' && ' + 'bash ' + srcfile
            misc.sh(cmd)
    finally:
        log.info('Stopping %s on %s...', tests, role)
