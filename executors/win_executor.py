from executors.abstract_executor import Executor
from re import search
from statuses import WinReturnCode, Status
from subprocess import run, PIPE


class WinExecutor(Executor):
    def __init__(self, settings):
        super().__init__(settings)

    def get_command_pattern(self, name, command):
        return ["sc", command, name]

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

    def set_service_status(self):
        res = run("sc query {}".format(self.settings.service), stdout=PIPE)
        if self.is_valid_code(res.returncode):
            status = search(b"\d+", res.stdout.split(b"\r\n")[3]).group()
            self.settings.service_status = Status(int(status))
