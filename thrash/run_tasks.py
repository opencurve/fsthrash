#import jinja2
import logging
import os
import sys
import time
import types
import yaml

from copy import deepcopy
from humanfriendly import format_timespan
#import sentry_sdk

#from thrash.config import config as fsthrash_config
from thrash.exceptions import ConnectionLostError
from thrash.job_status import set_status, get_status
from thrash.timer import Timer

log = logging.getLogger(__name__)


def get_task(name):
    # todo: support of submodules
    if '.' in name:
        module_name, task_name = name.split('.')
    else:
        module_name, task_name = (name, 'task')
    log.info("module_name = %s"%module_name)
    module = _import('thrash.tasks', module_name, task_name)
    log.info("module is %s"%module)
    try:
        task = getattr(module, task_name)
        log.info("task %s"%task)
        # If we get another module, we need to go deeper
        if isinstance(task, types.ModuleType):
            task = getattr(task, task_name)
    except AttributeError:
        log.error("No subtask of '{}' named '{}' was found".format(
            module_name,
            task_name,
        ))
        raise
    return task


def _import(from_package, module_name, task_name, fail_on_import_error=False):
    full_module_name = '.'.join([from_package, module_name])
    log.info("full_module_name is %s"%full_module_name)
    try:
        module = __import__(
            full_module_name,
            globals(),
            locals(),
            [task_name],
            0,
        )
        log.info("module is %s"%module)
    except ImportError:
 #       if fail_on_import_error:
        raise
#        else:
#            return None
    return module


def run_one_task(taskname, **kwargs):
    taskname = taskname.replace('-', '_')
    task = get_task(taskname)
    return task(**kwargs)


def run_tasks(tasks, ctx):
    archive_path = ctx.config.get('archive')
    if archive_path:
        timer = Timer(
            path=os.path.join(archive_path, 'timing.yaml'),
            sync=True,
        )
    else:
        timer = Timer()
    stack = []
    set_status(ctx.summary,'running')
    try:
        for taskdict in tasks:
            try:
                ((taskname, config),) = taskdict.items()
            except (ValueError, AttributeError):
                raise RuntimeError('Invalid task definition: %s' % taskdict)
            log.info('Running task %s,config is %s...', taskname,config)
            timer.mark('%s enter' % taskname)
            manager = run_one_task(taskname, ctx=ctx, config=config)
            if hasattr(manager, '__enter__'):
                stack.append((taskname, manager))
                manager.__enter__()
    except BaseException as e:
        if isinstance(e, ConnectionLostError):
            # Prevent connection issues being flagged as failures
            set_status(ctx.summary, 'dead')
        else:
            # the status may have been set to dead, leave it as-is if so
            if not ctx.summary.get('status', '') == 'dead':
                set_status(ctx.summary, 'fail')
        if 'failure_reason' not in ctx.summary:
            print "eeeeeeeeeeeeeeeee:"
            print e
            ctx.summary['failure_reason'] = str(e)
        log.exception('Saw exception from tasks.')


        # fail as before, but with easier to understand error indicators.
        if isinstance(e, ValueError):
            if str(e) == 'too many values to unpack':
                emsg = 'Possible configuration error in yaml file'
                log.error(emsg)
                ctx.summary['failure_info'] = emsg
    finally:
        try:
            exc_info = sys.exc_info()
            while stack:
                taskname, manager = stack.pop()
                log.info('Unwinding manager %s', taskname)
                timer.mark('%s exit' % taskname)
                try:
                    suppress = manager.__exit__(*exc_info)
                    log.info("ctx.summary=%s",ctx.summary)
                except Exception as e:
                    if isinstance(e, ConnectionLostError):
                        # Prevent connection issues being flagged as failures
                        set_status(ctx.summary, 'dead')
                    else:
                        set_status(ctx.summary, 'fail')
                    if 'failure_reason' not in ctx.summary:
                        ctx.summary['failure_reason'] = str(e)
                    log.exception('Manager failed: %s', taskname)

                    if exc_info == (None, None, None):
                        # if first failure is in an __exit__, we don't
                        # have exc_info set yet
                        exc_info = sys.exc_info()
#                else:
#                    if suppress:
#                        exc_info = (None, None, None)

            if exc_info != (None, None, None):
                log.debug('Exception was not quenched, exiting: %s: %s',
                          exc_info[0].__name__, exc_info[1])
                raise SystemExit(1)
            else:
                set_status(ctx.summary,'pass')
        finally:
            if ctx.summary['status'] == 'running':
                set_status(ctx.summary,'pass')
            # be careful about cyclic references
            del exc_info
        timer.mark("tasks complete")

