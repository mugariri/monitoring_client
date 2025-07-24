from device_info_collector import DeviceInfoCollector

collector = DeviceInfoCollector()
collector.print_info()
device_info = collector.to_json()
collector.to_json_file('device_info.json')
