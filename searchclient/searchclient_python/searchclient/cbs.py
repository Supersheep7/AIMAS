from state import State, Constraint
from frontier import FrontierBestFirstWidth
from heuristic import HeuristicBFWS
from graphsearch import search
from action import Action

class Node():

    def __init__(self, states):
        self.initial_states = states
        self.constraints = [state.constraints for state in self.initial_states]
        self.plans, self.paths = plans_from_states(self.initial_states)
        self.cost = max([len(plan) for plan in self.plans]) # length of longest solution

def match_length(arr1, arr2):
    len_diff = abs(len(arr2) - len(arr1))
    if len(arr1) < len(arr2):
        last_value = arr1[-1]
        arr1 += [last_value] * len_diff
    elif len(arr2) < len(arr1):
        last_value = arr2[-1]
        arr2 += [last_value] * len_diff
    return arr1, arr2

def agents_to_rest(plans):
    longest = max([len(plan) for plan in plans])
    filtered_plans = [plan for plan in plans if len(plan) <= longest]
    plans_with_rest = []
    for plan in filtered_plans:
        len_diff = longest - len(plan)
        plan += [[Action.NoOp]] * len_diff
        plans_with_rest.append(plan)
    return plans_with_rest

def plans_from_states(initial_states):

        plans = []
        plans_repr = []

        for num, initial_state in enumerate(initial_states):
            frontier = FrontierBestFirstWidth(HeuristicBFWS(initial_state))  
            plan, plan_repr = search(initial_state, frontier)
            plans.append(plan) 
            plans_repr.append(plan_repr)
            print("Ended search for initial state number", num)
            print()
            print("Plan extracted.")
            print()

        plans = agents_to_rest(plans)
        
        return plans, plans_repr

def validate(plan, plan_list):

    # Simple implementation for MAPF. We could need this also for teams and add boxes to the mix
    agent_i_full = plan[0][0][0]  # Something like 'AgentAt0'
    agent_i = agent_i_full.split('AgentAt')[-1]
    other_plans = [lst for lst in plan_list if lst is not plan]
    constraints = []

    for other_plan in other_plans:
        
        # Pads the shortest plan with copies of the last atom representation (agent still on the goal cell)
        plan, other_plan = match_length(plan, other_plan)   
        print("Plan len:", len(plan), "Other plan len:", len(other_plan),flush=True)
        for j in range(1,len(plan)):
            print("Plan:", plan[j], "Other plan:", other_plan[j],flush=True)
            if plan[j][0][1] == other_plan[j][0][1] or plan[j][1][1] == other_plan[j][1][1]:
                constraints.append(Constraint(agent=agent_i, loc_from=(plan[j-1][0][1], plan[j-1][1][1]), loc_to=(plan[j][0][1], plan[j][1][1]), time=j))

    return constraints    # [ConstraintObject0, ..., ConstraintObjectn]

def CBS(initial_states):
    is_single = False
    root = Node(initial_states)
    open = set()
    open.add(root)

    while open:
        P = min(open, key=lambda x: x.cost)
        C = []

        for path in P.paths:
            C.append(validate(path, P.paths))      # C is the set of constraints. Here we add the constraints for each path

        C = list(filter(None, C))
        print("Constraints: ", C,flush=True)
        if len(C) < 1:
            print(P.plans)
            print("Found solution")
            print("Positions: ", P.paths)
            if len(P.plans) == 1:
                print("One agent")
                solution = P.plans[0]
                is_single = True
            else:
                print("Multiple agents")
                solution = [list(x) for x in zip(*P.plans)]
            return solution, is_single       # Found solution, return solution in joint action normal form
        
        for constraint_set in C:                # Iter through each constraint set (the n of constraints after the validation of a single path)
            A = Node(initial_states)            # Initialize node
            A.constraints = P.constraints + constraint_set  
            A.plans, A.paths = plans_from_states(A.initial_states)
            A.cost = len(max(A.plans))
            open.add(A)

    return None