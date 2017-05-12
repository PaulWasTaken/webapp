from enum import Enum


class Status(Enum):
    Unknown = 0
    Stopped = 1
    StartPending = 2
    StopPending = 3
    Running = 4


class WinReturnCode(Enum):
    Ok = 0
    AccessDenied = 5
    DoesntExist = 1060
    IsBusy = 1061
    NotStarted = 1062


class UnixReturnCode(Enum):
    Ok = 0
    NotRunning = 3


class Commands(Enum):
    Start = 0
    Stop = 1
    Reboot = 2
