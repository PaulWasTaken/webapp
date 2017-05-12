from subprocess import run, PIPE
from re import search
from executors.abstract_executor import Executor
from statuses import Status, UnixReturnCode


class UnixExecutor(Executor):
    correspondence = {
        b"active": 4,
        b"inactive": 1
    }

    def __init__(self, settings):
        super().__init__(settings)
        self.check_state()

    def check_state(self):
        status = run("service {} status".format(
            self.settings.service).split(" "), stdout=PIPE).stdout
        exist = search(b"(?<=Loaded: )[^ ]+", status).group()
        if exist == b"not-found":
            self.settings.notification = 'The specified service does not ' \
                                         'exist as an installed service.'
        if exist == b"masked":
            self.settings.notification = "The service is masked. You will " \
                                         "not be able to manage it."

    def get_command_pattern(self, name, command):
        return ["service", name, command]

    def set_service_status(self):
        res = run("service {} status".format(self.settings.service).split(" "),
                  stdout=PIPE)
        if self.is_valid_code(res.returncode):
            status = search(b"(?<=Active: )[^ ]+", res.stdout).group()
            self.settings.service_status = Status(
                int(UnixExecutor.correspondence[status])
            )

    def is_valid_code(self, return_code):
        try:
            if return_code == UnixReturnCode.NotRunning:
                self.settings.notification = "The service is not running."
            else:
                return True
        except ValueError as e:
            self.settings.notification = "Bad return code: {}.".format(e)
            self.settings.service_status = Status.Unknown
