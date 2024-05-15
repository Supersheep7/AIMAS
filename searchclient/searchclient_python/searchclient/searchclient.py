import argparse
import sys
import time
import memory
from cbs import CBS
from levelparser import parse

class SearchClient:
    
    @staticmethod

    def print_search_status(start_time, explored, frontier):
        status_template = '#Expanded: {:8,}, #Frontier: {:8,}, #Generated: {:8,}, Time: {:3.3f} s\n[Alloc: {:4.2f} MB, MaxAlloc: {:4.2f} MB]'
        elapsed_time = time.perf_counter() - start_time
        print(status_template.format(len(explored), frontier.size(), len(explored) + frontier.size(), elapsed_time, memory.get_usage(), memory.max_usage), file=sys.stderr, flush=True)

    @staticmethod
    def main(args) -> None:
        # Use stderr to print to the console.
        print('SearchClient initializing. I am sending this using the error output stream.', file=sys.stderr, flush=True)
        
        # Send client name to server.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding='ASCII')
        print('Flower', flush=True)
        
        # We can also print comments to stdout by prefixing with a #.
        print('#This is a comment.', flush=True)
        
        # Parse the level.
        server_messages = sys.stdin
        if hasattr(server_messages, "reconfigure"):
            server_messages.reconfigure(encoding='ASCII')
        
        initial_states = parse(server_messages)

        joint_plan, is_single = CBS(initial_states)

        # Print plan to server.
        if joint_plan is None:
            print('Unable to solve level.', file=sys.stderr, flush=True)
            sys.exit(0)

        else:
            print('Found solution of length {}.'.format(len(joint_plan)), file=sys.stderr, flush=True)
           # print("Solutions:", joint_plan, file=sys.stderr, flush=True)
            for joint_action in joint_plan:
                if is_single:
                    print("|".join(a.name_+"@"+a.name for a in joint_action), flush=True)
                else:
                    print("|".join(a[0].name_+"@"+a[0].name for a in joint_action), flush=True)
                # We must read the server's response to not fill up the stdin buffer and block the server.
                response = server_messages.readline()

if __name__ == '__main__':
    # Program arguments.
    parser = argparse.ArgumentParser(description='Simple client based on state-space graph search.')
    parser.add_argument('--max-memory', metavar='<MB>', type=float, default=2048.0, help='The maximum memory usage allowed in MB (soft limit, default 2048).')
    
    strategy_group = parser.add_mutually_exclusive_group()
    strategy_group.add_argument('-cbs', action='store_true', dest='cbs', help='Use the CBS strategy.')
    
    args = parser.parse_args()
    
    # Set max memory usage allowed (soft limit).
    memory.max_usage = args.max_memory
    
    # Run client.
    SearchClient.main(args)