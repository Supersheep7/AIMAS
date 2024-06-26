from enum import Enum, unique

@unique
class ActionType(Enum):
    NoOp = 0
    Move = 1
    Push = 2
    Pull = 3

@unique
class Action(Enum):

    NoOp = ("NoOp", ActionType.NoOp, 0, 0, 0, 0)

    MoveN = ("Move(N)", ActionType.Move, -1, 0, 0, 0)
    MoveS = ("Move(S)", ActionType.Move, 1, 0, 0, 0)
    MoveE = ("Move(E)", ActionType.Move, 0, 1, 0, 0)
    MoveW = ("Move(W)", ActionType.Move, 0, -1, 0, 0)

    PushNN = ("Push(N,N)", ActionType.Push, -1, 0, -1, 0)
    PushNE = ("Push(N,E)", ActionType.Push, -1, 0, 0, 1)
    PushNW = ("Push(N,W)", ActionType.Push, -1, 0, 0, -1)
    PushSS = ("Push(S,S)", ActionType.Push, 1, 0, 1, 0)
    PushSE = ("Push(S,E)", ActionType.Push, 1, 0, 0, 1)
    PushSW = ("Push(S,W)", ActionType.Push, 1, 0, 0, -1)
    PushEE = ("Push(E,E)", ActionType.Push, 0, 1, 0, 1)
    PushES = ("Push(E,S)", ActionType.Push, 0, 1, 1, 0)
    PushEN = ("Push(E,N)", ActionType.Push, 0, 1, -1, 0)
    PushWW = ("Push(W,W)", ActionType.Push, 0, -1, 0, -1)
    PushWS = ("Push(W,S)", ActionType.Push, 0, -1, 1, 0)
    PushWN = ("Push(W,N)", ActionType.Push, 0, -1, -1, 0)

    PullNN = ("Pull(N,N)", ActionType.Pull, -1, 0, -1, 0)
    PullNE = ("Pull(N,E)", ActionType.Pull, -1, 0, 0, 1)
    PullNW = ("Pull(N,W)", ActionType.Pull, -1, 0, 0, -1)
    PullSS = ("Pull(S,S)", ActionType.Pull, 1, 0, 1, 0)
    PullSE = ("Pull(S,E)", ActionType.Pull, 1, 0, 0, 1)
    PullSW = ("Pull(S,W)", ActionType.Pull, 1, 0, 0, -1)
    PullEE = ("Pull(E,E)", ActionType.Pull, 0, 1, 0, 1)
    PullES = ("Pull(E,S)", ActionType.Pull, 0, 1, 1, 0)
    PullEN = ("Pull(E,N)", ActionType.Pull, 0, 1, -1, 0)
    PullWW = ("Pull(W,W)", ActionType.Pull, 0, -1, 0, -1)
    PullWS = ("Pull(W,S)", ActionType.Pull, 0, -1, 1, 0)
    PullWN = ("Pull(W,N)", ActionType.Pull, 0, -1, -1, 0)
    
    def __init__(self, name, type, ard, acd, brd, bcd):
        self.name_ = name
        self.type = type
        self.agent_row_delta = ard # horisontal displacement agent (-1,0,+1)
        self.agent_col_delta = acd # vertical displacement agent (-1,0,+1)
        self.box_row_delta = brd # horisontal displacement box (-1,0,+1)
        self.box_col_delta = bcd # vertical displacement box (-1,0,+1)