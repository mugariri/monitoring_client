import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime
import threading

from device_info_collector import DeviceInfoCollector, API_HOST, send_device_info, logger

collector = DeviceInfoCollector()
def run_app():
    try:
        logger.info("Starting device information collection")


        # Check for command line arguments
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--dashboard":
            collector.display_live_dashboard()
        else:
            collector.print_info()
            device_info = collector.to_json()

            # Save to JSON file
            with open('device_info.json', 'w') as f:
                f.write(device_info)
            logger.info("Device information has been saved to 'device_info.json'")

            # Replace with your WebSocket URL
            websocket_url = f"ws://{API_HOST}/ws/device-tracker/"
            asyncio.run(send_device_info(websocket_url, device_info=device_info))

    except Exception as e:
        logger.error(f"Error in main execution: {e}")

def run_app_threaded():
    thread = threading.Thread(target=run_app)
    thread.daemon = True
    thread.start()
class DeviceInfoUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Information Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Arial', 10, 'bold'))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'))

        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create header
        self.create_header()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Create tabs
        self.create_local_info_tab()
        self.create_api_info_tab()
        self.create_performance_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            style='Status.TLabel'
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))

        # Initialize with local data
        self.update_local_info()
        self.fetch_api_data_threaded() # Fetch API data on initialization
        self.schedule_run_app()
    def schedule_run_app(self):
        run_app_threaded()
        # Schedule next run in 5000 milliseconds (5 seconds)
        self.root.after(5000, self.schedule_run_app)

    def create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Device Information Dashboard",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)

        refresh_btn = ttk.Button(
            header_frame,
            text="Refresh All",
            command=self.refresh_all
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 5))

        api_refresh_btn = ttk.Button(
            header_frame,
            text="Refresh API Data",
            command=self.fetch_api_data_threaded
        )
        api_refresh_btn.pack(side=tk.RIGHT, padx=5)

    def create_local_info_tab(self):
        self.local_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.local_tab, text="Local Information")

        # Create paned window for left/right split
        paned = ttk.PanedWindow(self.local_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left pane - Basic info
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="System Information", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))

        self.basic_info_frame = ttk.Frame(left_frame)
        self.basic_info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Right pane - Software list
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Installed Software", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))

        # Treeview for software
        self.software_tree = ttk.Treeview(
            right_frame,
            columns=('name', 'version', 'publisher', 'install_date'),
            show='headings'
        )
        self.software_tree.heading('name', text='Name')
        self.software_tree.heading('version', text='Version')
        self.software_tree.heading('publisher', text='Publisher')
        self.software_tree.heading('install_date', text='Install Date')

        self.software_tree.column('name', width=200)
        self.software_tree.column('version', width=100)
        self.software_tree.column('publisher', width=150)
        self.software_tree.column('install_date', width=100)

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.software_tree.yview)
        self.software_tree.configure(yscroll=scrollbar.set)

        self.software_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_api_info_tab(self):
        self.api_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.api_tab, text="API Information")

        # Control frame
        control_frame = ttk.Frame(self.api_tab)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="Enter Hostname:").pack(side=tk.LEFT, padx=(0, 5))
        self.hostname_entry = ttk.Entry(control_frame, width=30)
        self.hostname_entry.pack(side=tk.LEFT, padx=(0, 5))
        fetch_btn = ttk.Button(control_frame, text="Fetch Data", command=self.fetch_api_data_threaded)
        fetch_btn.pack(side=tk.LEFT)

        # API info display frame
        self.api_info_display = ttk.Frame(self.api_tab)
        self.api_info_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Labels for API data
        ttk.Label(self.api_info_display, text="Device Details from API", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))

        self.api_labels = {}
        info_labels = [
            ("Hostname:", "hostname"),
            ("IP Address:", "ip_address"),
            ("Department:", "department"),
            ("OS:", "os"),
            ("Status:", "status"),
            ("Device Type:", "device_type"),
            ("CPU Usage:", "cpu_usage"),
            ("Memory Usage:", "memory_usage"),
            ("Disk Usage:", "disk_usage"),
            ("Download Speed:", "network_download_speed"),
            ("Upload Speed:", "network_upload_speed"),
            ("Last Updated:", "last_updated")
        ]

        for i, (label_text, key) in enumerate(info_labels):
            frame = ttk.Frame(self.api_info_display)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label_text, width=20, anchor=tk.W).pack(side=tk.LEFT)
            if key == 'status':
                self.api_labels[key] = ttk.Label(frame,  anchor=tk.W)
            else:
                self.api_labels[key] = ttk.Label(frame, text="N/A", anchor=tk.W)

            self.api_labels[key].pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_performance_tab(self):
        self.performance_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.performance_tab, text="Performance Metrics")

        # CPU Usage
        ttk.Label(self.performance_tab, text="CPU Usage", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W,
                                                                                      pady=(0, 5))
        self.cpu_usage = ttk.Label(self.performance_tab, text="0.0%")
        self.cpu_usage.grid(row=1, column=0, sticky=tk.W, padx=5)

        # Memory Usage
        ttk.Label(self.performance_tab, text="Memory Usage", style='Header.TLabel').grid(row=0, column=1, sticky=tk.W,
                                                                                         pady=(0, 5))
        self.memory_usage = ttk.Label(self.performance_tab, text="0.0% (0.0 GB / 0.0 GB)")
        self.memory_usage.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Disk Usage
        ttk.Label(self.performance_tab, text="Disk Usage", style='Header.TLabel').grid(row=0, column=2, sticky=tk.W,
                                                                                       pady=(0, 5))
        self.disk_usage = ttk.Label(self.performance_tab, text="0.0% (0.0 GB / 0.0 GB)")
        self.disk_usage.grid(row=1, column=2, sticky=tk.W, padx=5)

        # Network
        ttk.Label(self.performance_tab, text="Network", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W,
                                                                                    pady=(10, 5))
        self.network_download = ttk.Label(self.performance_tab, text="Download: 0.0 MB/s")
        self.network_download.grid(row=3, column=0, sticky=tk.W, padx=5)
        self.network_upload = ttk.Label(self.performance_tab, text="Upload: 0.0 MB/s")
        self.network_upload.grid(row=4, column=0, sticky=tk.W, padx=5)

        # Alerts
        ttk.Label(self.performance_tab, text="Active Alerts", style='Header.TLabel').grid(row=2, column=1, columnspan=2,
                                                                                          sticky=tk.W, pady=(10, 5))
        self.alerts_text = tk.Text(
            self.performance_tab,
            height=5,
            width=60,
            wrap=tk.WORD,
            font=('Arial', 9),
            padx=5,
            pady=5,
            state=tk.DISABLED
        )
        self.alerts_text.grid(row=3, column=1, columnspan=2, rowspan=2, sticky=tk.W + tk.E, padx=5)

        # Processes
        ttk.Label(self.performance_tab, text="Top Processes", style='Header.TLabel').grid(row=5, column=0, columnspan=3,
                                                                                          sticky=tk.W, pady=(10, 5))

        self.process_tree = ttk.Treeview(
            self.performance_tab,
            columns=('pid', 'name', 'cpu', 'memory', 'status'),
            show='headings',
            height=10
        )
        self.process_tree.heading('pid', text='PID')
        self.process_tree.heading('name', text='Name')
        self.process_tree.heading('cpu', text='CPU %')
        self.process_tree.heading('memory', text='Memory %')
        self.process_tree.heading('status', text='Status')

        self.process_tree.column('pid', width=50)
        self.process_tree.column('name', width=150)
        self.process_tree.column('cpu', width=60)
        self.process_tree.column('memory', width=70)
        self.process_tree.column('status', width=80)

        scrollbar = ttk.Scrollbar(
            self.performance_tab,
            orient=tk.VERTICAL,
            command=self.process_tree.yview
        )
        self.process_tree.configure(yscrollcommand=scrollbar.set)

        self.process_tree.grid(row=6, column=0, columnspan=3, sticky=tk.W + tk.E + tk.N + tk.S)
        scrollbar.grid(row=6, column=3, sticky=tk.N + tk.S)

        # Configure grid weights
        self.performance_tab.columnconfigure(0, weight=1)
        self.performance_tab.columnconfigure(1, weight=1)
        self.performance_tab.columnconfigure(2, weight=1)

    def update_local_info(self):
        try:
            system_info = collector.system_info

            # Clear existing widgets in basic info frame
            for widget in self.basic_info_frame.winfo_children():
                widget.destroy()

            # Add basic info labels
            info_pairs = [
                ("Hostname:", system_info['hostname']),
                ("IP Address:", system_info['ip_address']),
                ("MAC Address:", system_info['mac_address']),
                ("OS:", f"{system_info['os_info']['system']} {system_info['os_info']['release']}"),
                ("System Manufacturer:", system_info['system_manufacturer']),
                ("System Model:", system_info['system_model']),
                ("Serial Number:", system_info['serial_number'])
            ]

            for i, (label, value) in enumerate(info_pairs):
                ttk.Label(self.basic_info_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
                ttk.Label(self.basic_info_frame, text=value).grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)

            # Update software tree
            self.software_tree.delete(*self.software_tree.get_children())
            for software in system_info['installed_software']:
                self.software_tree.insert('', tk.END, values=(
                    software.get('name', 'Unknown'),
                    software.get('version', 'Unknown'),
                    software.get('publisher', 'Unknown'),
                    software.get('install_date', 'Unknown')
                ))

            # Update performance metrics
            self.update_performance_metrics(system_info['performance_metrics'])

            # Set hostname in API tab if empty
            if not self.hostname_entry.get():
                self.hostname_entry.insert(0, system_info['hostname'])

            self.status_var.set("Local information updated successfully")
        except Exception as e:
            self.status_var.set(f"Error updating local info: {str(e)}")
            messagebox.showerror("Error", f"Failed to update local information:\n{str(e)}")

    def update_performance_metrics(self, perf_metrics):
        try:
            # CPU
            cpu_usage = perf_metrics['cpu']['overall_usage']
            self.cpu_usage.config(text=f"{cpu_usage:.1f}%")

            # Memory
            mem = perf_metrics['memory']
            mem_text = f"{mem['percent']:.1f}% ({mem['used'] / (1024 ** 3):.1f} GB / {mem['total'] / (1024 ** 3):.1f} GB)"
            self.memory_usage.config(text=mem_text)

            # Disk
            if perf_metrics['disks']:
                disk = perf_metrics['disks'][0]
                disk_text = f"{disk['percent']:.1f}% ({disk['used'] / (1024 ** 3):.1f} GB / {disk['total'] / (1024 ** 3):.1f} GB)"
                self.disk_usage.config(text=disk_text)

            # Network
            net_io = perf_metrics['network']
            download_speed = net_io['bytes_recv'] / (1024 * 1024)  # MB
            upload_speed = net_io['bytes_sent'] / (1024 * 1024)  # MB
            self.network_download.config(text=f"Download: {download_speed:.2f} MB")
            self.network_upload.config(text=f"Upload: {upload_speed:.2f} MB")

            # Alerts
            alerts = collector.get_active_alerts()
            self.alerts_text.config(state=tk.NORMAL)
            self.alerts_text.delete(1.0, tk.END)

            if alerts:
                for alert in alerts:
                    self.alerts_text.insert(tk.END, f"⚠ {alert['type']}: {alert['message']}\n")
                self.alerts_text.tag_config("alert", foreground="red")
            else:
                self.alerts_text.insert(tk.END, "No active alerts")
                self.alerts_text.tag_config("normal", foreground="green")

            self.alerts_text.config(state=tk.DISABLED)

            # Processes
            self.process_tree.delete(*self.process_tree.get_children())
            processes = collector.get_running_processes(10)
            for proc in processes:
                self.process_tree.insert('', tk.END, values=(
                    proc['pid'],
                    proc['name'],
                    f"{proc['cpu']:.1f}",
                    f"{proc['memory']:.1f}",
                    proc['status']
                ))

        except Exception as e:
            self.status_var.set(f"Error updating performance metrics: {str(e)}")

    def fetch_api_data_threaded(self):
        """Start API fetch in a separate thread to prevent UI freezing"""
        self.status_var.set("Fetching API data...")
        threading.Thread(target=self.fetch_api_data, daemon=True).start()

    def fetch_api_data(self):
        try:
            hostname = self.hostname_entry.get().strip()
            if not hostname:
                messagebox.showwarning("Warning", "Please enter a hostname")
                return

            # Simulate API call (replace with actual API call)
            api_url = f"http://{API_HOST}/api/devices/by-hostname/{hostname}/"
            response = requests.get(api_url).json()

            # Define status color mapping
            status_colors = {
                "compliant": "green",
                "Compliant": "green",
                "non-compliant": "red",
                "Non-Compliant": "red",
                "warning": "orange",
                "Warning": "orange"
            }

            # Update the API labels with the fetched data
            if response:
                self.api_labels['hostname'].config(text=response.get('hostname', 'N/A'))
                self.api_labels['ip_address'].config(text=response.get('ip_address', 'N/A'))
                self.api_labels['department'].config(text=response.get('department', 'N/A'))
                self.api_labels['os'].config(text=response.get('os', 'N/A'))

                status = response.get('status', 'N/A')
                self.api_labels['status'].config(text=status)
                self.api_labels['status'].config(foreground=status_colors.get(status, 'black'))

                self.api_labels['device_type'].config(text=response.get('device_type', 'N/A'))
                self.api_labels['cpu_usage'].config(text=f"{response.get('cpu_usage', 0.0):.2f}%")
                self.api_labels['memory_usage'].config(text=f"{response.get('memory_usage', 0.0):.2f}%")
                self.api_labels['disk_usage'].config(text=f"{response.get('disk_usage', 0.0):.2f}%")
                self.api_labels['network_download_speed'].config(text=f"{response.get('network_download_speed', 0.0):.2f} MB/s")
                self.api_labels['network_upload_speed'].config(text=f"{response.get('network_upload_speed', 0.0):.2f} MB/s")
                self.api_labels['last_updated'].config(text=response.get('last_updated', 'N/A'))

                self.status_var.set(f"API data fetched successfully for {hostname}")
            else:
                self.status_var.set(f"No data found for hostname: {hostname}")
                messagebox.showinfo("Info", f"No data found for hostname: {hostname}")

        except requests.exceptions.RequestException as e:
            self.status_var.set(f"Error fetching API data: {str(e)}")
            messagebox.showerror("Error", f"Failed to fetch API data:\n{str(e)}")
        except json.JSONDecodeError as e:
            self.status_var.set(f"Error decoding JSON: {str(e)}")
            messagebox.showerror("Error", f"Error decoding JSON response:\n{str(e)}")
        except Exception as e:
            self.status_var.set(f"Error processing API data: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")

    def refresh_all(self):
        self.update_local_info()
        self.fetch_api_data_threaded()


if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceInfoUI(root)
    root.mainloop()
