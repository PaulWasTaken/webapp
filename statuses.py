from enum import Enum


class Status(Enum):
    Unknown = 0
    Stopped = 1
    StartPending = 2
    StopPending = 3
    Running = 4


class ReturnCode(Enum):
    Ok = 0
    AccessDenied = 5
    DoesntExist = 1060
    IsBusy = 1061


class Commands(Enum):
    Start = 0
    Stop = 1
    Reboot = 2
