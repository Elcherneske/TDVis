import streamlit as st
import pandas as pd
from DBUtils import DBUtils
from Pages.FunctionPages.FileUtils import FileUtils  


class AdminPage():
    def __init__(self, args):
        self.args = args
        self.db_utils = DBUtils(args)  # 添加: 初始化DBUtils

    def run(self):
        self.show_admin_page()
    def show_admin_page(self):
        with st.sidebar:
            if st.button("退出"):
                st.session_state['authentication_status'] = None
                st.rerun()
        st.title("管理员页面")
        
        modify_tab, add_tab,files_tab = st.tabs(["修改用户", "添加用户","查看数据"])
        
        users = self.db_utils.query_users(conditions="", limit=10, offset=0)
        users = users.drop(columns=["password"])
        users["is_selected"] = False
        with modify_tab: #Todo: 尚且不完善

            config = {
                "username": st.column_config.TextColumn("用户名"),
                # "password": st.column_config.TextColumn("密码"),
                "role": st.column_config.SelectboxColumn("角色", options=["admin", "user"]),
                "is_selected": st.column_config.CheckboxColumn("是否删除")
            }
            
            edited_df = st.data_editor(users, column_config=config, key="user_data_editor")
            # 更新和删除用户按钮
            if st.button("更新和删除用户"):
                # 先进行删除操作
                rows_to_delete = edited_df[edited_df["is_selected"]]
                for _, row in rows_to_delete.iterrows():
                    self.db_utils.delete_data("users", f"username = '{row['username']}'")
                
                # 再处理更新
                updated_rows = edited_df[~edited_df["is_selected"]]
                original_rows = users[~users["is_selected"]]
                for (index, row), (_, original_row) in zip(updated_rows.iterrows(), original_rows.iterrows()):
                    updates = {}
                    if row['username'] != original_row['username']:
                        updates['username'] = row['username']
                    if row['role'] != original_row['role']:
                        updates['role'] = row['role']
                    
                    if updates:
                        self.db_utils.update_user(
                            old_username=original_row['username'],
                            new_username=updates.get('username'),
                            new_role=updates.get('role')
                        )

                # 重新查询用户数据并刷新表格
                users = self.db_utils.query_users(conditions="", limit=10, offset=0)
                users = users.drop(columns=["password"])
                users["is_selected"] = False
                st.rerun()
                
        with add_tab:
            # 添加用户表单
            add_form = st.form("add_form", clear_on_submit=True)
            username = add_form.text_input("用户名")
            password = add_form.text_input("密码", type="password")
            role = add_form.selectbox("角色", options=["admin", "user"])

            # 添加用户按钮
            if add_form.form_submit_button("添加用户"):
                # 修改: 将密码转换为哈希值
                self.db_utils.user_register(username, password, role)
                st.rerun()
                
        with files_tab:
            #管理员实验数据查看表单
            df = FileUtils.query_files()#不加入用户名,从而获得查询所有数据的权限
            if not df.empty:
                df["file_select"] = False  # 添加选择列
                df.index = df.index + 1
                config = {
                    "用户名": st.column_config.TextColumn("用户目录"),
                    "文件名": st.column_config.TextColumn("文件名"),
                    "file_select": st.column_config.CheckboxColumn("选择状态")
                }

                select_df = st.data_editor(
                    df,
                    column_config=config,
                    key="admin_data_editor",
                    width=800,
                    height=400
                )

            if st.button("选择文件"):
                user_name=select_df[select_df['file_select'] == True]['用户名'].tolist()
                user_name=str(user_name[0])
                file_name=select_df[select_df['file_select'] == True]['文件名'].tolist()
                
                st.session_state['user_select_file'] =file_name
                st.session_state['authentication_username'] = user_name
                st.session_state['current_page'] = "showpage"
                st.rerun()  


            