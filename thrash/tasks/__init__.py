import logging

log = logging.getLogger(__name__)


class Task(object):

    def __init__(self, ctx=None, config=None):
        if not hasattr(self, 'name'):
            self.name = self.__class__.__name__.lower()
        self.log = log
        self.ctx = ctx
        self.config = config or dict()
        if not isinstance(self.config, dict):
            raise TypeError("config must be a dict")

    def setup(self):
        """
        Perform any setup that is needed by the task before it executes
        """
        pass

    def begin(self):
        """
        Execute the main functionality of the task
        """
        pass

    def end(self):
        """
        Perform any work needed to stop processes started in begin()
        """
        pass

    def teardown(self):
        """
        Perform any work needed to restore configuration to a previous state.

        Can be skipped by setting 'skip_teardown' to True in self.config
        """
        pass

    def __enter__(self):
        """
        When using an instance of the class as a context manager, this method
        calls self.setup(), then calls self.begin() and returns self.
        """
        self.setup()
        print "AAAAAAAAAAAAAAAAAAAAAAAA"
        self.begin()
        return self

    def __exit__(self, type_, value, traceback):
        """
        When using an instance of the class as a context manager, this method
        calls self.end() and self.teardown() - unless
        self.config['skip_teardown'] is True
        """
        self.end()
        if self.config.get('skip_teardown', False):
            self.log.info("Skipping teardown")
        else:
            self.teardown()
