import os
import yaml
import logging
import collections


def init_logging():
    log = logging.getLogger(__name__)
    return log

log = init_logging()


class YamlConfig(collections.MutableMapping):
    """
    A configuration object populated by parsing a yaml file, with optional
    default values.

    Note that modifying the _defaults attribute of an instance can potentially
    yield confusing results; if you need to do modify defaults, use the class
    variable or create a subclass.
    """
    _defaults = dict()

    def __init__(self, yaml_path=None):
        self.yaml_path = yaml_path
        if self.yaml_path:
            self.load()
        else:
            self._conf = dict()

    def load(self, conf=None):
        if conf:
            self._conf = conf
            return
        if os.path.exists(self.yaml_path):
            with open(self.yaml_path) as f:
                self._conf = yaml.safe_load(f)
        else:
            log.debug("%s not found", self.yaml_path)
            self._conf = dict()

    def to_str(self):
        """
        :returns: str(self)
        """
        return str(self)
    
    def get(self, key, default=None):
        return self._conf.get(key, default)

    def __str__(self):
        return yaml.safe_dump(self._conf, default_flow_style=False).strip()

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __getattr__(self, name):
        return self._conf.get(name, self._defaults.get(name))

    def __contains__(self, name):
        return self._conf.__contains__(name)

    def __setattr__(self, name, value):
        if name.endswith('_conf') or name in ('yaml_path'):
            object.__setattr__(self, name, value)
        else:
            self._conf[name] = value

    def __delattr__(self, name):
        del self._conf[name]
    
    def __len__(self):
        return self._conf.__len__()

    def __iter__(self):
        return self._conf.__iter__()

    def __setitem__(self, name, value):
        self._conf.__setitem__(name, value)

    def __delitem__(self, name):
        self._conf.__delitem__(name)
    @classmethod
    def from_dict(cls, in_dict):
        """
        Build a config object from a dict.

        :param in_dict: The dict to use
        :returns:       The config object
        """
        conf_obj = cls()
        conf_obj._conf = in_dict
        return conf_obj

class FsthrashConfig(YamlConfig):
    yaml_path = os.path.join(os.path.expanduser('~/fsthrash.yaml'))
    _defaults = {
        'suite_path': '',
        "numjobs": '1',
        'max_job_time': 259200,
        'testdir': '',
        'results_timeout': 43200,
        'queue_host': 'localhost',
        'queue_port': 11300,
        'log_dir': 'output',
        'email_to': 'chenyunhui@corp.netease.com',
    }

    def __init__(self, yaml_path=None):
        super(FsthrashConfig, self).__init__(yaml_path or self.yaml_path)

class JobConfig(YamlConfig):
    pass

class FakeNamespace(YamlConfig):
    """
    This class is meant to behave like a argparse Namespace

    We'll use this as a stop-gap as we refactor commands but allow the tasks
    to still be passed a single namespace object for the time being.
    """
    def __init__(self, config_dict=None):
        if not config_dict:
            config_dict = dict()
        self._conf = self._clean_config(config_dict)
        set_config_attr(self)

    def _clean_config(self, config_dict):
        """
        Makes sure that the keys of config_dict are able to be used.  For
        example the "--" prefix of a docopt dict isn't valid and won't populate
        correctly.
        """
        result = dict()
        for key, value in config_dict.items():
            new_key = key
            if new_key.startswith("--"):
                new_key = new_key[2:]
            elif new_key.startswith("<") and new_key.endswith(">"):
                new_key = new_key[1:-1]

            if "-" in new_key:
                new_key = new_key.replace("-", "_")

            result[new_key] = value

        return result

    def __getattr__(self, name):
        """
        We need to modify this for FakeNamespace so that getattr() will
        work correctly on a FakeNamespace instance.
        """
        if name in self._conf:
            return self._conf[name]
        elif name in self._defaults:
            return self._defaults[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == 'fsthrash_config':
            object.__setattr__(self, name, value)
        else:
            super(FakeNamespace, self).__setattr__(name, value)

    def __repr__(self):
        return repr(self._conf)

    def __str__(self):
        return str(self._conf)


def set_config_attr(obj):
    obj.fsthrash_config = config


def _get_config_path():
    system_config_path = '/etc/fsthrash.yaml'
    if not os.path.exists(FsthrashConfig.yaml_path) and \
            os.path.exists(system_config_path):
        return system_config_path
    return FsthrashConfig.yaml_path

config = FsthrashConfig(yaml_path=_get_config_path())
#if not  config.suite_path:
#    assert False,"test path not config"
#if not os.path.exists(config.suite_path):
#    assert False,"incorrect test path"
