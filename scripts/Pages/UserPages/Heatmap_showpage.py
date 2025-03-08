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

    def run(self):
        if st.session_state.get('current_page') == 'heatmap':
            self.show_page()

    def show_page(self):
        st.title("Featuremap数据可视化分析")
        if not self._validate_selection():
            return
            
        if self._load_data():
            self._setup_controls()
            self._plot_heatmap()
            integrated_data = self._process_integration()
            self._plot_spectrum(integrated_data)


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

            # 时间范围设置
            time_min = float(self.df['Apex_time'].min())
            time_max = float(self.df['Apex_time'].max())
            self.time_range = st.slider(
                "积分时间范围 (min)",
                min_value=time_min,
                max_value=time_max,
                value=(time_min, time_max)
            )

            # 质量范围设置
            mass_min = float(self.df['Mass'].min())
            mass_max = float(self.df['Mass'].max())
            self.mass_range = st.slider(
                "积分质量范围 (Da)",
                min_value=mass_min,
                max_value=mass_max,
                value=(mass_min, mass_max),
                format="%.4f"
            )
            self.log_scale = st.selectbox(
                "强度处理方式",
                options=['None', 'log2', 'ln','log10','sqrt'],
                index=0
            )
            self.binx=st.number_input("x 轴像素",500)
            self.biny=st.number_input("y 轴像素",500)

    def _process_integration(self):

        try:
            # 时间范围筛选
            time_mask = self.df['Apex_time'].between(*sorted(self.time_range))
            mass_mask = self.df['Mass'].between(*sorted(self.mass_range))
            
            integrated = self.df[time_mask & mass_mask].groupby('Mass')['Intensity'].sum().reset_index()
            
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
            self.df,  # 使用原始数据
            x='Apex_time',
            y='Mass',
            z=self._apply_scale(self.df['Intensity']),
            nbinsx=self.binx,
            nbinsy=self.biny,
            color_continuous_scale='Rainbow',
            labels={
                'Apex_time': '保留时间 (min)',
                'Mass': '质量 (Da)',
                'z': "强度"
            },
            title='质量-时间分布'
        )
        st.plotly_chart(fig, use_container_width=True)

    def _plot_spectrum(self, data):

        fig = px.bar(
            data,
            x='Mass',
            y=self._apply_scale(data['Intensity']),
            labels={'Mass': 'Mass', 'y': "强度"},
            title='积分质谱图',
            color=self._apply_scale(data['Intensity']),
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
                            if f.endswith('_ms1.feature')]
            if not feature_files:
                st.error("❌ 未找到特征文件")
                return False
                
            # 读取数据
            file_path = os.path.join(files_path, feature_files[0])
            self.df = pd.read_csv(file_path, sep='\t')
            
            # 校验数据列
            required_columns = {'Mass', 'Apex_time', 'Intensity'}
            if not required_columns.issubset(self.df.columns):
                missing = required_columns - set(self.df.columns)
                st.error(f"❌ 缺少必要列: {', '.join(missing)}")
                return False
                
            return True
            
        except Exception as e:
            st.error(f"⛔ 数据加载失败: {str(e)}")
            return False

if __name__ == "__main__":
    heatmap = Heatmap()
    heatmap.run()

'''
self.df:读取的原始数据表
'''
