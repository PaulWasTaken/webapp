import aiohttp_jinja2
import argparse
import jinja2
import json

from asyncio import sleep
from aiohttp import web
from collections import namedtuple
from os import devnull
from re import search
from statuses import Status, ReturnCode, Commands
from subprocess import run, PIPE

CommandAttrib = namedtuple("CommandAttrib", "expected, in_progress")


class WebApp(web.Application):
    colour_map = {
        Status.Running: "green",
        Status.Stopped: "red",
        Status.Unknown: "#D6CE1F",
        Status.StopPending: "red",
        Status.StartPending: "green"
    }

    command_attrib = {
        Commands.Start: CommandAttrib(Status.Running, Status.StartPending),
        Commands.Stop: CommandAttrib(Status.Stopped, Status.StopPending),
    }

    def __init__(self, service):
        super().__init__()
        aiohttp_jinja2.setup(self, loader=jinja2.FileSystemLoader(''))
        self.mode = True
        self.service = service
        self.service_status = Status.Unknown
        self.colour = WebApp.colour_map[self.service_status]
        self.make_route_table()
        self.notification = ""

    def make_route_table(self):
        self.router.add_get('/', self.base_handler)
        self.router.add_get('/start', self.start_handler)
        self.router.add_get('/reboot', self.reboot_handler)
        self.router.add_get('/stop', self.stop_handler)
        self.router.add_get('/check', self.check_handler)

    def mode_handler(self):
        self.mode = not self.mode
        with open('settings.json', 'w') as fp:
            json.dump(self.mode, fp)

    @aiohttp_jinja2.template('site.html')
    async def base_handler(self, request):
        parameters = request.rel_url.query
        self.set_service_status()
        if "mode" in parameters:
            self.mode_handler()
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def start_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.process(Commands.Start)
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def reboot_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.process(Commands.Stop)
        await self.sleep_until_stop()
        self.process(Commands.Start)
        self.notification = "Reboot has been completed."
        return self.get_fields_values()

    async def sleep_until_stop(self):
        while True:
            await sleep(0.5)
            self.set_service_status()
            if self.service_status is Status.Stopped:
                return

    @aiohttp_jinja2.template('site.html')
    async def stop_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.process(Commands.Stop)
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def check_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.set_service_status()
        return self.get_fields_values()

    def process(self, command):
        self.set_service_status()
        self.exec_command(command)

    def get_fields_values(self):
        notification = self.notification
        self.notification = ""
        return {
            "notification": notification,
            "mode": self.mode,
            "status": self.service_status.name,
            "color": self.colour_map[self.service_status]
        }

    def exec_command(self, command):
        with open(devnull, 'w') as temp:
            if self.service_status == WebApp.command_attrib[command].expected:
                return
            return_code = ReturnCode(run("sc {command} {service}".format(
                command=command.name, service=self.service),
                stdout=temp, stderr=temp).returncode)
            if not self.is_valid_code(return_code):
                return
            self.check_execution()

    def check_execution(self):
        try:
            self.set_service_status()
        except ValueError as e:
            self.notification = "Unknown status type({}).".format(e)

    def is_valid_code(self, return_code):
        if return_code == ReturnCode.AccessDenied:
            self.notification = "You should run the script " \
                                "with administrator rights."
        elif return_code == ReturnCode.IsBusy:
            self.notification = "The service is busy. " \
                                "Please, wait a little bit."
        elif return_code == ReturnCode.DoesntExist:
            self.notification = "The specified service does not " \
                                "exist as an installed service."
        else:
            return True
        return False

    def set_service_status(self):
        res = run("sc query {}".format(self.service), stdout=PIPE).stdout
        status = search(b"\d+", res.split(b"\r\n")[3]).group()
        self.service_status = Status(int(status))


def create_parser():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--port", type=int,
                   help="Set port value.", dest="port", default=8080)
    p.add_argument("-s", "--service", help="Set service you want to manage.",
                   dest="service", default="browser")
    return p


if __name__ == "__main__":
    parser = create_parser()
    settings = parser.parse_args()
    app = WebApp(settings.service)
    try:
        web.run_app(app, port=settings.port)
    except OSError:
        print("Port {} is already being used.".format(settings.port))
