''' Module of mixed utilities'''

# Used in searchclient

class Worker:

    def __init__(self, color, name, boxes, num_cols, num_rows):
        self.name = name
        self.movable = boxes
        self.agent_rows = [None for _ in range(10)]
        self.agent_cols = [None for _ in range(10)]
        self.goals = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        self.boxes = [['' for _ in range(num_cols)] for _ in range(num_rows)]
        self.color = color
        self.constraints = None

# Used in conflictmodule

def match_length(arr1, arr2):

    len_diff = abs(len(arr2) - len(arr1))
    if len(arr1) < len(arr2):
        last_value = arr1[-1]
        arr1 += [last_value] * len_diff
    elif len(arr2) < len(arr1):
        last_value = arr2[-1]
        arr2 += [last_value] * len_diff
    return arr1, arr2

# Used in heuristic 

def manhattan(pos0, pos1):
    return abs(pos0[0] - pos1[0]) + abs(pos0[1] - pos1[1])
