from __future__ import print_function
import os
import sys
os.environ['GEVENT_NOWAITPID'] = 'true'



import logging
import subprocess

__version__ = '1.0.0'

# do our best, but if it fails, continue with above

try:
    fsthrash_dir = os.path.dirname(os.path.realpath(__file__))
    site_dir = os.path.dirname(fsthrash_dir)
except Exception as e:
    raise

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s:%(name)s:%(message)s')
log = logging.getLogger(__name__)

log.debug('fsthrash version: %s', __version__)


def setup_log_file(log_path):
    root_logger = logging.getLogger()
    handlers = root_logger.handlers
    for handler in handlers:
#        handler.close()
#        root_logger.removeHandler(handler)
        if isinstance(handler, logging.FileHandler) and \
                handler.stream.name == log_path:
            log.debug("Already logging to %s; not adding new handler",
                      log_path)
            return handler
    formatter = logging.Formatter(
        fmt=u'%(asctime)s.%(msecs)03d %(levelname)s:%(name)s:%(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S')
    handler = logging.FileHandler(filename=log_path)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.info('fsthash version: %s', __version__)
    return handler

def close_log_file(handler):
    root_logger = logging.getLogger()
    handler.close()
    root_logger.removeHandler(handler)

def install_except_hook():
    """
    Install an exception hook that first logs any uncaught exception, then
    raises it.
    """
    def log_exception(exc_type, exc_value, exc_traceback):
        if not issubclass(exc_type, KeyboardInterrupt):
            log.critical("Uncaught exception", exc_info=(exc_type, exc_value,
                                                         exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    sys.excepthook = log_exception


def patch_gevent_hub_error_handler():
    Hub._origin_handle_error = Hub.handle_error

    def custom_handle_error(self, context, type, value, tb):
        if context is None or issubclass(type, Hub.SYSTEM_ERROR):
            self.handle_system_error(type, value)
        elif issubclass(type, Hub.NOT_ERROR):
            pass
        else:
            log.error("Uncaught exception (Hub)", exc_info=(type, value, tb))

    Hub.handle_error = custom_handle_error

#patch_gevent_hub_error_handler()
