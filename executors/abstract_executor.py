from abc import ABC, abstractmethod
from asyncio import sleep
from collections import namedtuple
from os.path import devnull
from subprocess import run

from statuses import Status, Commands

CommandAttrib = namedtuple("CommandAttrib", "expected, in_progress")


class Executor(ABC):
    expected_state = {
        Commands.Start: CommandAttrib(Status.Running, Status.StartPending),
        Commands.Stop: CommandAttrib(Status.Stopped, Status.StopPending)
    }

    def __init__(self, settings):
        self.settings = settings

    @abstractmethod
    def set_service_status(self):
        pass

    @abstractmethod
    def get_command_pattern(self):
        pass

    @abstractmethod
    def is_valid_code(self, return_code):
        pass

    def exec_command(self, command):
        expected = Executor.expected_state[command].expected
        pending = Executor.expected_state[command].in_progress
        with open(devnull, 'w') as temp:
            if self.settings.service_status in [expected, pending]:
                return
            return_code = run(self.get_command_pattern().format(
                command=command.name, service=self.settings.service)
                              .split(" "),
                              stdout=temp, stderr=temp).returncode
            if not self.is_valid_code(return_code):
                return
            self.set_service_status()

    async def sleep_until_stop(self):
        while True:
            await sleep(0.5)
            self.set_service_status()
            if self.settings.service_status is Status.Stopped:
                return
