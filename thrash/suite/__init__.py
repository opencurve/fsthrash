import logging
import os
import random
import time
from distutils.util import strtobool

#import fsthrash
from thrash.config import config, YamlConfig
#from thrash.report import ResultsReporter
from thrash.results import build_email_body 

from thrash.suite.run import Run
#from thrash.suite.util import schedule_fail

log = logging.getLogger(__name__)


def process_args(args):
    conf = YamlConfig()
    for (key, value) in args.items():
        # Translate --suite-dir to suite_dir
        key = key.lstrip('--').replace('-', '_')
        if key == 'debug' and value is None:
            value = True
        elif key in ('filter_all', 'filter_in', 'filter_out', 'rerun_statuses'):
            if not value:
                value = []
            else:
                value = [x.strip() for x in value.split(',')]
        if key == 'numjobs':
            conf[key] = int(value)
        else:
            conf[key] = value
    return conf


def normalize_suite_name(name):
    return name.replace('/', ':')

def main(args):
    conf = process_args(args)
    if conf.debug:
        fsthrash.log.setLevel(logging.DEBUG)
#    log.info("now conf is %s",conf)
    run = Run(conf)
    name = run.name
    run.prepare_and_schedule()
    if not conf.dry_run and conf.wait:
        return wait(name, config.max_job_time,
                    conf.archive_upload_url)
    jobs_info = build_email_body(name,run.args.log_dir)
    print jobs_info[0]
    print jobs_info[1]

def get_rerun_filters(name, statuses):
    reporter = ResultsReporter()
    run = reporter.get_run(name)
    filters = dict()
    filters['suite'] = run['suite']
    jobs = []
    for job in run['jobs']:
        if job['status'] in statuses:
            jobs.append(job)
    filters['descriptions'] = [job['description'] for job in jobs if job['description']]
    return filters



class WaitException(Exception):
    pass


def wait(name, max_job_time, upload_url):
    stale_job = max_job_time + Run.WAIT_MAX_JOB_TIME
    reporter = ResultsReporter()
    past_unfinished_jobs = []
    progress = time.time()
    log.debug("the list of unfinished jobs will be displayed "
              "every " + str(Run.WAIT_PAUSE / 60) + " minutes")
    exit_code = 0
    while True:
        jobs = reporter.get_jobs(name, fields=['job_id', 'status'])
        unfinished_jobs = []
        for job in jobs:
            if job['status'] in UNFINISHED_STATUSES:
                unfinished_jobs.append(job)
            elif job['status'] != 'pass':
                exit_code = 1
        if len(unfinished_jobs) == 0:
            log.info("wait is done")
            break
        if (len(past_unfinished_jobs) == len(unfinished_jobs) and
                time.time() - progress > stale_job):
            raise WaitException(
                "no progress since " + str(config.max_job_time) +
                " + " + str(Run.WAIT_PAUSE) + " seconds")
        if len(past_unfinished_jobs) != len(unfinished_jobs):
            past_unfinished_jobs = unfinished_jobs
            progress = time.time()
        time.sleep(Run.WAIT_PAUSE)
        job_ids = [job['job_id'] for job in unfinished_jobs]
        log.debug('wait for jobs ' + str(job_ids))
    jobs = reporter.get_jobs(name, fields=['job_id', 'status',
                                           'description', 'log_href'])
    # dead, fail, pass : show fail/dead jobs first
    jobs = sorted(jobs, key=lambda x: x['status'])
    return exit_code
