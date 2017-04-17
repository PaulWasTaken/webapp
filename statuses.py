from enum import Enum


class Status(Enum):
    Up = 1
    Down = 2
    Unknown = 3


class ReturnCode(Enum):
    Ok = 0
    AccessDenied = 5
    AlreadyStarted = 1056
    IsBusy = 1061
    AlreadyStopped = 1062


class Commands(Enum):
    Start = 0
    Stop = 1
    Reboot = 2
