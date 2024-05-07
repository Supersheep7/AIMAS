from state import State, Constraint
from frontier import FrontierBestFirstWidth
from heuristic import HeuristicBFWS
from graphsearch import search
from action import Action

class Node():

    def __init__(self, states, constraints=[]):
        self.initial_states = states
        self.constraints = constraints
        for state in self.initial_states:
            state.constraints.extend(self.constraints)
        self.plans, self.paths = plans_from_states(self.initial_states)
        print("Paths:", self.paths, flush=True)
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
            if initial_state.constraints:
                print("initial state constraint:", initial_state.constraints[0].loc_to ,initial_state.constraints[0].time, flush=True)
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
    """
    Generates constraints based on conflicts between the given plan and other plans in the plan_list,
    including illegal crossings.

    Parameters:
    - plan: The plan to validate for conflicts.
    - plan_list: List of all plans to compare against.

    Returns:
    - List[Constraint]: A list of constraints identified from conflicts.
    """
    agent_i_full = plan[0][0][0]  # Something like 'AgentAt0'
    agent_i = agent_i_full.split('AgentAt')[-1]  # Extract just the number after 'AgentAt'

    other_plans = [lst for lst in plan_list if lst is not plan]
    constraints = []

    for other_plan in other_plans:
        # Ensure both plans are of equal length
        plan, other_plan = match_length(plan, other_plan)
        for j in range(1, len(plan)):
            # Get current and previous states for both plans
            agent_state_current = plan[j][0][1]
            agent_state_previous = plan[j - 1][0][1]
            box_state_current = plan[j][1][1] if len(plan[j]) > 1 else None
            box_state_previous = plan[j - 1][1][1] if len(plan[j - 1]) > 1 else None

            other_agent_state_current = other_plan[j][0][1]
            other_agent_state_previous = other_plan[j - 1][0][1]
            other_box_state_current = other_plan[j][1][1] if len(other_plan[j]) > 1 else None
            other_box_state_previous = other_plan[j - 1][1][1] if len(other_plan[j - 1]) > 1 else None

            # Conflicting agent positions
            if agent_state_current == other_agent_state_current:
                constraints.append(Constraint(
                    agent=agent_i,
                    loc_from=(agent_state_previous, box_state_previous),
                    loc_to=(agent_state_current, box_state_current),
                    time=j+1
                ))

            # Conflicting box positions
            if box_state_current is not None and box_state_current == other_box_state_current:
                constraints.append(Constraint(
                    agent=agent_i,
                    loc_from=(agent_state_previous, box_state_previous),
                    loc_to=(agent_state_current, box_state_current),
                    time=j+1
                ))

            # Illegal crossing detection
            # Agents crossing each other
            if agent_state_current == other_agent_state_previous and agent_state_previous == other_agent_state_current:
                constraints.append(Constraint(
                    agent=agent_i,
                    loc_from=(agent_state_previous, box_state_previous),
                    loc_to=(agent_state_current, box_state_current),
                    time=j
                ))

            # Boxes crossing each other
            if box_state_current is not None and box_state_previous is not None and \
                    box_state_current == other_box_state_previous and box_state_previous == other_box_state_current:
                constraints.append(Constraint(
                    agent=agent_i,
                    loc_from=(agent_state_previous, box_state_previous),
                    loc_to=(agent_state_current, box_state_current),
                    time=j+1
                ))

            # Agent and Box crossing
            if box_state_current is not None and \
                    (agent_state_current == other_box_state_previous and agent_state_previous == other_box_state_current):
                constraints.append(Constraint(
                    agent=agent_i,
                    loc_from=(agent_state_previous, box_state_previous),
                    loc_to=(agent_state_current, box_state_current),
                    time=j+1
                ))

    return constraints  # [ConstraintObject0, ..., ConstraintObjectn]
def CBS(initial_states):
    is_single = False
    root = Node(initial_states)
    open_set = set()
    open_set.add(root)
    closed_set = set()

    while open_set:
        P = min(open_set, key=lambda x: x.cost)
        open_set.remove(P)
        closed_set.add(P)

        C = []
        for path in P.paths:
            C.extend(validate(path, P.paths))  # C is the set of constraints. Here we add the constraints for each path

        if not C:
            print(P.plans)
            print("Found solution")
            print("Positions:", P.paths)
            if len(P.plans) == 1:
                print("One agent")
                solution = P.plans[0]
                is_single = True
            else:
                print("Multiple agents")
                solution = [list(x) for x in zip(*P.plans)]
            return solution, is_single  # Found solution, return solution in joint action normal form
        
        for constraint in C:
            # Create a new set of initial states with the constraints applied
            new_states = [State(state.agent_rows, state.agent_cols, state.boxes, state.goals, state.agents, state.constraints[:]) for state in P.initial_states]
            print("Added constraint:",constraint.loc_to,constraint.time , flush=True)
            A = Node(new_states, P.constraints + [constraint])

            if A not in closed_set:
                open_set.add(A)

    return None