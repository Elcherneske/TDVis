import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import os

class Heatmap():
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
        if st.session_state.get('current_page') == 'heatmap':
            self.show_page()

    def show_page(self):
        st.title("MS1 Featuremap")
        if not self._validate_selection():
            return
            
        if self._load_data():
            self._setup_controls()
            integrated_data = self._process_integration()
            self._plot_heatmap()
            self._plot_spectrum(integrated_data)
            st.write("对数操作也会同时反应到积分图中")

    def _setup_controls(self):
        """核心控制组件"""
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
            st.button("返回报告界面",key="return_showpage",on_click=lambda: st.session_state.update({
                    'current_page': None
                }))
                
            # 时间范围设置
            time_min = float(self.df[self.time_col].min())
            time_max = float(self.df[self.time_col].max())
            time_max=st.number_input("积分时间上界",time_min,time_max,time_max)
            time_min=st.number_input("积分时间下界",time_min,time_max,time_min)
            self.time_range =(time_min, time_max)

            # 质量范围设置
            mass_min = float(self.df[self.mass_col].min())
            mass_max = float(self.df[self.mass_col].max())
            mass_max=st.number_input("积分时间上界",mass_min,mass_max,mass_max)
            mass_min=st.number_input("积分时间下界",mass_min,mass_max,mass_min)
            self.mass_range =(mass_min, mass_max)
            
            self.log_scale = st.selectbox(
                "强度处理方式",
                options=['None', 'log2', 'ln','log10','sqrt'],
                index=0
            )
            self.binx=st.number_input("x 轴像素",500)
            self.biny=st.number_input("y 轴像素",500)
            
            self.color=st.selectbox(
                "配色",
                options=['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance', 'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg', 'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl', 'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric', 'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys', 'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet', 'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges', 'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl', 'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn', 'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu', 'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar', 'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn', 'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid', 'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd'],
                
                index=0
            )

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
        """热力图可视化"""
        fig = px.density_heatmap(
                self.df,
                x=self.time_col,
                y=self.mass_col,
                z=self._apply_scale(self.df[self.intensity_col]),
        nbinsx=self.binx,
        nbinsy=self.biny,
        color_continuous_scale=self.color,
        labels={
            self.time_col: '保留时间 (min)',
            self.mass_col: '质量 (Da)',
            'z': "强度"
        },
        title='质量-时间分布'
        )
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
        """应用强度转换"""
        if self.log_scale == 'log2':
            return np.log2(series + 1)
        if self.log_scale == 'ln':
            return np.log(series + 1)
        if self.log_scale == 'sqrt':
            return np.sqrt(series + 1)
        elif self.log_scale == 'log10':
            return np.log10(series + 1)
        return series

    # 保留原有数据加载和验证方法
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
            path = st.session_state['user_select_file'][0]
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

'''
self.df:读取的原始数据表
'''
