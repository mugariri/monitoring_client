import psutil
import json


def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            process = psutil.Process(proc.info['pid'])

            # Initialize memory attributes with None
            memory_shared = None
            memory_data = None
            memory_stack = None

            # Get memory info and check for attributes
            mem_info = process.memory_info()
            if hasattr(mem_info, 'shared'):
                memory_shared = mem_info.shared / (1024 * 1024)
            if hasattr(mem_info, 'data'):
                memory_data = mem_info.data / (1024 * 1024)
            if hasattr(mem_info, 'stack'):
                memory_stack = mem_info.stack / (1024 * 1024)

            # Initialize IO counters with None for optional fields
            io_read_chars = None
            io_write_chars = None
            io_counters = process.io_counters()
            if hasattr(io_counters, 'read_chars'):
                io_read_chars = io_counters.read_chars
            if hasattr(io_counters, 'write_chars'):
                io_write_chars = io_counters.write_chars

            process_info = {
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'status': proc.info['status'],
                'create_time': process.create_time(),
                'exe': process.exe(),
                'cmdline': process.cmdline(),
                'num_ctx_switches': process.num_ctx_switches()._asdict() if hasattr(process,
                                                                                    'num_ctx_switches') else None,
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None,  # Number of file descriptors
                'cwd': process.cwd() if hasattr(process, 'cwd') else None,  # Current working directory
                'memory': {
                    'rss': mem_info.rss / (1024 * 1024),
                    'vms': mem_info.vms / (1024 * 1024),
                    'percent': process.memory_percent(),
                    'shared': memory_shared,
                    'data': memory_data,
                    'stack': memory_stack
                },
                'cpu': {
                    'percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'cpu_times': process.cpu_times()._asdict(),
                    'affinity': process.cpu_affinity() if hasattr(process, 'cpu_affinity') else None,  # CPU affinity
                },
                'io': {
                    'read_bytes': io_counters.read_bytes,
                    'write_bytes': io_counters.write_bytes,
                    'read_chars': io_read_chars,
                    'write_chars': io_write_chars,
                },
                'open_files': [f.path for f in process.open_files()] if hasattr(process, 'open_files') else [],
                # List of open files
                'connections': [{
                    'fd': c.fd,
                    'family': str(c.family),
                    'type': str(c.type),
                    'laddr': c.laddr._asdict() if c.laddr else None,
                    'raddr': c.raddr._asdict() if c.raddr else None,
                    'status': str(c.status)
                } for c in process.net_connections()] if hasattr(process, 'net_connections') else [],
                'num_connections': len(process.net_connections()) if hasattr(process, 'net_connections') else 0,
                'threads': [{
                    'id': t.id,
                    'user_time': t.user_time,
                    'system_time': t.system_time
                } for t in process.threads()] if hasattr(process, 'threads') else [],
                'num_ctx_switches': process.num_ctx_switches()._asdict() if hasattr(process,
                                                                                    'num_ctx_switches') else None,
                'parent_pid': process.ppid() if hasattr(process, 'ppid') else None,
                'nice': process.nice() if hasattr(process, 'nice') else None,  # Process nice value (priority)
            }

            # Get username for Windows
            if hasattr(process, 'username'):
                process_info['username'] = process.username()

            # Get uids and gids for Unix-based systems
            if hasattr(process, 'uids'):
                process_info['uids'] = process.uids()._asdict()
            if hasattr(process, 'gids'):
                process_info['gids'] = process.gids()._asdict()

            processes.append(process_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes


def save_to_json(processes, filename):
    with open(filename, 'w') as f:
        json.dump(processes, f, indent=4)


def main():
    processes = get_processes()
    save_to_json(processes, 'processes.json')
    for proc in processes:
        print(f"PID: {proc['pid']}, Name: {proc['name']}, Status: {proc['status']}")
        print(f"  Create Time: {proc['create_time']}")
        print(f"  Executable: {proc['exe']}")
        print(f"  Command Line: {proc['cmdline']}")
        print(f"  Current Working Directory (CWD): {proc['cwd']}")
        print(f"  Parent PID: {proc['parent_pid']}")
        print(f"  Nice Value: {proc['nice']}")
        print(f"  Context Switches: {proc['num_ctx_switches']}")
        print(f"  Number of File Descriptors: {proc['num_fds']}")

        print(
            f"  Memory: {proc['memory']['rss']:.2f} MB RSS, {proc['memory']['vms']:.2f} MB VMS, {proc['memory']['percent']:.2f}%")

        # Only print if the attributes exist
        if proc['memory']['shared'] is not None:
            print(f"    Shared Memory: {proc['memory']['shared']:.2f} MB")
        if proc['memory']['data'] is not None:
            print(f"    Data Memory: {proc['memory']['data']:.2f} MB")
        if proc['memory']['stack'] is not None:
            print(f"    Stack Memory: {proc['memory']['stack']:.2f} MB")

        print(f"  CPU: {proc['cpu']['percent']:.2f}%, {proc['cpu']['num_threads']} threads")
        print(f"  CPU Times: {proc['cpu']['cpu_times']}")
        print(f"  CPU Affinity: {proc['cpu']['affinity']}")
        print(f"  IO: {proc['io']['read_bytes']} bytes read, {proc['io']['write_bytes']} bytes written")
        if proc['io']['read_chars'] is not None:
            print(f"  IO (Chars): {proc['io']['read_chars']} chars read, {proc['io']['write_chars']} chars written")

        print(f"  Open Files ({len(proc['open_files'])}): {proc['open_files']}")
        print(f"  Connections ({proc['num_connections']}):")
        for conn in proc['connections']:
            print(f"    FD: {conn['fd']}, Family: {conn['family']}, Type: {conn['type']}, "
                  f"Laddr: {conn['laddr']}, Raddr: {conn['raddr']}, Status: {conn['status']}")
        print(f"  Threads ({len(proc['threads'])}):")
        for thread in proc['threads']:
            print(
                f"    ID: {thread['id']}, User Time: {thread['user_time']:.2f}, System Time: {thread['system_time']:.2f}")

        # Print username if available
        if 'username' in proc:
            print(f"  Username: {proc['username']}")

        # Print uids and gids if available
        if 'uids' in proc:
            print(f"  UIDs: {proc['uids']}")
        if 'gids' in proc:
            print(f"  GIDs: {proc['gids']}")

        print("-" * 40)  # Separator for better readability


if __name__ == "__main__":
    main()