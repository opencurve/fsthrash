import copy
import logging
import os
import smtplib
import socket
import subprocess
import sys

from email.mime.text import MIMEText


from thrash.config import config
from thrash.suite.build_matrix import combine_path

log = logging.getLogger(__name__)


def schedule_fail(message, name=''):
    """
    If an email address has been specified anywhere, send an alert there. Then
    raise a ScheduleFailError.
    """
    email = config.results_email
    if email:
        subject = "Failed to schedule {name}".format(name=name)
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = config.results_sending_email
        msg['To'] = email
        try:
            smtp = smtplib.SMTP('localhost')
            smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
            smtp.quit()
        except socket.error:
            log.exception("Failed to connect to mail server!")
    raise ScheduleFailError(message, name)



def strip_fragment_path(original_path):
    scan_after = '/suites/'
    scan_start = original_path.find(scan_after)
    if scan_start > 0:
        return original_path[scan_start + len(scan_after):]
    return original_path


def filter_configs(configs, suite_name=None,
                            filter_in=None,
                            filter_out=None,
                            filter_all=None,
                            filter_fragments=True):
    """
    Returns a generator for pairs of description and fragment paths.

    Usage:

        configs = build_matrix(path, subset, seed)
        for description, fragments in filter_configs(configs):
            pass
    """
    for item in configs:
        fragment_paths = item[1]
        description = combine_path(suite_name, item[0]) \
                                        if suite_name else item[0]
        base_frag_paths = [strip_fragment_path(x)
                                        for x in fragment_paths]
        def matches(f):
            if f in description:
                log.info("%s is in %s"%(f,description))
                return True
            if filter_fragments and \
                    any(f in path for path in base_frag_paths):
                return True
            return False
        if filter_all:
            if not all(matches(f) for f in filter_all):
                continue
        if filter_in:
            if not any(matches(f) for f in filter_in):
                continue
        if filter_out:
            if any(matches(f) for f in filter_out):
                continue
        yield([description, fragment_paths])
