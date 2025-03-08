import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid
from .Heatmap_showpage import Heatmap

class ShowPage():
    def __init__(self):
        self.selected_file = None
        self.df = None

    def run(self):
        self.show_show_page()
        
    def show_show_page(self):
        st.title("报告界面")
        
        # 构建文件路径（与Heatmap一致）
        files_path = self._get_files_path()
        file_list = self._get_feature_files(files_path)
        
        with st.sidebar:
            # 文件选择框
            self.selected_file = st.selectbox(
                "选择数据文件",
                options=file_list,
                index=0,
                format_func=lambda x: os.path.basename(x)
            )
            
            # 操作按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("重新选择", key="btn_reselect_show"):
                    st.session_state['user_select_file'] = None
                    st.rerun()
            with col2:
                if st.button("Heatmap分析", key="btn_heatmap_show"):
                    st.session_state['current_page'] = 'heatmap'
                    st.rerun()

        # 显示数据表格
        if self.selected_file:
            try:
                self.df = pd.read_csv(self.selected_file, sep='\t')
                self._display_data_grid()
            except Exception as e:
                st.error(f"文件读取失败: {str(e)}")

    def _get_files_path(self):
        if 'user_select_file' not in st.session_state or not st.session_state['user_select_file']:
            return None
            
        path = st.session_state['user_select_file'][0]
        username = st.session_state['authentication_username']
        return os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'files', username, path
        )
        
        

    def _get_feature_files(self, files_path):
        """获取用户目录下所有特征文件"""
        if not os.path.exists(files_path):
            return []
            
        return [
            os.path.join(files_path, f) 
            for f in os.listdir(files_path) 
            if f.endswith('.feature')
        ]

    def _display_data_grid(self):
        """配置AgGrid列显示"""
        st.markdown(f"### 当前文件: `{os.path.basename(self.selected_file)}`")
        
        # 配置列显示规则
        column_defs = [
            {
                "headerName": col,
                "field": col,
                "hide": col not in ["Mass", "Intensity", "Apex_time"]
            } 
            for col in self.df.columns
        ]

        AgGrid(
            self.df,
            height=600,
            column_defs=column_defs,  # 添加列配置
            fit_columns_on_grid_load=True,
            theme='streamlit',
            custom_css={
                ".ag-header-cell-label": {"justify-content": "center"},
                ".ag-cell": {"display": "flex", "align-items": "center"}
            }
        )

if __name__ == "__main__":
    ShowPage().run()

