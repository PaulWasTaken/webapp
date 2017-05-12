from executors.abstract_executor import Executor
from re import search
from statuses import WinReturnCode, Status, Commands
from subprocess import run, PIPE


class WinExecutor(Executor):
    command_correspondence = {
        Commands.Start: "start",
        Commands.Stop: "stop",
        Commands.Status: "query"
    }
    state_correspondence = {
        b"1": Status.Stopped,
        b"2": Status.StartPending,
        b"3": Status.StopPending,
        b"4": Status.Running
    }

    def __init__(self, settings):
        super().__init__(settings)

    def get_state_correspondence(self, state):
        return WinExecutor.state_correspondence[state]

    def get_command_correspondence(self, command):
        return WinExecutor.command_correspondence[command]

    def get_command_pattern(self, command):
        return ["sc", self.get_command_correspondence(command),
                self.settings.service]

    def is_valid_code(self, code):
        try:
            return_code = WinReturnCode(code)
            if return_code == WinReturnCode.AccessDenied:
                self.settings.notification = "You should run the script " \
                                             "with administrator rights."
            elif return_code == WinReturnCode.IsBusy:
                self.settings.notification = "The service is busy. " \
                                             "Please, wait a little bit."
            elif return_code == WinReturnCode.DoesntExist:
                self.settings.notification = \
                    'The specified service does not ' \
                    'exist as an installed service.'
            elif return_code == WinReturnCode.NotStarted:
                self.settings.notification = 'The service has ' \
                                             'not been started.'
            else:
                return True
        except ValueError as e:
            self.settings.notification = "Unknown return code: {}. " \
                                         "Please, try again.".format(e)
            self.settings.service_status = Status.Unknown

    def extract_status(self, output):
        return search(b"\d+", output.split(b"\r\n")[3]).group()
