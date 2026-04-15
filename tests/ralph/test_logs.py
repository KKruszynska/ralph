
from ralph import logs


class TestLogs:
    """
    Class with tests for logs.
    """

    def test_create_log(self, log_level):
        """
        Create a logger instance and write all level of information in it.
        :param log_level: Log level (error, info, debug).
        """
        log = logs.start_log('tests/ralph/data/output/',
                             log_level,
                             event_name=f'test_{log_level:s}'
                             )
        log.debug('Hello! This is a debug.')
        log.info('Hello! This is an info.')
        log.error('Hello! This is an error.')
        # log.exception('Hello! This is an exeption.')
        logs.close_log(log)

def test_run():
    """
    Run all tests to check if the logs are working.
    """
    test = TestLogs()
    test.test_create_log('debug')
    test.test_create_log('error')

