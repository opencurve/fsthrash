import beanstalkc
import yaml
import logging
import pprint
import sys
from collections import OrderedDict

from thrash.config import config

log = logging.getLogger(__name__)
yaml.warnings({'YAMLLoadWarning': False})

def connect():
    host = config.queue_host
    port = config.queue_port
    if host is None or port is None:
        raise RuntimeError(
            'Beanstalk queue information not found in {conf_path}'.format(
                conf_path=config.fsthrash_yaml))
    return beanstalkc.Connection(host=host, port=port)


def watch_tube(connection, tube_name):
    if ',' in tube_name:
        tube_name = 'fsthrash'
    connection.watch(tube_name)
    connection.ignore('default')
    return tube_name

def peek_bury_job(connection):
    job = connection.peek_buried()
    return job


def walk_jobs(connection, tube_name, processor, pattern=None):
    """
    def callback(jobs_dict)
    """
    log.info("Checking Beanstalk Queue...")
    job_count = connection.stats_tube(tube_name)['current-jobs-ready']
    if job_count == 0:
        log.info('No jobs in Beanstalk Queue')
        return

    # Try to figure out a sane timeout based on how many jobs are in the queue
    timeout = job_count / 2000.0 * 60
    for i in range(1, job_count + 1):
        print_progress(i, job_count, "Loading")
        job = connection.reserve(timeout=timeout)
        if job is None or job.body is None:
            continue
        job_config = yaml.safe_load(job.body,loader=yaml.FullLoader)
        job_name = job_config['name']
        job_id = job.stats()['id']
        if pattern is not None and pattern not in job_name:
            continue
        processor.add_job(job_id, job_config, job)
    end_progress()
    processor.complete()


def print_progress(index, total, message=None):
    msg = "{m} ".format(m=message) if message else ''
    sys.stderr.write("{msg}{i}/{total}\r".format(
        msg=msg, i=index, total=total))
    sys.stderr.flush()


def end_progress():
    sys.stderr.write('\n')
    sys.stderr.flush()


class JobProcessor(object):
    def __init__(self):
        self.jobs = OrderedDict()

    def add_job(self, job_id, job_config, job_obj=None):
        job_id = str(job_id)

        job_dict = dict(
            index=(len(self.jobs) + 1),
            job_config=job_config,
        )
        if job_obj:
            job_dict['job_obj'] = job_obj
        self.jobs[job_id] = job_dict

        self.process_job(job_id)

    def process_job(self, job_id):
        pass

    def complete(self):
        pass


class JobPrinter(JobProcessor):
    def __init__(self, show_desc=False, full=False):
        super(JobPrinter, self).__init__()
        self.show_desc = show_desc
        self.full = full

    def process_job(self, job_id):
        job_config = self.jobs[job_id]['job_config']
        job_index = self.jobs[job_id]['index']
        job_name = job_config['name']
        job_desc = job_config['des']
        print('Job: {i:>4} priority: {pri:>4} {job_name}/{job_id}'.format(
            i=job_index,
            pri=job_priority,
            job_id=job_id,
            job_name=job_name,
            ))
        if self.full:
            pprint.pprint(job_config)
        elif job_desc and self.show_desc:
            for desc in job_desc.split():
                print('\t {}'.format(desc))


class RunPrinter(JobProcessor):
    def __init__(self):
        super(RunPrinter, self).__init__()
        self.runs = list()

    def process_job(self, job_id):
        run = self.jobs[job_id]['job_config']['name']
        if run not in self.runs:
            self.runs.append(run)
            print(run)


def pause_tube(connection, tube, duration):
    duration = int(duration)
    if not tube:
        tubes = sorted(connection.tubes())
    else:
        tubes = [tube]

    prefix = 'Unpausing' if duration == 0 else "Pausing for {dur}s"
    templ = prefix + ": {tubes}"
    log.info(templ.format(dur=duration, tubes=tubes))
    for tube in tubes:
        connection.pause_tube(tube, duration)

def stats_tube(connection, tube):
    stats = connection.stats_tube(tube)
    result = dict(
        name=tube,
        count=stats['current-jobs-ready'],
        paused=(stats['pause'] != 0),
    )
    return result

def main(args):
    tube = args['--tube']
    status = args['--status']
    try:
        connection = connect()
        if machine_type:
            watch_tube(connection, machine_type)
        if status:
            print(stats_tube(connection, machine_type))
        else:
            walk_jobs(connection, machine_type,
                      JobPrinter(show_desc=show_desc, full=full))
    except KeyboardInterrupt:
        log.info("Interrupted.")
    finally:
        connection.close()
