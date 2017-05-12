from subprocess import run, PIPE
from re import search
from executors.abstract_executor import Executor
from statuses import Status, UnixReturnCode, Commands


class UnixExecutor(Executor):
    command_correspondence = {
        Commands.Start: "start",
        Commands.Stop: "stop",
        Commands.Status: "status"
    }
    state_correspondence = {
        b"active": Status.Running,
        b"inactive": Status.Stopped
    }

    def __init__(self, settings):
        super().__init__(settings)
        self.check_state()

    def check_state(self):
        status = run(self.get_command_pattern(Commands.Status),
                     stdout=PIPE).stdout
        exist = search(b"(?<=Loaded: )[^ ]+", status).group()
        if exist == b"not-found":
            self.settings.notification = 'The specified service does not ' \
                                         'exist as an installed service.'
        if exist == b"masked":
            self.settings.notification = "The service is masked. You will " \
                                         "not be able to manage it."

    def get_command_correspondence(self, command):
        return UnixExecutor.command_correspondence[command]

    def get_state_correspondence(self, state):
        return UnixExecutor.state_correspondence[state]

    def get_command_pattern(self, command):
        return ["service", self.settings.service,
                self.get_command_correspondence(command)]

    def extract_status(self, output):
        return search(b"(?<=Active: )[^ ]+", output).group()

    def is_valid_code(self, return_code):
        try:
            UnixReturnCode(return_code)
            return True
        except ValueError as e:
            self.settings.notification = "Bad return code: {}.".format(e)
            self.settings.service_status = Status.Unknown
