import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from streamlit_plotly_events import plotly_events
import os


class Featuremap():
    def __init__(self):
        self.df = None
        self.time_range = (300,1000)      # 积分时间范围
        self.mass_range = (300,1000)     # 积分质量范围 
        self.log_scale = 'None'      # 强度显示方式
        self.column_map = {
        'mass': ['Mass', 'Monoisotopic_mass', 'Precursor_mz'],
        'start_time':['Start_time', 'Min_time'],
        'end_time':['End_time', 'Max_time'],
        'time': ['Apex_time', 'Retention_time', 'RT'],
        'intensity': ['Intensity', 'Height', 'Area']
        }
        self.mass_col = None  # 实际质量列名
        self.start_time_col = None  # 实际起始时间列名
        self.end_time_col = None    # 实际结束时间列名
        self.time_col = None  # 实际时间列名
        self.intensity_col = None  # 实际强度列名

        self.neighbor_range = 20  # 默认邻近峰质量范围
        self.neighbour_limit = 0  # 默认邻近峰强度阈值
    def run(self):
        self.show_page()

    def show_page(self):
        st.header("**MS1 Featuremap**")
        if not self._validate_selection():
            return
            
        if self._load_data():
            self._setup_controls()
            self._plot_heatmap()
            
            # 质量范围和时间范围设置容器
            with st.expander("**积分范围手动设置**"):
                manual=st.checkbox("手动设置积分范围", value=False, key='manual')
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
            
            # 重新处理积分数据并绘图
            integrated_data = self._process_integration()
            self._plot_spectrum(integrated_data)
            st.write("**注**:当将一条谱线放大到较宽的时候,悬浮鼠标即可获得其信息")

    def _setup_controls(self):
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
                help="默认显示强度最高的1000个数据点"
            )

        with st.expander("**高级配色设置**"):
            self.use_custom = st.checkbox("启用自定义配色")
            
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

    def _process_integration(self):
        try:
            time_mask = self.df[self.time_col].between(*sorted(self.time_range))
            mass_mask = self.df[self.mass_col].between(*sorted(self.mass_range))
            integrated = self.df[time_mask & mass_mask].groupby(self.mass_col)[self.intensity_col].sum().reset_index()
            if integrated.empty:
                st.warning("积分区间无有效数据，请调整范围设置")
                return None
            return integrated
            
        except Exception as e:
            st.error(f"数据处理失败: {str(e)}")
            return None
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
        #TODO :将悬浮的信息显示添加回来!
            hovermode='closest',
        )
        fig.update_layout(
        dragmode='select',  
    )

        selected_range = plotly_events(fig, select_event=True)
        if selected_range:
            try:
                x_start = selected_range[0]["x"]
                x_end = selected_range[-1]["x"]
                self.time_range = (x_start-1, x_end+1)# 这里加一点余量

                y_values = [point["y"] for point in selected_range]
                y_min = min(y_values) - 1  # 质量范围增加余量
                y_max = max(y_values) + 1
                self.mass_range = (y_min, y_max)
            except (IndexError, KeyError):
                pass
        st.write(self.time_range,self.mass_range)
        st.rerun
        # st.plotly_chart(fig, use_container_width=True, key="feature_heatmap")
        

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

        clicked_point = plotly_events(fig, select_event=True)
        with st.expander("**邻近峰筛选**", expanded=True):
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
                    "阈值控制",
                    min_value=0.00,
                    value=3.00,
                    max_value=100.00,
                    step=0.01
                )
            with col2:
                st.write("框选最高点即可选中一个峰")
                st.markdown("**注**:峰之间的距离可以体现其PTMS信息")
                st.markdown("常见的PTMS修饰有:")
                st.markdown("• **15**: 甲基化")


        if clicked_point:
            #默认使用第一个峰!
            selected_mass = clicked_point[0]["x"]
            # 添加主峰标注
            fig.add_trace(go.Scatter(
                x=[selected_mass],
                y=[data[data[self.mass_col] == selected_mass]['Normalized Intensity'].values[0]],
                mode='markers',
                marker=dict(color='red', size=12),
                name='Selected Peak'
            ))
            
            # 查找并添加邻近峰
            neighbors = self._find_nearest_peaks(selected_mass, data)
            if not neighbors.empty:
                fig.add_trace(go.Scatter(
                    x=neighbors[self.mass_col],
                    y=neighbors['Normalized Intensity'],
                    mode='markers',
                    marker=dict(color='orange', size=10, symbol='x'),
                    name='Neighboring Peaks',
                    hoverinfo='text',
                    text=[f"质量: {m:.4f} Da<br>强度: {i:.1f}%" for m,i in zip(neighbors[self.mass_col], neighbors['Normalized Intensity'])]
                ))

            if not neighbors.empty:
                st.write("**邻近峰信息**")
                st.write(f"选中质量: {selected_mass:.4f} Da")
                st.write(neighbors[['Monoisotopic_mass', 'mass_diff']])
            else:
                st.warning("在指定范围内未找到邻近峰")



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
        try:
            path = st.session_state['user_select_file']
            username = st.session_state['authentication_username']
            files_path = os.path.join(
                os.path.dirname(__file__), '..', '..', '..', 
                'files', username, path
            )
            
            feature_files = [f for f in os.listdir(files_path) 
                            if f.endswith('ms1.feature')]
            if not feature_files:
                st.error("❌ 未找到特征文件")
                return False
                
            file_path = os.path.join(files_path, feature_files[0])
            self.df = pd.read_csv(file_path, sep='\t')
            
            self.mass_col = self._find_column(self.column_map['mass'])
            if self.mass_col:
                self.df[self.mass_col] = self.df[self.mass_col].astype(float)
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
    def _find_nearest_peaks(self, target_mass, data):
        """查找指定质量附近的邻近峰"""
        if data.empty or pd.isna(target_mass):
            return pd.DataFrame()

        # 获取邻近峰数据（±neighbor_range范围）
        mass_col = self.mass_col
        lower_bound = target_mass - self.neighbor_range
        upper_bound = target_mass + self.neighbor_range
        
        neighbors = data[
            (data[mass_col].between(lower_bound, upper_bound)) &
            (data["Normalized Intensity"] >= self.neighbour_limit) &
            (~np.isclose(data[mass_col], target_mass, atol=1e-4))  # 排除主峰
        ].copy()

        if neighbors.empty:
            return neighbors

        # 计算精确质量差（保留4位小数）
        neighbors["mass_diff"] = (neighbors[mass_col] - target_mass).round(4)
        
        # 按质量差差绝对值排序并截断结果
        return neighbors.sort_values("mass_diff")

    def _find_column(self, candidates):
        """在数据框中查找候选列名"""
        for col in candidates:
            if col in self.df.columns:
                return col
        return None
    
if __name__ == "__main__":
    heatmap = Featuremap()
    heatmap.run()

