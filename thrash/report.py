import os
import yaml
import json
import re
import logging
import socket
from datetime import datetime

import thrash
from thrash.config import config
from thrash.job_status import get_status, set_status



def init_logging():
    """
    Set up logging for the module

    :returns: a logger
    """
    log = logging.getLogger(__name__)
    return log



class ResultsSerializer(object):
    """
    This class exists to poke around in the archive directory doing things like
    assembling lists of test runs, lists of their jobs, and merging sets of job
    YAML files together to form JSON objects.
    """
    yamls = ('config.yaml', 'summary.yaml')

    def __init__(self, archive_base, log=None):
        self.archive_base = archive_base or config.archive_base
        self.log = log or init_logging()


    def job_info(self, run_name, job_id):
        """
        Given a run name and job id, merge the job's YAML files together.

        :param run_name: The name of the run.
        :param job_id:   The job's id.
        :param simple(bool): Read less data for speed (only orig.config.yaml/info.yaml)
        :returns:        A dict.
        """
        job_archive_dir = os.path.join(self.archive_base,
                                       run_name,
                                       job_id)
        job_info = {}

        for yaml_name in self.yamls:
            yaml_path = os.path.join(job_archive_dir, yaml_name)
            if not os.path.exists(yaml_path):
                continue
            with open(yaml_path) as yaml_file:
                partial_info = yaml.safe_load(yaml_file)
                if partial_info is not None:
                    job_info.update(partial_info)

        if 'job_id' not in job_info:
            job_info['job_id'] = job_id

        return job_info

    def json_for_job(self, run_name, job_id):
        """
        Given a run name and job id, merge the job's YAML files together to
        create a JSON object.

        :param run_name: The name of the run.
        :param job_id:   The job's id.
        :returns:        A JSON object.
        """
        job_info = self.job_info(run_name, job_id)
        job_json = json.dumps(job_info, sort_keys=True, indent=4)
        return job_json

    def jobs_for_run(self, run_name):
        """
        Given a run name, look on the filesystem for directories containing job
        information, and return a dict mapping job IDs to job directories.

        :param run_name: The name of the run.
        :returns:        A dict like: {'1': '/path/to/1', '2': 'path/to/2'}
        """
        archive_dir = os.path.join(self.archive_base, run_name)
        if not os.path.isdir(archive_dir):
            return {}
        jobs = {}
        for item in os.listdir(archive_dir):
            if not re.match('\d+$', item):
                continue
            job_id = item
            job_dir = os.path.join(archive_dir, job_id)
            if os.path.isdir(job_dir):
                jobs[job_id] = job_dir
        return jobs

    def running_jobs_for_run(self, run_name):
        """
        Like jobs_for_run(), but only returns jobs with no summary.yaml

        :param run_name: The name of the run.
        :returns:        A dict like: {'1': '/path/to/1', '2': 'path/to/2'}
        """
        jobs = self.jobs_for_run(run_name)
        for job_id in list(jobs):
            if os.path.exists(os.path.join(jobs[job_id], 'summary.yaml')):
                jobs.pop(job_id)
        return jobs

    @property
    def all_runs(self):
        """
        Look in the base archive directory for all test runs. Return a list of
        their names.
        """
        archive_base = self.archive_base
        if not os.path.isdir(archive_base):
            return []
        runs = []
        for run_name in os.listdir(archive_base):
            if not os.path.isdir(os.path.join(archive_base, run_name)):
                continue
            runs.append(run_name)
        return runs


class ResultsReporter(object):

    def __init__(self, archive_base=None, save=False,
                 refresh=False, log=None):
        self.log = log or init_logging()
        self.archive_base = archive_base or config.archive_base
        self.serializer = ResultsSerializer(archive_base, log=self.log)

    def get_all_runs(self):
        """
        Get *all* runs in self.archive_dir to the results server.
        """
        all_runs = self.serializer.all_runs
        runs = all_runs
        return self.report_runs(runs)

    def report_runs(self, run_names):
        """
        Report several runs to the results server.

        :param run_names: The names of the runs.
        """
        all_info = []
        num_runs = len(run_names)
        num_jobs = 0
        self.log.info("Posting %s runs", num_runs)
        for run_name in run_names:
            jobs = self.serializer.jobs_for_run(run_name)
            if jobs:
                for job_id in jobs.keys():
                    job_info = self.serializer.job_info(run_name, job_id)
                    if get_status(job_info) is None:
                        set_status(job_info, 'Running')
                    all_info.append(job_info)
                    num_jobs += 1
            elif not jobs:
                self.log.debug("    no jobs; skipped")
        self.log.info("Total: %s jobs in %s runs", num_jobs, len(run_names))
        return all_info

