import memory
import time
import sys
from action import Action

globals().update(Action.__members__)

start_time = time.perf_counter()

def search(initial_state, frontier):
       
        iterations = 0

        frontier.explored.append(initial_state.atoms)
        frontier.add(initial_state)

        while True:
            iterations += 1
            if iterations % 1000 == 0:
                print_search_status(frontier.explored, frontier)

            if memory.get_usage() > memory.max_usage:
                print_search_status(frontier.explored, frontier)
                print('Maximum memory usage exceeded.', file=sys.stderr, flush=True)
                return None

            if frontier.is_empty():
                plan, plan_repr = None, None
                return plan, plan_repr
            
            current_state = frontier.pop()
            current_time = current_state.g+1
            current_constraints = current_state.constraints
            sorted_constraints = sorted(current_constraints, key=lambda x: x.time)

            # Plan from constraints
            if len(sorted_constraints) > 0:
                
                if current_state.is_goal_state() and current_time > sorted_constraints[-1].time:
                    plan, plan_repr = current_state.extract_plan()
                    return plan, plan_repr
            
            # Plan no constraint
            else:
                if current_state.is_goal_state():
                    plan, plan_repr = current_state.extract_plan()
                    return plan, plan_repr
                     
            expanded_states = current_state.get_expanded_states()

            frontier.explored.append(current_state.atoms)

            for child_state in expanded_states:
                
                if not frontier.contains(child_state) and child_state.constraint_step == False:
                    frontier.add(child_state)        

def print_search_status(explored, frontier):
    status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
    elapsed_time = time.perf_counter() - start_time
    print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)