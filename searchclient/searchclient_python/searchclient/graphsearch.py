import memory
import time
import sys

from action import Action
from state import atoms


globals().update(Action.__members__)

start_time = time.perf_counter()

def search(initial_state, frontier):
       
        iterations = 0

        frontier.explored.append(atoms(initial_state))
        frontier.add(initial_state)
        # print("Started search for worker", initial_state.worker_name)

        while True:
            iterations += 1
            if iterations % 1000 == 0:
                print_search_status(frontier.explored, frontier)

            if memory.get_usage() > memory.max_usage:
                print_search_status(frontier.explored, frontier)
                print('Maximum memory usage exceeded.', file=sys.stderr, flush=True)
                return None

            if frontier.is_empty():
                # print("Big bomboclat for", initial_state.worker_name)
                plan, plan_repr = None, None
                return plan, plan_repr
            
            current_state = frontier.pop()
            current_time = current_state.g+1
            current_constraints = current_state.constraints
            constraint_times = [constraint.time for constraint in current_constraints]
            constraint_locations = [(constraint.loc_to) for constraint in current_constraints]
            # print("Current constraint times:", constraint_times, flush=True)
            # print("Current constraint locations:", [(constraint.loc_from, constraint.loc_to) for constraint in current_constraints], flush=True)
            is_constraint_step = None
            #if (current_state.agent_cols, current_state.agent_rows) == ([3],[2]) and current_state.worker_name == "worker1":
            #    print("LOOK FOR CONSTRAINTS\n\n\n\n coords:", current_state.worker_name, current_state.agent_cols, current_state.agent_rows, flush=True)
            # print(current_state.worker_name, current_state.agent_cols, current_state.agent_rows)
            if current_state.is_goal_state():
                #print("Solution found", flush=True)
            # Solution found
                plan, plan_repr = current_state.extract_plan()
                return plan, plan_repr         

            expanded_states = current_state.get_expanded_states()

            frontier.explored.append(atoms(current_state))

            for child_state in expanded_states:
                #if current_state.agent_rows == [3] and current_state.agent_cols == [5] and current_state.worker_name == 1:
                    #print("Child state:",child_state.agent_cols, child_state.agent_rows, current_time-1, flush=True)
                # print(child_state.agent_rows, child_state.agent_cols, child_state.constraint_step)
                # print("Child state:",child_state.agent_cols, child_state.agent_rows, current_time-1, flush=True)
                if not frontier.contains(child_state) and child_state.constraint_step == False:
                #    print("Added to frontier", flush=True)
                    frontier.add(child_state)
                                
            # print_search_status(explored, frontier)
        

def print_search_status(explored, frontier):
    status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
    elapsed_time = time.perf_counter() - start_time
    print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)