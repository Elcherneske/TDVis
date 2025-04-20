import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import os

class Featuremap():
    def __init__(self):
        self.df = None
        self.time_range = (0, 1)      # 积分时间范围
        self.mass_range = (0, 1)     # 积分质量范围
        self.log_scale = 'None'      # 强度显示方式
        self.column_map = {
        'mass': ['Mass', 'Monoisotopic_mass', 'Precursor_mz'],
        'time': ['Apex_time', 'Retention_time', 'RT'],
        'intensity': ['Intensity', 'Height', 'Area']
        }
        self.mass_col = None  # 实际质量列名
        self.time_col = None  # 实际时间列名
        self.intensity_col = None  # 实际强度列名
    def run(self):
        self.show_page()

    def show_page(self):
        st.title("MS1 Featuremap")
        if not self._validate_selection():
            return
            
        if self._load_data():
            self._setup_controls()
            self._plot_heatmap()
            # 质量范围和时间范围设置容器
            with st.expander("**积分范围设置**"):
                with st.container():
                    col1, col2 = st.columns(2)
                    
                    # 质量范围设置列
                    with col1:
                        st.write("质量范围设置")
                        mass_min0 = float(self.df[self.mass_col].min())
                        mass_max0 = float(self.df[self.mass_col].max())
                        # 使用双列布局包装上下界输入
                        mass_max = st.number_input("积分质量上界", 
                            min_value=mass_min0, 
                            max_value=mass_max0, 
                            value=mass_max0)
                        mass_min = st.number_input("积分质量下界", 
                            min_value=mass_min0, 
                            max_value=mass_max0, 
                            value=mass_min0)

                        self.mass_range = (mass_min, mass_max)

                    # 时间范围设置列
                    with col2:
                        st.write("时间范围设置")
                        time_min0 = float(self.df[self.time_col].min())
                        time_max0 = float(self.df[self.time_col].max())
                        # 使用双列布局包装上下界输入
                        time_max = st.number_input("积分时间上界", 
                                                min_value=time_min0, 
                                                max_value=time_max0, 
                                                value=time_max0)
                        time_min = st.number_input("积分时间下界", 
                                                min_value=time_min0, 
                                                max_value=time_max0, 
                                                value=time_min0)

                        self.time_range = (time_min, time_max)
                        
            integrated_data = self._process_integration()
                
            self._plot_spectrum(integrated_data)

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
                
                # 按位置排序颜色节点
                self.custom_colors.sort(key=lambda x: x[0])
                
                # 转换为Plotly接受的格式
                self.color_scale = [[pos, color] for pos, color in self.custom_colors]
            else:
                self.color =[[0.00,"#FFFFFF" ],[0.4,"#0000FF"],[0.7,"#FF0000"],[1.00,"#FF0000"]]

    def _process_integration(self):

        try:
            # 时间范围筛选
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

        """Improved scatter plot with better visibility"""
        # Create a copy for visualization
        plot_df = self.df.copy()
        plot_df['scaled_intensity'] = self._apply_scale(plot_df[self.intensity_col])
        
        fig = px.scatter(
            plot_df,
            x=self.time_col,
            y=self.mass_col,
            color='scaled_intensity',
            size='scaled_intensity',
            color_continuous_scale=self.color_scale if self.use_custom else self.color,
            labels={
                self.time_col: '保留时间 (min)',
                self.mass_col: '质量 (Da)',
                'color': "强度"
            },
            title='质量-时间分布',
            size_max=1 # Reduced maximum size
        )

        # Enhanced marker styling
        fig.update_traces(marker=dict(
            opacity=0.4,
            line=dict(
                width=0.1,
                color='rgba(30, 30, 30, 0.5)'  # Darker border for contrast
            ),
            sizemode='diameter',
            sizeref=2,  
            sizemin=6
        ))

        # Improved background and grid
        fig.update_layout(
            plot_bgcolor='rgba(240, 240, 240, 1)',  # Light gray background
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.9)',  # Bright grid lines
                griddash='dot'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.9)',
                griddash='dot'
            ),
            coloraxis_colorbar=dict(
                thickness=20,
                title_side='right'
            )
        )
        # Replace current sampling with intensity-based sampling
        if len(plot_df) > 5000:
            plot_df = plot_df.sample(n=5000, weights='scaled_intensity')  # Prefer high-intensity points
            st.warning("展示高亮度采样数据 (5000个点)")
        st.plotly_chart(fig, use_container_width=True)

    def _plot_spectrum(self, data):
        if data is None:
            return
        
        # 归一化处理
        max_intensity = data[self.intensity_col].max()
        if max_intensity == 0:
            st.warning("所有强度值为零，无法进行归一化")
            return
        
        data['Normalized Intensity'] = (data[self.intensity_col] / max_intensity) * 100
        fig = px.bar(
            data,
            x=self.mass_col,
            y=data['Normalized Intensity'], 
            labels={self.mass_col: '质量 (Da)', 'Normalized Intensity':"强度(%)"},  
            title='积分图',
            color=data['Normalized Intensity'],
            color_continuous_scale='Bluered'
        )
        st.plotly_chart(fig, use_container_width=True)

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
            # 构建文件路径
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
                
            # 读取数据
            file_path = os.path.join(files_path, feature_files[0])
            self.df = pd.read_csv(file_path, sep='\t')
            
            self.mass_col = self._find_column(self.column_map['mass'])
            self.time_col = self._find_column(self.column_map['time'])
            self.intensity_col = self._find_column(self.column_map['intensity'])
            
            # 校验结果
            if not all([self.mass_col, self.time_col, self.intensity_col]):
                missing = []
                if not self.mass_col: missing.append("mass")
                if not self.time_col: missing.append("time")
                if not self.intensity_col: missing.append("intensity")
                st.error(f"❌ 缺少必要列: {', '.join(missing)}，可接受列名: {self._format_acceptable_names(missing)}")
                return False
                
            return True
            
        except Exception as e:
            st.error(f"⛔ 数据加载失败: {str(e)}")
            return False
    def _find_column(self, candidates):
        """在数据框中查找候选列名"""
        for col in candidates:
            if col in self.df.columns:
                return col
        return None
    
if __name__ == "__main__":
    heatmap = Heatmap()
    heatmap.run()

