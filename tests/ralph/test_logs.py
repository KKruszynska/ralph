import pytest

from MFPipeline import logs

class testLogs():
    '''
    Class with tests
    '''
    def test_create_log(self, log_level):
        log = logs.start_log("tests/test_logs/", log_level, event_name="test_%s"%log_level)
        log.debug("Hello! This is a debug.")
        log.info("Hello! This is an info.")
        log.error("Hello! This is an error.")
        # log.exception("Hello! This is an exeption.")
        logs.close_log(log)

def test_run():
    test = testLogs()
    test.test_create_log("debug")
    test.test_create_log("error")