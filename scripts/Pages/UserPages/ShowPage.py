import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid,GridOptionsBuilder
from .Heatmap_showpage import Heatmap

class ShowPage():
    def __init__(self):
        self.selected_file = None
        self.df = None

    def run(self):
        self.show_show_page()
        
    def show_show_page(self):
        st.title("报告界面")
        files_path = self._get_files_path()
        file_list = self._get_feature_files(files_path)
        
        with st.sidebar:
            # 文件选择框
            self.selected_file = st.selectbox(
                "选择Feature文件",
                options=file_list,
                index=0,
                format_func=lambda x: os.path.basename(x)
            )
            if st.button("重新选择", key="btn_reselect_show"):
                st.session_state['user_select_file'] = None
                st.rerun()

            if st.button("Feature map", key="btn_Feature_map_show"):
                st.session_state['current_page'] = 'heatmap'
                st.rerun()
            
            self.selected_toppic = st.selectbox(
                "选择TOPPIC文件",
                options=file_list,
                index=0,
                format_func=lambda x: os.path.basename(x)
            )
            #todo
            # if st.link_button("查看toppic报告"):
            #     #todo
            #     st.rerun()

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
        # 文件下载按钮
        csv_data = self.df.to_csv(index=False, sep='\t').encode('utf-8')
        st.download_button(
            label="📥 下载选中文件",
            data=csv_data,
            file_name=os.path.basename(self.selected_file),
            mime='text/csv',
            key='btn_download_feature'
        )
            # 配置列显示规则
        default_columns = ['Mass', 'Apex_time', 'Intensity']  # 示例列名
        grid_builder = GridOptionsBuilder.from_dataframe(self.df)
        for col in self.df.columns:
            # 默认列保持可见，其他列隐藏
            grid_builder.configure_column(
                field=col,
                hide=col not in default_columns  # 关键配置
            )
        grid_builder.configure_side_bar(filters_panel=True, columns_panel=False)
        grid_options = grid_builder.build()
        
        AgGrid(
            self.df,
            height=500,
            gridOptions=grid_options,
            key="grid_show_page",
            theme='streamlit',
            custom_css={
                ".ag-header-cell-label": {"justify-content": "center"},
                ".ag-cell": {"display": "flex", "align-items": "center"}
            }
        )
        st.markdown(
            '''其他的数据被隐藏起来了,点击`columns`侧边栏即可找到
            后续进一步开发作图组件
            '''
        )
if __name__ == "__main__":
    ShowPage().run()

