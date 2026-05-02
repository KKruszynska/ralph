import os
from pathlib import Path

from ralph.toolbox import logs


class LogsTest:
    """
    Class with tests for logs.
    """

    def __init__(self,
                 log_level):
        """
        Constructor.

        :param log_level: Log level (error, info, debug).
        """

        self.log_level = log_level

    def test_create_log(self):
        """
        Create a logger instance and write all level of information in it.
        :param log_level: Log level (error, info, debug).
        """

        self.log = logs.start_log('tests/ralph/data/output/logs/',
                                  self.log_level,
                                  event_name=f'test_{self.log_level:s}'
                                  )

    def test_debug_log(self):
        """
        Test debug logger instance and write to it.
        """
        if self.log_level == 'debug':
            self.log.debug('Hello! This is a debug.')

    def test_error_log(self):
        """
        Test error logger instance and write to it.
        """
        if self.log_level == 'error':
            self.log.error('Hello! This is an error.')

    def test_info_log(self):
        """
        Test info logger instance and write to it.
        """
        self.log.info('Hello! This is an info.')

        # log.exception('Hello! This is an exeption.')

def run_debug_test():
    """
    Run the debug test for Ralph.
    """

    test_debug = LogsTest('debug')
    test_debug.test_create_log()
    test_debug.test_debug_log()
    logs.close_log(test_debug.log)

def run_error_test():
    """
    Run the error test for Ralph.
    """

    test_error = LogsTest('error')
    test_error.test_create_log()
    test_error.test_error_log()
    logs.close_log(test_error.log)


def run_info_test():
    """
    Run the info test for Ralph.
    """

    test_info = LogsTest('info')
    test_info.test_create_log()
    test_info.test_info_log()
    logs.close_log(test_info.log)


def test_run():
    """
    Run all tests to check if the logs are working.
    """

    run_info_test()
    run_debug_test()
    run_error_test()

    analyst_path = 'tests/ralph/data/output/logs/'
    log_level = ['info', 'debug', 'error']

    for level in log_level:
        output = Path(analyst_path + f'test_{level:s}.log')
        if output.exists():
            os.remove(output)



