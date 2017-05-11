from statuses import Status


class Settings:
    colour_map = {
        Status.Running: "green",
        Status.Stopped: "red",
        Status.Unknown: "#D6CE1F",
        Status.StopPending: "red",
        Status.StartPending: "green"
    }

    def __init__(self, service):
        self.mode = True
        self.service = service
        self.service_status = Status.Unknown
        self._colour = None
        self.notification = ""

    @property
    def colour(self):
        self.colour = Settings.colour_map[self.service_status]
        return self._colour

    @colour.setter
    def colour(self, value):
        self._colour = value
