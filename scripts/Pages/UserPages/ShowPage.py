import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid,GridOptionsBuilder
from .Heatmap_showpage import Heatmap
from .toppic_showpage import ToppicShowPage

class ShowPage():
    def __init__(self):
        self.selected_file = None
        self.df = None

    def run(self):
        self.show_show_page()
        

    def show_show_page(self):
        st.title("报告界面")
        files_path = self._get_select_path()
        file_list = self._get_feature_files(files_path)
        
        with st.sidebar:
            # 文件选择框  
            if st.button("重新选择", key="btn_reselect_show"):
                st.session_state['user_select_file'] = None
                st.rerun()

            self.selected_file = st.selectbox(
                "选择Feature文件",
                options=file_list,
                index=0,
                format_func=lambda x: os.path.basename(x)
            )
            if st.button("Feature map", key="btn_Feature_map_show"):
                st.session_state['current_page'] = 'heatmap'
                st.rerun()
                
            if st.button("查看TOPPIC结果",key="btn_TOPPIC_show"):
                st.session_state['current_page'] = 'toppic'
                st.rerun()

        self._count_report_files()

        # 显示数据表格
        if self.selected_file:
            try:
                self.df = pd.read_csv(self.selected_file, sep='\t')
                self._display_data_grid()
            except Exception as e:
                st.error(f"文件读取失败: {str(e)}")

    def _get_select_path(self):
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
        st.markdown(f"**当前文件:**  `{os.path.basename(self.selected_file)}`")
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
        default_columns = ['Mass','Monoisotopic_mass', 'Apex_time', 'Intensity']  # 示例列名
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
            ''')
        
    def _count_report_files(self):
        """统计HTML报告相关文件数量"""
        html_path=self._get_html_report_path()
        try:
            base_path = os.path.join(
                html_path,
                "toppic_proteoform_cutoff",
                "data_js"
            )
            
            # 定义需要统计的文件夹
            target_folders = [
                ("proteins", "蛋白"),
                ("proteoforms", "变体"), 
                ("prsms", "特征")
            ]
            results = []
            for folder, display_name in target_folders:
                folder_path = os.path.join(base_path, folder)
                if os.path.exists(folder_path):
                    file_count = len([
                        f for f in os.listdir(folder_path) 
                        if os.path.isfile(os.path.join(folder_path, f))
                    ])
                    results.append(f" **{display_name}**: {file_count} 个")
                else:
                    results.append(f"⚠️ {display_name}目录不存在")
            st.markdown("__本样品共检测到:__")
            st.markdown("\n".join(results))
                
                
        except Exception as e:
            st.sidebar.error(f"文件统计失败: {str(e)}")
    def _get_html_report_path(self):
        """获取HTML报告路径"""
        base_path = self._get_select_path()
        if not base_path or not os.path.exists(base_path):
            return None
        # 获取目录下所有文件
        all_files = os.listdir(base_path)
        for filename in all_files:
            if filename.endswith("_html"):
                break

        
        base_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', '..',
            'files', 
            st.session_state['authentication_username'],
            st.session_state['user_select_file'][0],
            filename  # 添加_html后缀
        )
        return base_dir
        
if __name__ == "__main__":
    ShowPage().run()
