import aiohttp_jinja2
import argparse
import jinja2
import json

from aiohttp import web
from executors.unix_executor import UnixExecutor
from executors.win_executor import WinExecutor
from os.path import realpath, split
from settings import Settings
from statuses import Commands
from sys import platform


class WebApp(web.Application):
    def __init__(self, service):
        super().__init__()
        aiohttp_jinja2.setup(self, loader=jinja2.
                             FileSystemLoader(split(realpath(__file__))[0]))
        self.settings = Settings(service)
        self.executor = None
        self.chose_executor()
        self.make_route_table()

    def chose_executor(self):
        if platform == "win32":
            self.executor = WinExecutor(self.settings)
        elif platform == "linux":
            self.executor = UnixExecutor(self.settings)
        else:
            raise NotImplementedError

    def make_route_table(self):
        self.router.add_get('/', self.base_handler)
        self.router.add_get('/start', self.start_handler)
        self.router.add_get('/reboot', self.reboot_handler)
        self.router.add_get('/stop', self.stop_handler)
        self.router.add_get('/check', self.check_handler)

    def mode_handler(self):
        self.settings.mode = not self.settings.mode
        with open('settings.json', 'w') as fp:
            json.dump(self.settings.mode, fp)

    @aiohttp_jinja2.template('site.html')
    async def base_handler(self, request):
        parameters = request.rel_url.query
        self.executor.set_service_status()
        if "mode" in parameters:
            self.mode_handler()
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def start_handler(self, request):
        if not self.settings.mode:
            return self.get_fields_values()
        self.executor.process(Commands.Start)
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def reboot_handler(self, request):
        if not self.settings.mode:
            return self.get_fields_values()
        self.executor.process(Commands.Stop)
        await self.executor.sleep_until_stop()
        self.executor.process(Commands.Start)
        self.settings.notification = "Reboot has been completed."
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def stop_handler(self, request):
        if not self.settings.mode:
            return self.get_fields_values()
        self.executor.process(Commands.Stop)
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def check_handler(self, request):
        if not self.settings.mode:
            return self.get_fields_values()
        self.executor.set_service_status()
        return self.get_fields_values()

    def get_fields_values(self):
        notification = self.settings.notification
        self.settings.notification = ""
        return {
            "notification": notification,
            "mode": self.settings.mode,
            "status": self.settings.service_status.name,
            "color": self.settings.colour
        }


def create_parser():
    p = argparse.ArgumentParser()
    p.add_argument("service", help="Set service you want to manage.",
                   metavar="service")
    p.add_argument("-p", type=int,
                   help="Set port value.", dest="port", default=8080)
    p.add_argument("-i", type=str, help="Set ip address.",
                   dest="ip", default="localhost")
    return p


if __name__ == "__main__":
    parser = create_parser()
    settings = parser.parse_args()
    app = WebApp(settings.service)
    try:
        web.run_app(app, host=settings.ip, port=settings.port)
    except OSError:
        print("Port {} is already being used.".format(settings.port))
    except NotImplementedError:
        print("The platform you are trying to use is not supported.")
