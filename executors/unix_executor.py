from subprocess import run, PIPE
from re import search
from executors.abstract_executor import Executor
from statuses import Status, UnixReturnCode


class UnixExecutor(Executor):
    def __init__(self, settings):
        super().__init__(settings)

    def get_command_pattern(self):
        return "service {service} {command}"

    def set_service_status(self):
        res = run("service {} status".format(self.settings.service),
                  stdout=PIPE)
        if self.is_valid_code(res.returncode):
            status = search(b"\d+", res.stdout.split(b"\r\n")[3]).group()
            self.settings.service_status = Status(int(status))

    def is_valid_code(self, return_code):
        try:
            UnixReturnCode(return_code)
            return True
        except ValueError as e:
            self.settings.notification = "Bad return code: {}.".format(e)
            self.settings.service_status = Status.Unknown
