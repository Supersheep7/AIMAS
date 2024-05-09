import memory
import time
import sys

from action import Action
globals().update(Action.__members__)

start_time = time.perf_counter()

def search(initial_state, frontier):
    
    output_fixed_solution = False

    if output_fixed_solution:
        # Part 1: 
        # The agents will perform the sequence of actions returned by this method.
        # Try to solve a few levels by hand, enter the found solutions below, and run them:

        return [
            [MoveS],
        ]

    else:

        # Part 2:
        # Now try to implement the Graph-Search algorithm from R&N figure 3.7
        # In the case of "failure to find a solution" you should return None.
        # Some useful methods on the state class which you will need to use are:

        # state.is_goal_state() - Returns true if the state is a goal state.
        # state.extract_plan() - Returns the list of actions used to reach this state.
        # state.get_expanded_states() - Returns a list containing the states reachable from the current state.
        # You should also take a look at frontier.py to see which methods the Frontier interface exposes
        
        # print_search_status(expanded, frontier): As you can see below, the code will print out status
        # (#expanded states, size of the frontier, #generated states, total time used) for every 1000th node
        # generated.
        # You should also make sure to print out these stats when a solution has been found, so you can keep
        # track of the exact total number of states generated!!
   

        iterations = 0

        frontier.add(initial_state)
        explored = set()

        while True:

            iterations += 1
            if iterations % 1000 == 0:
                print_search_status(explored, frontier)

            if memory.get_usage() > memory.max_usage:
                print_search_status(explored, frontier)
                print('Maximum memory usage exceeded.', file=sys.stderr, flush=True)
                return None

            
            if frontier.is_empty():
                print("Big bomboclat", flush=True)
                return None

            is_constrained = False
            current_state = frontier.pop()
            current_time = current_state.g+1
            current_constraints = current_state.constraints
            constraint_times = [constraint.time for constraint in current_constraints]
            v = None
            t = None
            if current_constraints:
                v = current_constraints[0].loc_to[0]
                t = constraint_times[0]
            is_constraint_step = None
            if current_time in constraint_times:
                is_constraint_step = current_time
            coords = (current_state.agent_rows, current_state.agent_cols)
            coords = (coords[0][0], coords[1][0])
            if v is not None and t is not None:
                if v == coords and t == current_time:
                    is_constrained == True
                    
            if current_state.is_goal_state():
            # Solution found
                print_search_status(explored, frontier)
                plan, plan_repr = current_state.extract_plan()
                return plan, plan_repr         

            # explored.add(current_state)
            
            expanded_states = current_state.get_expanded_states()
            for child_state in expanded_states:
               # print("Child state:",child_state.agent_cols, child_state.agent_rows, current_time-1, flush=True)
                if (child_state, is_constraint_step) not in explored:
                #    print("Added to frontier", flush=True)
                    frontier.add(child_state)
                    explored.add((child_state, is_constraint_step))

            
            # print_search_status(explored, frontier)
        

def print_search_status(explored, frontier):
    status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
    elapsed_time = time.perf_counter() - start_time
    print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)