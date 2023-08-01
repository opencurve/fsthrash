import os
import yaml
import sys
import logging
import time

import thrash
from thrash.job_status import get_status
from thrash.misc import  merge_configs
from thrash.run_tasks import run_tasks
from thrash.results import email_results
from thrash.config import FakeNamespace

log = logging.getLogger(__name__)


def set_up_logging(archive,name,debug=False):
    if debug:
        thrash.log.setLevel(logging.DEBUG)
    name = name + '.log'
    thrash.setup_log_file(os.path.join(archive,name))



def setup_config(config_paths):
    """
    Takes a list of config yaml files and combines them
    into a single dictionary. Processes / validates the dictionary and then
    returns it.
    """
    config = merge_configs(config_paths)

    job_id = config.get('job_id')
    if job_id is not None:
        job_id = str(job_id)
        config['job_id'] = job_id

    # targets must be >= than roles
    if 'targets' in config and 'roles' in config:
        targets = len(config['targets'])
        roles = len(config['roles'])
        assert targets >= roles, \
            '%d targets are needed for all roles but found %d listed.' % (
                roles, targets)

    return config


def get_summary(description):
    summary = dict(success=True)
#    summary['failure_reason'] = 'none'
    summary['status'] = 'running'
    summary['duration'] = 0
    summary['starttime'] = time.time()
    if description is not None:
        summary['description'] = description

    return summary

def validate_tasks(config):
    if 'tasks' not in config:
        log.warning('No tasks specified. Continuing anyway...')
        # return the default value for tasks
        return []
    msg = "Expected list in 'tasks'; instead got: {0}".format(config['tasks'])
    assert isinstance(config['tasks'], list), msg
    return config["tasks"]

def report_outcome(config, archive, summary, end=False):
    """ Reports on the final outcome of the command. """
    if archive is not None:
        yaml_name = 'summary.yaml'
        with open(os.path.join(archive, yaml_name), 'w') as f:
            yaml.safe_dump(summary, f, default_flow_style=False)

    summary_dump = yaml.safe_dump(summary)
    log.info('Summary data:\n%s' % summary_dump)

    config_dump = yaml.safe_dump(config)
    yaml_conf_name = 'config.yaml'
    with open(os.path.join(archive, yaml_conf_name), 'w') as f:
        yaml.safe_dump(config, f)
    if end:
        status = get_status(summary)
        passed = status == 'pass'
        if passed:
            log.info(status)
        else:
            log.info(str(status).upper())
            sys.exit(1)

def get_fsthrash_command(args):
    """
    Rebuilds the fsthrash command used to run this job
    and returns it as a string.
    """
    cmd = ["fsthrash"]
    for key, value in args.items():
        if value:
            # an option, not an argument
            if not key.startswith("<"):
                cmd.append(key)
            else:
                # this is the <config> argument
                for arg in value:
                    cmd.append(str(arg))
                continue
            if isinstance(value, str):
                cmd.append(value)
    return " ".join(cmd)

def runtask(args,jobargs):
    suite_path = args.suite_path
    name = jobargs['name']
    testdir = args.testdir
    debug = args.debug
    archive = jobargs['log_archive']
    description = jobargs['desc']
    log.info("archive is aaaa %s"%archive)
#    set_up_logging(archive,name,debug)
    args["summary"] = get_summary(description)
    log.info("args summary is %s"%args.summary)
    # print the command being ran
    log.debug("Fsthrash command: {0}".format(get_fsthrash_command(args)))

    config = jobargs['yaml']
    log.info("jid is %s,jobargs is %s"%(jobargs["job_id"],jobargs))
    args["job_id"] = jobargs["job_id"]
    print "-----------------------------------"
#    report.try_push_job_info(config, dict(status='running'))

    log.info(
        '\n  '.join(['Config:', ] + yaml.safe_dump(
            config, default_flow_style=False).splitlines()))

    config["tasks"] = validate_tasks(config)
    config['archive'] = archive

    if suite_path is not None:
        config['suite_path'] = suite_path


    args["<config>"] = config
    fake_ctx = FakeNamespace(args)

    try:
        report_outcome(jobargs, archive, fake_ctx.summary)
        run_tasks(tasks=config['tasks'], ctx=fake_ctx)
    finally:
        log.info("send results ......")
        duration = time.time() - fake_ctx.summary['starttime']
        fake_ctx.summary['duration'] = duration
        # print to stdout the results and possibly send an email on any errors
        report_outcome(jobargs, archive, fake_ctx.summary, end=True)
        return fake_ctx

