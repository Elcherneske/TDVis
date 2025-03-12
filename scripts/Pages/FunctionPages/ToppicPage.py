import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder
from .FileUtils import FileUtils  # 引入新的文件工具类
import subprocess
import threading
import socket

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
                    # 通过创建临时socket获取本机IP,不过因为还是不了解网络的结构,对与该问题尚且不了解
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                    return ip
                except Exception as e:
                    st.error(f"获取本机IP失败: {str(e)}")
                    return "localhost" 
                
            def start_server(report_path):
                """启动支持IPv6的HTTP服务器"""
                try:
                    subprocess.run([
                        "python", "-m", "http.server", 
                        "8000", "--directory", report_path,
                        "--bind", "::"  # 关键参数：启用IPv6
                    ], check=True)
                except subprocess.CalledProcessError as e:
                    st.error(f"服务器启动失败: {e.stderr.decode()}")
            # 获取IPv6地址
            ipv6_address = get_global_ipv6()
            
            if ipv6_address:
                server_url = f"http://[{ipv6_address}]:8000/topmsv/index.html"
                threading.Thread(
                    target=start_server,
                    args=(report_path,),
                    daemon=True
                ).start()
                st.markdown(f"[IPv6访问地址]({server_url})")
            else:
                # IPv6不可用时回退到IPv4
                local_ip = get_local_ip()
                server_url = f"http://{local_ip}:8000/topmsv/index.html"
                st.markdown(f"[IPv4访问地址]({server_url}) (备用)")
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

    def start_server(report_path):
        subprocess.run(
            ["python", "-m", "http.server", "8000", "--directory", report_path],
            check=True
        )
    
    def is_zju_internal_ip(ip):
        """检测是否为浙大内网IP"""
        zju_network_ranges = [
            '10.0.0.0/8',        # 浙大核心内网
            '172.16.0.0/12',     # 实验室私有网络
            '192.168.0.0/16',    # 各校区子网
            '210.32.0.0/16',     # 浙大公网IP段
            '222.205.0.0/16'     # 浙大IPv4公网段
        ]
        
        from ipaddress import ip_address, ip_network
        client_ip = ip_address(ip)
        return any(client_ip in ip_network(net) for net in zju_network_ranges)
