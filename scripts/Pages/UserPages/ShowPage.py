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
        def _display_html_report(self, html_path):
            """嵌入HTML报告"""
            from streamlit.components.v1 import html
            
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # 设置自适应iframe容器
            st.markdown("""
            <style>
            .report-container {
                height: 80vh;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 渲染HTML内容
            with st.container():
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                html(html_content, height=800, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)


            
        def _get_toppic_report_path(self):
            """构造TOPPIC报告路径"""
            if not self.selected_toppic:
                return None
            base_name = os.path.basename(self.selected_toppic).replace('.feature', '')
            report_dir = os.path.join(
                os.path.dirname(self.selected_toppic),  
                f"{base_name}_report"                 
            )
            
            # 验证报告文件存在性
            index_path = os.path.join(report_dir, "index.html")
            return index_path if os.path.exists(index_path) else None        
                
            
        
if __name__ == "__main__":
    ShowPage().run()


