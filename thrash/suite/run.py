import copy
import logging
import os
import pwd
import re
import time
import yaml

from humanfriendly import format_timespan

from datetime import datetime
from tempfile import NamedTemporaryFile

import thrash.beanstalk
from thrash import misc
from thrash.config import config, JobConfig
from thrash.worker import worker_start_all
from thrash.suite import util
from thrash.run import runtask
from thrash.suite.build_matrix import build_matrix
from thrash.suite.placeholder import substitute_placeholders, dict_templ

log = logging.getLogger(__name__)


class Run(object):
    WAIT_MAX_JOB_TIME = 120 * 60
    WAIT_PAUSE = 5 * 60

    def __init__(self, args):
        """
        args must be a config.YamlConfig object
        """
        self.args = args
        self.args.tube = 'fsthrash'
        if not self.args.email_to:
            self.args.email_to = config.email_to
        # We assume timestamp is a datetime.datetime object
        self.timestamp = self.args.timestamp or \
            datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        self.args.log_dir = config.log_dir
        self.name = self.make_run_name()
        log.info("name is %s",self.name)

        self.base_config = self.create_initial_config()
        
        self.args.suite_path = os.path.abspath(self.args.suite_path)
        self.suite_path = self.args.suite_path

    def make_run_name(self):
        """
        Generate a run name. A run name looks like:
            fsthrash-2022-11-23_19:00:37-rename-1-testing
        """
        return '-'.join(
            [
                str(self.timestamp),
                self.args.suite_path,
                str(self.args.numjobs),
            ]
        ).replace('/', ':')

    def create_initial_config(self):
        """
        :returns: A JobConfig object
        """
        self.config_input = dict(
            suite=os.path.basename(self.args.suite_path.strip('/')),
            suite_path=self.args.suite_path,
            numjobs=self.args.numjobs,
            testdir=self.args.testdir
        )
        return self.build_base_config()

    def build_base_config(self):
        conf_dict = substitute_placeholders(dict_templ, self.config_input)
        print "*********substitute conf dict *********************"
        print conf_dict
        job_config = JobConfig.from_dict(conf_dict)
        job_config.timestamp = self.timestamp
        if self.args.sleep_before_teardown:
            job_config.sleep_before_teardown = int(self.args.sleep_before_teardown)
        return job_config

    def build_base_args(self):
        base_args = [
            '--name', self.name,
        ]
        return base_args


    def prepare_and_schedule(self):
        self.base_args = self.build_base_args()


        num_jobs = self.schedule_suite()

        if num_jobs:
#            self.write_result()
            log.info("run jobs %d ",num_jobs)
#           print "pass"

    def collect_jobs(self, configs):
        jobs_to_schedule = []
        jobs_missing_packages = []
        for description, fragment_paths in configs:
            raw_yaml = '\n'.join([open(a, 'r').read() for a in fragment_paths])

            parsed_yaml = yaml.safe_load(raw_yaml)
            arg = copy.deepcopy(self.base_args)
            arg.extend([
                '--description', description,
                '--',
            ])
            arg.extend(fragment_paths)

            job = dict(
                yaml=parsed_yaml,
                desc=description,
                args=arg
            )

            jobs_to_schedule.append(job)
        return jobs_missing_packages, jobs_to_schedule
        
    def schedule_job(self,job_config, num=1, report_status=False):
        num = int(num)
        job = yaml.safe_dump(job_config)
        tube = job_config.pop('tube')
        beanstalk = thrash.beanstalk.connect()
        beanstalk.use(tube)
        priority=job_config.get('priority',0)
        while num > 0:
            jid = beanstalk.put(
                job,
                ttr=60 * 60 * 24,
                priority=priority,
            )
            print('Job scheduled with name {name} and ID {jid}'.format(
                name=job_config['name'], jid=jid))
            job_config['job_id'] = str(jid)
            num -= 1

    def schedule_jobs(self, jobs_to_schedule, name):
        for job in jobs_to_schedule:
            log.info(
                'Scheduling %s', job['desc']
            )
            new_name = job['desc'].split('/')[-1]
            job["name"] = new_name
            job['tube'] = self.args.tube
            num = self.args.get('num',1)
            self.schedule_job(job,num)

    def schedule_suite(self):
        """
        Schedule the suite-run. Returns the number of jobs scheduled.
        """
        name = self.name
        suite_name = self.base_config.suite
        suite_path = self.args.suite_path
        self.args.testdir = self.args.testdir.split(',')
        basedir=config.get('work_basedir','workunits')
        for d in self.args.testdir:
            cmd = 'rm -rf {testpath}/{basedir} && cp -r {basedir} {testpath}'.format(basedir=basedir,testpath=d)
            misc.sh(cmd)
        configs = build_matrix(suite_path)
        log.info('Suite %s in %s generated %d jobs (not yet filtered)' % (
            suite_name, suite_path, len(configs)))

        base_yaml_path = NamedTemporaryFile(
            prefix='schedule_suite_', delete=False
        ).name

        job_limit = self.args.limit or 0

        backtrack = 0
        limit = 10
        while backtrack <= limit:
            jobs_missing_packages, jobs_to_schedule = \
                self.collect_jobs(
                    util.filter_configs(configs,
                        filter_in=self.args.filter_in,
                        filter_out=self.args.filter_out,
                        filter_all=self.args.filter_all,
                        filter_fragments=self.args.filter_fragments,
                        suite_name=suite_name))
            if jobs_missing_packages:
                self.base_config = self.build_base_config()
                backtrack += 1
                continue
            break

        with open(base_yaml_path, 'w+b') as base_yaml:
            base_yaml.write(str(self.base_config).encode())
        self.schedule_jobs(jobs_to_schedule, name)
 

        count = len(jobs_to_schedule)
        missing_count = len(jobs_missing_packages)
        worker_start_all(self.args)
        log.info(
            'Suite %s in %s scheduled %d jobs.' %
            (suite_name, suite_path, count)
        )
        log.info('%d/%d jobs were filtered out.',
                 (len(configs) - count),
                 len(configs))
        return count
