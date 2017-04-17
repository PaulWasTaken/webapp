import aiohttp_jinja2
import jinja2
import subprocess
import json
from os import devnull
from aiohttp import web
from statuses import Status, ReturnCode, Commands


class WebApp(web.Application):
    colour_map = {
        Status.Up: "green",
        Status.Down: "red",
        Status.Unknown: "#D6CE1F"
    }

    map_name = {
        Commands.Start.name: Status.Up,
        Commands.Stop.name: Status.Down,
    }

    def __init__(self, service):
        super().__init__()
        aiohttp_jinja2.setup(self, loader=jinja2.FileSystemLoader(''))
        self.mode = True
        self.service = service
        self.service_status = Status.Unknown
        self.colour = WebApp.colour_map[self.service_status]
        self.make_route_table()
        self.error = ""

    def make_route_table(self):
        self.router.add_get('/', self.base_handler)
        self.router.add_get('/start', self.start_handler)
        self.router.add_get('/reboot', self.reboot_handler)
        self.router.add_get('/stop', self.stop_handler)
        self.router.add_get('/change', self.mode_handler)

    async def mode_handler(self, request):
        self.mode = not self.mode
        self.service_status = Status.Unknown
        with open('settings.json', 'w') as fp:
            json.dump(self.mode, fp)
        return web.Response()

    @aiohttp_jinja2.template('site.html')
    async def base_handler(self, request):
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def start_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.exec_command(Commands.Start.name)
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def reboot_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.exec_command(Commands.Stop.name)
        self.exec_command(Commands.Start.name)
        return self.get_fields_values()

    @aiohttp_jinja2.template('site.html')
    async def stop_handler(self, request):
        if not self.mode:
            return self.get_fields_values()
        self.exec_command(Commands.Stop.name)
        return self.get_fields_values()

    def get_fields_values(self):
        error = self.error
        self.error = ""
        return {
            "error": error,
            "mode": self.mode,
            "status": self.service_status.name,
            "color": self.colour_map[self.service_status]
        }

    def exec_command(self, command):
        with open(devnull, 'w') as temp:
            try:
                return_code = ReturnCode(subprocess.run(
                    "sc {command} {service}".format(
                        command=command, service=self.service),
                    shell=True, stdout=temp, stderr=temp).returncode)
                if return_code is ReturnCode.Ok or \
                   return_code is ReturnCode.AlreadyStarted or \
                   return_code is ReturnCode.AlreadyStopped:
                    self.service_status = WebApp.map_name[command]
                elif return_code == ReturnCode.AccessDenied:
                    self.error = "You should run the script with administrator rights."
                elif return_code == ReturnCode.IsBusy:
                    self.error = "The service is busy. Please, wait a little bit."
                else:
                    self.service_status = Status.Unknown    # For the future needs
            except ValueError as e:
                self.error = "Unknown return code."


app = WebApp("browser")
web.run_app(app, host='localhost', port=8080)
