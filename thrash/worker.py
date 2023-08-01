import logging
import os
import subprocess
import sys
import tempfile
import time
import yaml
from multiprocessing import Process
from datetime import datetime

from thrash.run import runtask
from thrash import setup_log_file, install_except_hook, close_log_file
from thrash.config import config as fsthrash_config
from thrash import beanstalk

log = logging.getLogger(__name__)
start_time = datetime.utcnow()
restart_file_path = '/tmp/fsthrash-restart-workers'
stop_file_path = '/tmp/fsthrash-stop-workers'


def sentinel(path):
    if not os.path.exists(path):
        return False
    file_mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
    if file_mtime > start_time:
        return True
    else:
        return False


def restart():
    log.info('Restarting...')
    args = sys.argv[:]
    args.insert(0, sys.executable)
    os.execv(sys.executable, args)


def stop():
    log.info('Stopping...')
    sys.exit(0)

def worker_start_all(args):
    numjobs = int(args.numjobs)
    p_list = []
    fsthrash_config.load()
    for i in range(numjobs):
        p = Process(target=worker_start,args=(args,))
        p_list.append(p)
        p.start()
        log.info("Job PID: %s", str(p.pid))
    for proc in p_list:
        proc.join()
        if proc.exitcode != 0:
            log.error("proc %s run fail!!!",str(proc.pid))

def worker_start(ctx):
    loglevel = logging.INFO
    log.setLevel(loglevel)


    install_except_hook()


#    set_config_attr(ctx)

    connection = beanstalk.connect()
    beanstalk.watch_tube(connection, ctx.tube)
    connection.use(ctx.tube)
    result_proc = None
    while connection.stats_tube(ctx.tube)['current-jobs-ready']:
        if result_proc is not None and result_proc.poll() is not None:
            log.debug("results exited with code: %s",
                      result_proc.returncode)
            result_proc = None

        if sentinel(restart_file_path):
            restart()
        elif sentinel(stop_file_path):
            stop()
        job = connection.reserve(timeout=60)
        if job is None:
            continue

        # bury the job so it won't be re-run if it fails
        job.bury()
        job_id = job.jid
        job_config = yaml.safe_load(job.body)
        job_config['job_id'] = str(job_id)
        log_dir = os.path.join(ctx.log_dir,job_config['name'],str(job_id))
        job_config['log_archive'] = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, 'worker.{tube}.{jid}'.format( \
            jid=job_id, tube=ctx.tube,))
        handler = setup_log_file(log_file_path)

        if job_config.get('stop_worker'):
            return 0
        try:
            run_job(
                ctx,
                job_config
            )
#        except SkipJob:
#            continue
        except:
            job.delete()
            continue
        finally:
            close_log_file(handler)

        # This try/except block is to keep the worker from dying when
        # beanstalkc throws a SocketError
        try:
            job.delete()
        except Exception:
            log.exception("Saw exception while trying to delete job")

def run_job(ctx,job_config):

    log.info('Running job %s', job_config['job_id'])
    runtask(ctx,job_config)

#    if ret != True:
#        log.error('Child exited with code %d', ret)
#    else:
#        log.info('Success!')

if (__name__=="__main__"):
   main()
