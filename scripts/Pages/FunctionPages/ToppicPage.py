import streamlit as st

import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from .FileUtils import FileUtils  # 引入新的文件工具类
import subprocess
import threading
import socket

import time
import os

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote


class ToppicShowPage():
    def __init__(self):
        # 定义文件后缀映射
        self.file_suffixes = {
            "Proteoform (Single)": "_ms2_toppic_proteoform_single.tsv",
            "Proteoform": "_ms2_toppic_proteoform.tsv",
            "PrSM": "_ms2_toppic_prsm.tsv",
            "PrSM (Single)": "_ms2_toppic_prsm_single.tsv"
        }
        
        # 配置各文件类型默认显示的列
        self.default_columns = {
            "_ms2_toppic_proteoform_single.tsv": ['Prsm ID', 'Precursor mass', 'Retention time','Fixed PTMs'],
            "_ms2_toppic_proteoform.tsv": ['Proteoform ID', 'Protein name', 'Mass'],
            "_ms2_toppic_prsm.tsv": ['PrSM ID', 'E-value', 'Score'],
            "_ms2_toppic_prsm_single.tsv": ['Feature ID', 'Sequence', 'Modifications']
        }
    def run(self):
        self.show_toppic()

    def _get_toppic_files(self):
        """扫描用户目录获取所有TOPPIC文件"""
        base_path = FileUtils.get_select_path()  # 使用新的工具类方法
        if not base_path or not os.path.exists(base_path):
            return None
        
        # 获取目录下所有文件
        all_files = os.listdir(base_path)

        # 创建后缀->文件路径的映射
        file_map = {}
        for filename in all_files:
            for suffix in self.file_suffixes.values():
                if filename.endswith(suffix):
                    # 处理可能存在的重复后缀情况（取第一个匹配的）
                    if suffix not in file_map:
                        file_map[suffix] = os.path.join(base_path, filename)
                    break
        return file_map

    def show_toppic(self):
        # 侧边栏控制按钮
        with st.sidebar:
            st.button("退出", key="exit", 
                    on_click=lambda: st.session_state.update({
                        'authentication_status': None,
                        'current_page': None
                    }))
            st.button("重新选样", key="reselect", 
                    on_click=lambda: st.session_state.update({
                        'user_select_file': None,
                        'current_page': st.session_state['authentication_role']
                    }))
            st.button("返回报告界面", key="return_showpage",
                    on_click=lambda: st.session_state.update({'current_page': None}))
        file_map = self._get_toppic_files()
        
        st.header("TOPPIC展示界面")
        st.write("请在`columns`侧边栏中选择您需要查看的列")
        tabs = st.tabs([f"📊 {display_name}" for display_name in self.file_suffixes.keys()])
        
        report_path=FileUtils.get_html_report_path()
        
        for idx, (display_name, suffix) in enumerate(self.file_suffixes.items()):
             with tabs[idx]:
                if suffix in file_map:
                    self._display_tab_content(file_map[suffix], suffix)
                else:
                    st.warning(f"⚠️ 目录中未找到 {suffix} 类型的文件")
        if st.button("📑 打开Toppic报告"):
            def get_global_ipv6():
                """获取公网IPv6地址"""
                try:
                    # 获取所有IPv6地址
                    all_address = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6)
                    # 筛选全球单播地址（2000::/3）
                    global_ipv6 = [
                        addr[4][0] for addr in all_address
                        if not addr[4][0].startswith('fe80')  # 排除本地链路地址
                        and not addr[4][0].startswith('::')    # 排除环回地址
                        and addr[4][0].count(':') >= 2         # 标准格式判断
                    ]
                    return global_ipv6[0] if global_ipv6 else None
                except Exception as e:
                    st.error(f"获取IPv6地址失败: {str(e)}")
                    return None

            def get_local_ip():
                """动态获取本机IP地址"""
                try:
                    # 通过创建临时socket获取本机IP
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                    return ip
                except Exception as e:
                    st.error(f"获取本机IP失败: {str(e)}")
                    return "localhost"  # 失败时回退到本地地址

            # 在 Streamlit 按钮点击事件中启动
            st.write(report_path)
            threading.Thread(
                target=start_server,
                args=(report_path,),
                daemon=True
            ).start()

            # 生成访问链接
            st.markdown("🔗 **访问链接:**")
            st.markdown(f"🌐 **IPv6:** `http://[{get_global_ipv6()}]:8000/topmsv/index.html`")
            st.markdown(f"🌐 **IPv4:** `http://{get_local_ip()}:8000/topmsv/index.html`")
    def _display_tab_content(self, file_path, suffix):
        df = pd.read_csv(file_path,sep='\t',skiprows=37)
        filename = os.path.basename(file_path)
            
        try:
            row_count = df.shape[0]
            st.markdown(f"✈ **表格条目数：** `{row_count:,}` 条")
            # 文件下载功能
            self._create_download_button(df, filename)
            
            # 表格显示配置
            self._configure_aggrid(df, suffix, filename)
        except Exception as e:
            st.error(f"加载 {filename} 失败: {str(e)}")

    def _create_download_button(self, df, filename):
        """创建下载按钮组件"""
        csv_data = df.to_csv(index=False, sep='\t').encode('utf-8')
        st.download_button(
            label=f"📥 下载 {filename}",
            data=csv_data,
            file_name=filename,
            mime='text/tab-separated-values',
            key=f'download_{filename}'
        )

    def _configure_aggrid(self, df, suffix, filename):
        """配置AgGrid表格显示"""
        # 获取默认显示的列
        default_cols = self.default_columns[suffix]
        # 构建网格配置
        grid_builder = GridOptionsBuilder.from_dataframe(df,enableValue=True,enableRowGroup=True,enablePivot=True)
        for col in df.columns:
            grid_builder.configure_column(
                field=col,
                hide=col not in default_cols
            )
            
        grid_builder.configure_side_bar(
            filters_panel=True, 
            columns_panel=True
        )
        # 渲染表格
        AgGrid(
            df,
            gridOptions=grid_builder.build(),
            height=500,
            theme='streamlit',
            enable_enterprise_modules=True,
            custom_css={
                ".ag-header-cell-label": {"justify-content": "center"},
                ".ag-cell": {"display": "flex", "align-items": "center"}
            },
            key=f"grid_{filename}"
        )

def virus_scan(report_path):
    """在文件服务启动前进行安全扫描"""
    try:
        result = subprocess.run(
            ["clamscan", "-r", "--infected", report_path],
            capture_output=True,
            text=True
        )
        if "Infected files: 0" not in result.stdout:
            st.error("病毒扫描未通过，终止服务启动")
            os._exit(1)  # 强制终止进程
    except FileNotFoundError:
        st.warning("未安装ClamAV，跳过病毒扫描")

def log_monitor(report_path, token):
    """实现日志监控函数"""
    # 这里可以添加具体的日志监控逻辑
    pass

def start_server(report_path):
    """启动带访问控制的HTTP服务器"""
    try:
        virus_scan(report_path)
        os.chdir(report_path)

        # 创建IPv6 socket并允许双栈
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)  # 关键参数
        sock.bind(('::', 8000))
        server = ThreadingHTTPServer(
            ('0.0.0.0', 8000),  # 同时监听IPv4/IPv6
            CustomRequestHandler,
            bind_and_activate=False
        )

        server.socket = sock
        # 启动超时监控
        threading.Thread(target=server_monitor, args=(server,)).start()
        server.serve_forever()

    except Exception as e:
        st.error(f"服务器启动失败: {str(e)}")

def server_monitor(server):
    """60分钟无操作自动关闭"""
    start_time = time.time()
    while time.time() - start_time < 3600:
        time.sleep(10)
    server.shutdown()

class CustomRequestHandler(SimpleHTTPRequestHandler):
    secure_paths = {
        '/topmsv/visual/ms.html': '../../toppic_prsm_cutoff/data_js',
        '/topmsv/visual/proteins.html': '../../toppic_prsm_cutoff/data_js'
    }

    def do_GET(self):
        # 记录访问日志
        st.session_state.setdefault('access_log', []).append({
            'time': time.ctime(),
            'client': self.client_address[0],
            'path': self.path
        })
        
        # 路径安全检查
        if not self._path_check():
            return
            
        super().do_GET()

    def _path_check(self):
        parsed = urlparse(self.path)
        if parsed.path not in self.secure_paths:
            self.send_error(404, "File not found")
            return False
            
        allowed_folder = self.secure_paths[parsed.path]
        if f"folder={allowed_folder}" not in parsed.query:
            self.send_error(403, "Invalid folder parameter")
            return False
            
        return True