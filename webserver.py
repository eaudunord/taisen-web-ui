#!/usr/bin/env python3
#web_server_version=2025.09.06.1441

import sys
import subprocess
import os
import threading
import time
import json
import glob
import io
import requests

if sys.version_info[0] >= 3:
    import http.server as httpserver
    import socketserver
    import urllib.parse as urlparse
else:
    import SimpleHTTPServer as httpserver
    import SocketServer as socketserver
    import urlparse

PORT = 1999
current_process = None
process_output = []

class LinkCableHandler(httpserver.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = open("index.html", "rb").read()
            
            self.wfile.write(html)
            
        elif self.path.startswith('/start'):
            self.handle_start_request()
        elif self.path.startswith('/stop'):
            self.handle_stop_request()
        elif self.path == '/status':
            self.handle_status_request()
        elif self.path == '/logs':
            self.handle_logs_request()
        elif self.path == '/ports':
            self.handle_ports_request()
        elif self.path == '/dreampi_start':
            self.handle_dreampi_start()
        elif self.path == '/dreampi_stop':
            self.handle_dreampi_stop()
        elif self.path == '/dreampi_status':
            self.handle_dreampi_status()
        elif self.path == '/fetch_updates':
            self.fetch_updates()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_start_request(self):
        global current_process, process_output
        
        query = urlparse.urlparse(self.path).query
        params = urlparse.parse_qs(query)
        
        config = {}
        for key, value in params.items():
            config[key] = value[0] if value else ''
        
        print("DEBUG: Received parameters:", config)
        
        try:
            # Validate required parameters
            if not config.get('com_port'):
                raise Exception("COM port not specified")
            if not config.get('game'):
                raise Exception("Game not specified")
            if not config.get('matching'):
                raise Exception("Connection method not specified")
            
            # Build command arguments
            args = ["python", "link_cable.py"]
            args.append("com={}".format(config['com_port']))
            args.append("game={}".format(config['game']))

            if config.get('ftdi'):
                args.append("ftdi=" + config['ftdi'])
            
            if config['matching'] == '1':
                args.append("matching=1")
            elif config['matching'] == '2':
                if not config.get('ip_address'):
                    raise Exception("IP address required for direct connection")
                args.append("address={}".format(config['ip_address']))
                if config.get('connection_type') == '1':
                    args.append("state=waiting")
                else:
                    args.append("state=calling")
            
            command_str = ' '.join(args)
            print("DEBUG: Executing command:", command_str)
            
            # clear any old processes
            try:
                command = "ps -ef | grep  'link_cable.py' | grep -v grep | awk '{print $2}'"

                stale_processes = subprocess.check_output(command, shell=True).decode().split('\n')
                [subprocess.check_output(["kill", "-9", pid]) for pid in stale_processes if len(stale_processes) > 0 and pid != '']
            except:
                pass

            # Start the process
            current_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=False,
                bufsize=1
            )
            
            # Clear previous output
            process_output = []
            
            # Start output capture thread
            def capture_output():
                try:
                    for line in io.TextIOWrapper(current_process.stdout, encoding="utf-8"):
                    # for line in iter(current_process.stdout.readline, ''):
                        if line:
                            line = line.strip()
                            process_output.append(line)
                            # print("LINK_CABLE:", line)
                            
                            # Keep only last 50 lines
                            if len(process_output) > 50:
                                process_output.pop(0)
                except:
                    pass
            
            # Python 3.5 compatible threading
            t = threading.Thread(target=capture_output)
            t.daemon = True
            t.start()
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {
                "success": True,
                "message": "Link cable started successfully",
                "command": command_str
            }
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print("ERROR:", str(e))
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(result).encode())

    def handle_dreampi_start(self):
        try:
            start_dreampi = subprocess.check_output(["sudo", "service", "dreampi", "start"])
            result = subprocess.run(["systemctl", "is-active", "dreampi"], stdout=subprocess.DEVNULL)
            if result.returncode == 0:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                result = {"success": True, "message": "Dreampi service is running"}
                self.wfile.write(json.dumps(result).encode())
                process_output.append("Dreampi service started")
            else:
                process_output.append("Error. Dreampi service not started")
                raise Exception("Dreampi service not active")

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(result).encode())

    def handle_dreampi_stop(self):
        try:
            stop_dreampi = subprocess.check_output(["sudo", "service", "dreampi", "stop"])
            result = subprocess.run(["systemctl", "is-active", "dreampi"], stdout=subprocess.DEVNULL)
            if result.returncode != 0:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                result = {"success": True, "message": "Dreampi service stopped"}
                self.wfile.write(json.dumps(result).encode())
                process_output.append("Dreampi service stopped")
            else:
                process_output.append("Error. Dreampi service still active")
                raise Exception("Error. Dreampi service still active")

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(result).encode())
            process_output.append("Error executing Dreampi stop command")

    def handle_dreampi_status(self):
        try:
            result = subprocess.run(["systemctl", "is-active", "dreampi"], stdout=subprocess.DEVNULL)
            if result.returncode == 0:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                result = {"success": True, "message": "Dreampi service is running"}
                self.wfile.write(json.dumps(result).encode())
            else:
                raise Exception("Dreampi service not active")

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(result).encode())
    
    def handle_stop_request(self):
        global current_process
        stale_processes = None
        
        try:
            if current_process:
                current_process.terminate()
                try:
                    current_process.wait()
                except:
                    current_process.kill()
                current_process = None
                print("DEBUG: Link cable process stopped")

            command = "ps -ef | grep  'link_cable.py' | grep -v grep | awk '{print $2}'"

            stale_processes = subprocess.check_output(command, shell=True).decode().split('\n')
            [subprocess.check_output(["kill", "-9", pid]) for pid in stale_processes if len(stale_processes) > 0 and pid != '']
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {"success": True, "message": "Link cable stopped"}
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(result).encode())
    
    def handle_status_request(self):
        global current_process
        
        is_running = current_process is not None and current_process.poll() is None
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        result = {"running": is_running}
        self.wfile.write(json.dumps(result).encode())
    
    def handle_logs_request(self):
        global process_output
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        logs = '<br>'.join(process_output[-30:]) if process_output else ''
        result = {"logs": logs}
        self.wfile.write(json.dumps(result).encode())
    
    def handle_ports_request(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        ports = []
        
        try:
            # Scan for common USB serial device patterns
            patterns = ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyAMA*']
            
            for pattern in patterns:
                devices = glob.glob(pattern)
                for device in devices:
                    description = ""
                    
                    try:
                        # Try to determine device type
                        if 'ttyUSB' in device:
                            # Check if it's an FTDI device (common for coders cables)
                            try:
                                uevent_path = '/sys/class/tty/{}/device/uevent'.format(os.path.basename(device))
                                with open(uevent_path, 'r') as f:
                                    content = f.read()
                                    if 'FTDI' in content:
                                        description = "FTDI USB Serial (Likely Coders Cable)"
                                    elif 'Prolific' in content:
                                        description = "Prolific USB Serial"
                                    else:
                                        description = "USB Serial Device"
                            except:
                                description = "USB Serial Device"
                        elif 'ttyACM' in device:
                            description = "USB Communication Device"
                        elif 'ttyAMA' in device:
                            description = "Hardware UART"
                        
                        # Verify device exists and is accessible
                        if os.path.exists(device):
                            ports.append({
                                "device": device,
                                "description": description
                            })
                    except:
                        # If we can't get description, still add the device
                        ports.append({
                            "device": device,
                            "description": "Serial Device"
                        })
            
            # Sort ports by device name
            ports.sort(key=lambda x: x['device'])
            
        except Exception as e:
            print("Error detecting ports:", str(e))
        
        result = {"ports": ports}
        self.wfile.write(json.dumps(result).encode())

    def fetch_updates(self):
        global process_output
        restart_flag = False
        link_script = "https://raw.githubusercontent.com/eaudunord/dc-taisen-netplay/main/link_cable.py"
        web_server = "https://raw.githubusercontent.com/eaudunord/taisen-web-ui/main/webserver.py"
        index_html = "https://raw.githubusercontent.com/eaudunord/taisen-web-ui/main/index.html"
        check_scripts = [link_script, web_server, index_html]
        for script in check_scripts:
            url = script
            try:
                r=requests.get(url, stream = True)
                r.raise_for_status()
                for line in r.iter_lines():
                    if b'_version' in line: 
                        upstream_version = str(line.decode().split('version=')[1]).strip()
                        break
                local_script = script.split("/")[-1]
                if os.path.isfile(local_script) == False:
                    local_version = None
                else:
                    with open(local_script,'rb') as f:
                        for line in f:
                            if b'_version' in line:
                                local_version = str(line.decode().split('version=')[1]).strip()
                                break
                if upstream_version == local_version:
                    process_output.append('%s Up To Date' % local_script)
                else:
                    r = requests.get(url)
                    r.raise_for_status()
                    with open(local_script,'wb') as f:
                        f.write(r.content)
                    process_output.append('%s Updated' % local_script)
                    if local_script == "webserver.py":
                        os.system("sudo chmod +x webserver.py")
                        restart_flag = True

            except requests.exceptions.HTTPError:
                process_output.append("Couldn't check updates for: %s" % local_script)
                continue

            except requests.exceptions.SSLError:
                process_output.append("SSL error while checking for updates. System time may need to be synced")
                continue
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        result = {"success": True, "message": "Checked for updates"}
        self.wfile.write(json.dumps(result).encode())
        if restart_flag:
            subprocess.check_output(["sudo", "systemctl", "restart", "dreampi-linkcable"])


if __name__ == "__main__":
    try:
        httpd = socketserver.TCPServer(("", PORT), LinkCableHandler)
        print("DreamPi Link Cable Web Server Starting...")
        print("Access from any device: http://your-dreampi-ip:{}".format(PORT))
        print("Local access: http://localhost:{}".format(PORT))
        print("Press Ctrl+C to stop")
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped")
        if current_process:
            current_process.terminate()
    finally:
        httpd.server_close()