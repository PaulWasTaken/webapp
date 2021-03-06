from abc import ABC, abstractmethod
from asyncio import sleep
from collections import namedtuple
from os.path import devnull
from subprocess import run, PIPE

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
    def extract_status(self, output):
        pass

    @abstractmethod
    def get_command_pattern(self, command):
        pass

    @abstractmethod
    def get_command_correspondence(self, command):
        pass

    @abstractmethod
    def get_state_correspondence(self, state):
        pass

    @abstractmethod
    def is_valid_code(self, return_code):
        pass

    def set_service_status(self):
        res = run(self.get_command_pattern(Commands.Status), stdout=PIPE)
        if self.is_valid_code(res.returncode):
            status = self.extract_status(res.stdout)
            self.settings.service_status = self.get_state_correspondence(
                status)

    def process(self, command):
        self.set_service_status()
        self.exec_command(command)
        self.set_service_status()

    def exec_command(self, command):
        expected = Executor.expected_state[command].expected
        pending = Executor.expected_state[command].in_progress
        with open(devnull, 'w') as temp:
            if self.settings.service_status in [expected, pending]:
                return
            run(self.get_command_pattern(command),
                stdout=temp, stderr=temp)

    async def sleep_until_stop(self):
        while True:
            await sleep(0.5)
            self.set_service_status()
            if self.settings.service_status is Status.Stopped:
                return
