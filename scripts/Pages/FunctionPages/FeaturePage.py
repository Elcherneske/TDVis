import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import uuid  # <-- Add this import
from .ServerUtils import ServerControl
from .FileUtils import FileUtils
import os

class Featuremap():
    def __init__(self):
        #作图初始化
        self.df = None
        self.time_range = None      # 积分时间范围
        self.mass_range = None    # 积分质量范围 
        self.log_scale = 'None'      # 强度显示方式

        #数据读取列名初始化
        self.column_map = {
        'feature': ['Feature_ID', 'Feature ID'],
        'mass': ['Mass', 'Monoisotopic_mass', 'Precursor_mz'],
        'start_time':['Start_time', 'Min_time'],
        'end_time':['End_time', 'Max_time'],
        'time': ['Apex_time', 'Retention_time', 'RT'],
        'intensity': ['Intensity', 'Height', 'Area']
        }
        self.feature_col=None
        self.mass_col = None  # 实际质量列名
        self.start_time_col = None  # 实际起始时间列名
        self.end_time_col = None    # 实际结束时间列名
        self.time_col = None  # 实际时间列名
        self.intensity_col = None  # 实际强度列名

        #PTMs匹配参数初始化
        self.selected_mass = None  # 存储用户选择的质量
        self.neighbor_range = 20  # 默认邻近峰质量范围
        self.neighbour_limit = 0  # 默认邻近峰强度阈值
        self.ptms = [{"mass_diff": 15.994915, "name": "氧化"},
                    {"mass_diff": 42.010565, "name": "乙酰化"}]  # 存储用户输入的PTMs
        self.ppm_threshold = 5.00

    def run(self):
        self.show_page()

    def show_page(self):  
        st.header("**MS1 Featuremap**")
        if not self._validate_selection():
            return st.error("请选取一个文件进行分析！")

        if self._load_data():
            st.caption(" :material/star: **FeatureMap:** 展示特征的时间和质量分布! 请在图中进行框选以进行下一步!")
            with st.container(border=True):
                self._featuremap_widgets()
                self._plot_heatmap()
            st.caption(" :material/star: **2.Integratation:** 对Featuremap进行积分，得到指定范围的质谱图,请在图中框选以进行下一步!")
            with st.container(border=True):
                if self.time_range and self.mass_range:
                    self._integrate_widget()
                    integrated_data = self._process_integration()
                    self.selected_mass = self._plot_spectrum(integrated_data)
            st.caption(" :material/star: **3.PTMs:** 对选定范围内最强的峰进行PTMs匹配!")
            with st.container(border=True):
                if self.selected_mass:
                    self._near_peak_widget(integrated_data)
                    self._PTMs_DIY()
                    neighbor = self._near_peak_process(self.selected_mass, integrated_data)
                    self._near_peak_show(self.selected_mass,neighbor)
                    self._request_feature_widget()


#-------------------绘图组件---------------------

    def _plot_heatmap(self):
        """Visualize features as time-range bars with transparency"""
        fig = go.Figure()
        
        #进行数据的过滤,选取最强的点
        sorted_df = self.df.sort_values(by=self.intensity_col, ascending=False)
        if len(sorted_df) > self.data_limit:
            sorted_df = sorted_df.head(self.data_limit)
            
        # Add trace for each feature
        fig.add_trace(go.Bar(
        y=sorted_df[self.mass_col],
        x=sorted_df[self.end_time_col] - sorted_df[self.start_time_col],  # Changed here
        base=sorted_df[self.start_time_col],  # Changed here
        orientation='h',
        marker=dict(
            color=self._apply_scale(sorted_df[self.intensity_col]),
            colorscale=self.color_scale if self.use_custom else 'Bluered',
            opacity=0.3,
            line=dict(width=0)
        ),
        hoverinfo='text',  
        width=1.6
        ))

        # Axis formatting
        fig.update_layout(
            xaxis_title="Retention Time Range",
            yaxis_title="Mass (Da)",
            bargap=0.1,
            title="Feature Heatmap",
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.2)',
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.2)'
            ),
            hovermode='closest',
        )
        fig.update_layout(
        dragmode='select',  
        )
        # 最新版Streamlit事件处理
        event_data = st.plotly_chart(fig, 
            key="feature_heatmap",
            on_select="rerun",
            use_container_width=True,
            theme="streamlit",)

        # 处理选择事件
        if event_data.selection:
            try:
                # 直接获取第一个有效框选范围并添加5%边界缓冲
                box = next(b for b in event_data.selection.get('box', []) if b.get('xref') == 'x' and b.get('yref') == 'y')
                
                # 时间范围处理（x轴）
                time_min, time_max = sorted([box['x'][0], box['x'][1]])
                buffer = (time_max - time_min) * 0.05  # 5%边界缓冲
                self.time_range = (time_min - buffer, 
                                time_max + buffer)
                
                # 质量范围处理（y轴）
                mass_min, mass_max = sorted([box['y'][0], box['y'][1]])
                buffer = (mass_max - mass_min) * 0.05  # 5%边界缓冲
                self.mass_range = (mass_min - buffer,
                                mass_max + buffer)
                
            except (StopIteration, KeyError, TypeError):
                pass  # 保持当前范围不重置
            except ValueError as e:
                st.error(f"范围值错误: {str(e)}")

    def _plot_spectrum(self, data):
        if data is None:
            return
        # 归一化处理
        max_intensity = data[self.intensity_col].max()
        if max_intensity == 0:
            st.warning("所有强度值为零，无法进行归一化")
            return
        
        data['Normalized Intensity'] = (data[self.intensity_col] / max_intensity) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data[self.mass_col],
            y=data['Normalized Intensity'],
            marker=dict(
                color=data['Normalized Intensity'],
                colorscale='Bluered',
                colorbar=dict(title='强度(%)')
            ),
            hoverinfo='text',
        ))
        fig.update_layout(
            xaxis_title="质量 (Da)",
            yaxis_title="强度(%)",
            title='积分图',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.2)',
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.2)'
            )
        )

        event_data = st.plotly_chart(fig, use_container_width=True, key="spectrum",on_select="rerun",theme="streamlit")
        
        # 处理选择事件
        if event_data.selection:
            try:
                box = next(b for b in event_data.selection.get('box', []) if b.get('xref') == 'x')
                mass_min, mass_max = sorted([box['x'][0], box['x'][1]])
                
                # 在范围内找强度最高峰
                mask = data[self.mass_col].between(mass_min, mass_max)
                selected_data = data[mask]
                if not selected_data.empty:
                    self.selected_mass = selected_data.loc[selected_data['Normalized Intensity'].idxmax(), self.mass_col]
                else:
                    st.warning("选择范围内无有效数据")
                    return None
                return self.selected_mass  
            
            except (StopIteration, KeyError):
                return None
        
        # self._near_peak_widget(data)
        # if event_data.selection:
        #     self._near_peak_show(data, selected_mass)


    def _near_peak_show(self, selected_mass, neighbors):
        """
        根据widget所给出的参数,进行临近峰的展示
        Args:
            neighbors (DataFrame): 筛选后的邻近峰数据
            selected_mass (float): 当前选中的峰的质量
        """
        # 合并PTMS匹配逻辑到展示方法
        if not neighbors.empty and self.ptms:
            # 定义内部匹配函数
            def find_closest_ptms(row):
                mass_diff = abs(row['mass_diff'])
                if mass_diff == 0:
                    return ("", float('inf'))
                
                ppm_values = [
                    (ptm['name'], abs(abs(mass_diff) - abs(ptm['mass_diff'])) / self.selected_mass * 1e6)
                    for ptm in self.ptms
                ]
                best_match = min(ppm_values, key=lambda x: x[1]) if ppm_values else ("", float('inf'))
                # 新增阈值判断：仅当ppm低于阈值时显示修饰名称
                return (best_match[0], best_match[1]) if best_match[1] <= self.ppm_threshold else ("", best_match[1])

            # 执行匹配计算
            results = neighbors.apply(find_closest_ptms, axis=1)
            neighbors[['匹配修饰', 'ppm']] = pd.DataFrame(results.tolist(), index=neighbors.index)
            neighbors['ppm'] = neighbors['ppm'].round(2)

        # 显示处理后的数据
        if not neighbors.empty and self.mass_col and self.feature_col:
            display_columns = {
                self.mass_col: '质量 (Da)',
                'mass_diff': '质量差',
                '匹配修饰': 'PTMS修饰',
                'ppm': '匹配精度(ppm)',
                self.feature_col: 'Feature ID'
            }
            
            # 确保列存在并格式化ppm
            valid_columns = [col for col in display_columns.keys() if col in neighbors.columns]
            neighbors_diff = neighbors[valid_columns].rename(columns=display_columns)
            neighbors_diff['匹配精度(ppm)'] = neighbors_diff['匹配精度(ppm)'].round(2)
            
            st.write("**邻近峰信息**")
            st.dataframe(neighbors_diff)
            return neighbors_diff
        else:
            st.warning("在指定范围内未找到邻近峰")


#-------------------控制组件---------------------
    def _featuremap_widgets(self):
        """核心控制组件"""
        with st.expander("**基本设置**"):
            self.log_scale = st.selectbox(
                "强度处理方式",
                options=['log10','None', 'log2', 'ln','sqrt'],
                index=0
            )
            self.binx=st.number_input("x 轴像素",500)
            self.biny=st.number_input("y 轴像素",1000)
            self.data_limit = st.number_input(
                "显示数据点数量", 
                min_value=100, 
                max_value=9999, 
                value=1000,
                help="按照强度从高到低排序,显示最强的前n个点以清晰化其图像"
            )

        with st.expander("**高级配色设置**"):
            self.use_custom = st.checkbox("启用自定义配色",help="如果启用,则会覆盖默认的颜色配置")
            
            if self.use_custom:
                st.markdown("**颜色节点配置**")
                self.custom_colors = []
                
                # 初始化session_state
                if 'color_nodes' not in st.session_state:
                    st.session_state.color_nodes = 3  # 默认3个节点
                
                # 节点数量控制
                cols = st.columns([1,1,2])
                with cols[0]:
                    if st.button("➕ 添加节点") and st.session_state.color_nodes < 6:
                        st.session_state.color_nodes += 1
                with cols[1]:
                    if st.button("➖ 减少节点") and st.session_state.color_nodes > 2:
                        st.session_state.color_nodes -= 1
                # 动态生成颜色选择器
                for i in range(st.session_state.color_nodes):
                    col1, col2 = st.columns(2)
                    with col1:
                        color = st.color_picker(f"节点{i+1} 颜色", 
                                            value="#FF0000" if i==0 else "#0000FF" if i==1 else "#00FF00",
                                            key=f"color_{i}")
                    with col2:
                        position = st.number_input(f"节点{i+1} 位置", 
                                                min_value=0.0, 
                                                max_value=1.0,
                                                value=float(i)/(st.session_state.color_nodes-1) if st.session_state.color_nodes>1 else i,
                                                step=0.01,
                                                key=f"pos_{i}")
                    self.custom_colors.append([position, color])
                self.custom_colors.sort(key=lambda x: x[0])
                self.color_scale = [[pos, color] for pos, color in self.custom_colors]
            else:
                self.color_scale = [[0.00, "#FFFFFF"], [0.4, "#0000FF"], [0.5, "#FF0000"], [1.00, "#FF0000"]]
    
    def _integrate_widget(self):
        """手动设置积分范围--小组件"""
        with st.container():
            # 质量范围和时间范围设置容器
            with st.expander("**积分范围手动设置**"):
                manual=st.checkbox("手动设置积分范围", value=False, key='manual',help="如果您对于Featuremap的框选范围不满意,可以手动设置积分范围。框选后启用")
                if manual:
                    with st.container():
                        col1, col2 = st.columns(2)
                        # 质量范围设置列
                        with col1:
                            st.write("质量范围设置")
                            mass_min0 = float(self.df[self.mass_col].min())
                            mass_max0 = float(self.df[self.mass_col].max())
                            mass_max = st.number_input("积分质量上界", 
                                min_value=mass_min0, 
                                max_value=mass_max0, 
                                value=mass_max0,
                                key='mass_max')
                            mass_min = st.number_input("积分质量下界", 
                                min_value=mass_min0, 
                                max_value=mass_max0, 
                                value=mass_min0,
                                key='mass_min')
                            self.mass_range = (mass_min, mass_max)

                        # 时间范围设置列
                        with col2:
                            st.write("时间范围设置")
                            time_min0 = float(self.df[self.time_col].min())
                            time_max0 = float(self.df[self.time_col].max())
                            time_max = st.number_input("积分时间上界", 
                                                    min_value=time_min0, 
                                                    max_value=time_max0, 
                                                    value=time_max0,
                                                    key='time_max')
                            time_min = st.number_input("积分时间下界", 
                                                    min_value=time_min0, 
                                                    max_value=time_max0, 
                                                    value=time_min0,
                                                    key='time_min')

                            self.time_range = (time_min, time_max)

    def _request_feature_widget(self):
        """
        根据featureid来给出prsm的链接信息!
        """
        with st.expander("**Prsm查询**", expanded=True):
            featureid=st.number_input("输入您感兴趣的FeatureID", key='neighbor_range',help='会返回一个带有链接的表格,E-value越小,置信度越高')
            if st.button("查询"):
                prsmid=self._get_prsm_id(featureid)
                prsmid_sorted = prsmid.sort_values(by='E-value', ascending=True).reset_index(drop=True)
                
                # 配置列参数
                st.dataframe(
                    prsmid_sorted[['URL', 'E-value']],
                    column_config={
                        "URL": st.column_config.LinkColumn(
                            "prsm链接",
                            help="点击查看详细prsm信息",
                            validate="^http",
                            max_chars=100
                        ),
                        "E-value": st.column_config.NumberColumn(
                            format="%.2e",
                            disabled=True
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )

    def _near_peak_widget(self, data):
        """
        添加邻近峰筛选的控制功能
        """
        with st.expander(" **邻近峰筛选:** 以框选区域强度最高的峰作为基准", expanded=True):
            # 添加主峰和邻近峰标注
            col1, col2 = st.columns(2)
            with col1:
                self.neighbor_range = st.slider(
                    "质量范围 (±Da)",
                    min_value=0.1,
                    max_value=1000.0,
                    value=20.0,
                    step=0.1
                )
                self.neighbour_limit = st.number_input(
                    "强度阈值控制(%)",
                    min_value=0.00,
                    value=3.00,
                    max_value=100.00,
                    step=0.01,
                    help="是为修饰邻近峰的阈值,单位为%。如果该峰的强度低于该阈值,则不会被视为邻近峰。"
                )
            with col2:
                st.markdown("**help**:峰之间的距离可以体现其PTMs信息")
                st.markdown("常见的PTMs修饰有:")
                st.markdown("• **15**: 甲基化")


    def _PTMs_DIY(self):
        """自定义PTMs质量差匹配规则"""
        with st.expander("**自定义PTMs匹配库**"):
            # 在session_state中初始化PTMs存储
            if 'ptms_list' not in st.session_state:
                st.session_state.ptms_list = [{'uuid': str(uuid.uuid4()), **item} for item in self.ptms]
            col_add, col_del, _ = st.columns([1,1,3])
            with col_add:
                if st.button("➕ 添加PTMs规则", help="最多支持10条规则") and len(st.session_state.ptms_list) < 10:
                    st.session_state.ptms_list.append({"mass_diff": 0.0, "name": "", "uuid": str(uuid.uuid4())})
            with col_del:
                if st.button("➖ 删除选中项") and len(st.session_state.ptms_list) > 1:
                    # 通过checkbox选择要删除的项
                    selected_indices = [i for i, item in enumerate(st.session_state.ptms_list) if st.session_state.get(f'del_{item["uuid"]}')]
                    for i in reversed(selected_indices):
                        del st.session_state.ptms_list[i]
            
            updated_entries = []
            for item in st.session_state.ptms_list:
                with st.container(border=True):
                    cols = st.columns([2, 2, 1])
                    with cols[0]:
                        new_mass = st.number_input(
                            "质量差 (Da)",
                            min_value=-1000.0,
                            value=item["mass_diff"],
                            step=0.00001,  # 步长缩小到1e-5
                            format="%.5f",  # 显示5位有效数字
                            key=f"ptms_mass_{item['uuid']}"
                        )
                    with cols[1]:
                        new_name = st.text_input(
                            "修饰类型",
                            value=item["name"],
                            key=f"ptms_name_{item['uuid']}"
                        )
                    with cols[2]:
                        st.markdown(f'<small style="color:#666">ID:{item["uuid"][-6:]}</small>', unsafe_allow_html=True)
                        st.checkbox("删除", key=f"del_{item['uuid']}")
                updated_entries.append({"mass_diff": new_mass, "name": new_name, "uuid": item['uuid']})
            
            st.session_state.ptms_list = updated_entries
            self.ptms = [{"mass_diff": e["mass_diff"], "name": e["name"]} for e in st.session_state.ptms_list]

            ptm_text = st.text_area(
                '批量输入PTMs规则', 
                value='''示例:[
                    {"mass_diff": 15.9949, "name": "氧化"},
                    {"mass_diff": 42.0105, "name": "乙酰化"}
                ]    注意:这里的输入会对前面的规则进行覆盖!'''
            )
            if st.button("批量输入"):
                try:
                    if ptm_text.strip():
                        self.ptms = json.loads(ptm_text)
                        st.success("PTMS规则解析成功")
                except Exception as e:
                    st.error(f"解析失败: {str(e)}，请确保输入格式为合法JSON数组")
                    st.json('''正确格式示例：
                    [
                        {"mass_diff": 15.9949, "name": "氧化"},
                        {"mass_diff": 42.0105, "name": "乙酰化"}
                    ]''')

            self.ppm_threshold = st.number_input(
                "匹配精度阈值 (ppm)",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.01,
                help="若精度高于该阈值,则认为超出质谱精度容忍范围,无匹配的修饰"
            )

#----------------后端计算----------------

    def _apply_scale(self, series):
        """应用强度转换并归一化"""
        # 原始转换
        if self.log_scale == 'log2':
            scaled = np.log2(series + 1)
        elif self.log_scale == 'ln':
            scaled = np.log(series + 1)
        elif self.log_scale == 'sqrt':
            scaled = np.sqrt(series + 1)
        elif self.log_scale == 'log10':
            scaled = np.log10(series + 1)
        else:
            scaled = series.copy()

        # 归一化到0-1范围
        min_val = scaled.min()
        max_val = scaled.max()
        
        if max_val - min_val > 0:
            return (scaled - min_val) / (max_val - min_val)
        else:
            return scaled * 0  

    def _validate_selection(self):
        """验证文件选择状态"""
        if 'user_select_file' not in st.session_state or not st.session_state['user_select_file']:
            st.warning("⚠️ 请先选择数据文件夹")
            return False
        return True

    def _load_data(self):
        """数据加载与校验"""
        selected_path = st.session_state['user_select_file']
        sample_name = st.session_state['sample']
        try:
            # feature数据以及prsm数据的加载
            feature_path = FileUtils.get_file_path('_ms1.feature',selected_path=selected_path,sample_name=sample_name)
            prsm_path = FileUtils.get_file_path('_ms2_toppic_prsm_single.tsv',selected_path=selected_path,sample_name=sample_name)
            
            if not feature_path:
                st.error("❌ 未找到特征文件")
                return False
            self.df = pd.read_csv(feature_path, sep='\t')

            if not prsm_path:
                st.error("❌ 未找到PrSM数据文件")
                return False

            #实现对tsv文件的动态读取
            with open(prsm_path, 'r') as f:
                empty_line_idx = None
                for i, line in enumerate(f):
                    if not line.strip():  # 找到第一个空行
                        empty_line_idx = i
                        break

            try:
                # 根据空行位置设置读取参数
                self.df2 = pd.read_csv(
                    prsm_path,
                    sep='\t+',
                    skiprows=empty_line_idx + 1 if empty_line_idx is not None else 0,
                    header=0,  # 空行后的第一行为列名
                    on_bad_lines='warn',
                    dtype=str,
                    engine='python',
                    quoting=3
                ).dropna(how='all')
            except pd.errors.EmptyDataError:
                st.error(f"文件 {os.path.basename(prsm_path)} 内容为空")
            except Exception as e:
                st.error(f"加载 {os.path.basename(prsm_path)} 失败: {str(e)}")


            # 列名映射
            self.mass_col = self._find_column(self.column_map['mass'])
            if self.mass_col:
                self.df[self.mass_col] = self.df[self.mass_col].astype(float)
                self.feature_col = self._find_column(self.column_map['feature'])
                self.time_col = self._find_column(self.column_map['time'])
                self.intensity_col = self._find_column(self.column_map['intensity'])
                self.start_time_col = self._find_column(self.column_map['start_time'])
                self.end_time_col = self._find_column(self.column_map['end_time'])

                if not all([self.mass_col, self.time_col, self.intensity_col, self.start_time_col, self.end_time_col]):
                    missing = []
                    if not self.mass_col: missing.append(f"mass ({', '.join(self.column_map['mass'])})")
                    if not self.time_col: missing.append(f"time ({', '.join(self.column_map['time'])})")
                    if not self.intensity_col: missing.append(f"intensity ({', '.join(self.column_map['intensity'])})")
                    if not self.start_time_col: missing.append(f"start_time ({', '.join(self.column_map['start_time'])})")
                    if not self.end_time_col: missing.append(f"end_time ({', '.join(self.column_map['end_time'])})")
                    st.error(f"❌ 缺少必要列: {', '.join(missing)}")
                    return False
            return True
        except Exception as e:
            st.error(f"⛔ 数据加载失败: {str(e)}")
            return False

    def _near_peak_process(self, target_mass, data):
        """查找指定质量附近的邻近峰"""
        if data.empty or pd.isna(target_mass):
            return pd.DataFrame()
        # 获取邻近峰数据（±neighbor_range范围）
        mass_col = self.mass_col
        lower_bound = target_mass - self.neighbor_range
        upper_bound = target_mass + self.neighbor_range
        neighbors = data[
            (data[mass_col].between(lower_bound, upper_bound)) &
            (data["Normalized Intensity"] >= self.neighbour_limit) # 排除主峰
            ].copy()

        if neighbors.empty:
            return neighbors

        # 计算精确质量差（保留6位小数）
        neighbors["mass_diff"] = (neighbors[mass_col] - target_mass).round(6)
        
        # 按质量差差绝对值排序并截断结果
        return neighbors.sort_values("mass_diff")

    def _find_column(self, candidates):
        """在数据框中查找候选列名"""
        for col in candidates:
            if col in self.df.columns:
                return col
        return None

    def _get_prsm_id(self, ID):
        """根据featureID查询prsmID"""
        local_ip = ServerControl.get_local_ip()
        if self.df2.empty:
            return pd.DataFrame()

        matches = self.df2[self.df2['Feature ID'] == ID]
        if matches.empty:
            return pd.DataFrame()

        # 创建包含链接的DataFrame
        result_df = matches.copy()
        result_df['URL'] = result_df['Prsm ID'].apply(
            lambda x: f"http://{local_ip}:8000/topmsv/visual/proteins.html?folder=../../toppic_prsm_cutoff/data_js&prsm_id={x}"
        )
        return result_df
        
    # 计算所有PTMS规则的ppm值
    def find_closest_ptms(row):
        """
        pandas apply函数,是为一种操作规则
        """
        mass_diff = abs(row['mass_diff'])
        if mass_diff == 0:
            return ("", float('inf'))
        
        # 计算ppm：|Δm| / 目标质量 * 1e6
        ppm_values = [
            (ptm['name'], abs(abs(mass_diff) - abs(ptm['mass_diff'])) / target_mass * 1e6)
            for ptm in self.ptms
        ]
        # 找到ppm最小的修饰
        return min(ppm_values, key=lambda x: x[1]) if ppm_values else ("", float('inf'))

    def _process_integration(self):
        try:
            time_mask = self.df[self.time_col].between(*sorted(self.time_range))
            mass_mask = self.df[self.mass_col].between(*sorted(self.mass_range))
            integrated = self.df[time_mask & mass_mask].groupby(self.mass_col).agg({
                self.intensity_col: 'sum',
                self.feature_col: lambda x: list(x.unique())
            }).reset_index()
            if integrated.empty:
                st.warning("积分区间无有效数据，请调整范围设置")
                return None
            return integrated
            
        except Exception as e:
            st.error(f"数据处理失败: {str(e)}")
            return None

#------------------运行组件------------------
if __name__ == "__main__":
    heatmap = Featuremap()
    heatmap.run()


