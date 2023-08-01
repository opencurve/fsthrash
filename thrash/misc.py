import argparse
import os
import logging
import getpass
import shutil
import socket
import subprocess
import tarfile
import time
import yaml
import json
import re
import pprint
import datetime
import sys

from tarfile import ReadError


from config import config
reload(sys)
sys.setdefaultencoding('utf8')

log = logging.getLogger(__name__)

stamp = datetime.datetime.now().strftime("%y%m%d%H%M")



def config_file(string):
    """
    Create a config file

    :param string: name of yaml file used for config.
    :returns: Dictionary of configuration information.
    """
    config_dict = {}
    try:
        with open(string) as f:
            g = yaml.safe_load_all(f)
            for new in g:
                config_dict.update(new)
    except IOError as e:
        raise argparse.ArgumentTypeError(str(e))
    return config_dict


class MergeConfig(argparse.Action):
    """
    Used by scripts to mergeg configurations.   (nuke, run, and
    schedule, for example)
    """
    def __call__(self, parser, namespace, values, option_string=None):
        """
        Perform merges of all the day in the config dictionaries.
        """
        config_dict = getattr(namespace, self.dest)
        for new in values:
            deep_merge(config_dict, new)


def merge_configs(config_paths):
    """ Takes one or many paths to yaml config files and merges them
        together, returning the result.
    """
    conf_dict = dict()
    for conf_path in config_paths:
        if not os.path.exists(conf_path):
            log.debug("The config path {0} does not exist, skipping.".format(conf_path))
            continue
        with open(conf_path) as partial_file:
            partial_dict = yaml.safe_load(partial_file)
        try:
            conf_dict = deep_merge(conf_dict, partial_dict)
        except Exception:
            # TODO: Should this log as well?
            pprint.pprint("failed to merge {0} into {1}".format(conf_dict, partial_dict))
            raise

    return conf_dict


def sh(command, log_limit=1024, cwd=None, env=None):
    """
    Run the shell command and return the output in ascii (stderr and
    stdout).  If the command fails, raise an exception. The command
    and its output are logged, on success and on error.
    """
    log.debug(":sh: " + command)
    proc = subprocess.Popen(
        args=command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        bufsize=1)
    lines = []
    truncated = False
    with proc.stdout:
        for line in proc.stdout:
            line = line.decode()
            lines.append(line)
            line = line.strip()
            if len(line) > log_limit:
                truncated = True
                log.debug(line[:log_limit] +
                          "... (truncated to the first " + str(log_limit) +
                          " characters)")
            else:
                log.debug(line)
    output = "".join(lines)
    if proc.wait() != 0:
        if truncated:
            log.error(command + " replay full stdout/stderr"
                      " because an error occurred and some of"
                      " it was truncated")
            log.error(output)
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=command,
            output=output
        )
    return output

