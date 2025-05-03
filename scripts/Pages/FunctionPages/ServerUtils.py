from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import os
import threading
import time
import socket

class ServerControl():
    _active_server = None  # 新增类变量跟踪活动服务器
    _active_monitor = None  # 新增监控线程跟踪

    @staticmethod
    def stop_active_server():
        """关闭当前活动的服务器"""
        if ServerControl._active_server:
            try:
                ServerControl._active_server.shutdown()
                ServerControl._active_server.server_close()
            except Exception as e:
                pass
            finally:
                ServerControl._active_server = None

    @staticmethod
    def start_report_server(report_path):
        """启动报告服务器并返回访问URL"""
        try:
            # 先关闭已有服务器
            ServerControl.stop_active_server()

            os.chdir(report_path)
            ServerControl._active_server = ThreadingHTTPServer(
                ('0.0.0.0', 8000),
                ServerControl.ZJUHTTPHandler
            )
            
            # 启动超时监控
            ServerControl._active_monitor = threading.Thread(
                target=ServerControl.server_monitor,
                args=(ServerControl._active_server,),
                daemon=True
            )
            ServerControl._active_monitor.start()
            
            threading.Thread(
                target=ServerControl._active_server.serve_forever,
                daemon=True
            ).start()
            
            return ServerControl.get_url()
        except Exception as e:
            raise Exception(f"服务器启动失败: {str(e)}")
    @staticmethod
    def get_local_ip():
        """动态获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            return "localhost"

    @staticmethod
    def get_url():
        """获取报告URL"""
        local_ip = ServerControl.get_local_ip()
        return f"http://{local_ip}:8000/topmsv/index.html"
    @staticmethod
    def server_monitor(server):
        """60分钟无操作自动关闭"""
        start_time = time.time()
        while time.time() - start_time < 3600:
            time.sleep(10)
        server.shutdown()

    class ZJUHTTPHandler(SimpleHTTPRequestHandler):
        """浙大内网访问控制器"""
        zju_networks = [
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('210.32.0.0/15'),
            ipaddress.ip_network('222.205.0.0/16'),
            ipaddress.ip_network('2001:da8::/32'),
            ipaddress.ip_network('2001:da8:8000::/48')
        ]
        
        def is_zju_client(self):
            try:
                client_ip = ipaddress.ip_address(self.client_address[0].split('%')[0])
                return any(client_ip in net for net in self.zju_networks)
            except:
                return False

        def do_GET(self):
            if not self.is_zju_client():
                self.send_error(403, "Forbidden", "仅限浙江大学内网访问")
                return
            super().do_GET()