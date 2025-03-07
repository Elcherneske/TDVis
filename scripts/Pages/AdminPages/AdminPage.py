import streamlit as st
import pandas as pd
from DBUtils import DBUtils
import hashlib

class AdminPage():
    def __init__(self, args):
        self.args = args
        self.db_utils = DBUtils(args)  # 添加: 初始化DBUtils

    def run(self):
        self.show_admin_page()

    def show_admin_page(self):
        # 侧边栏退出按钮
        with st.sidebar:
            if st.button("退出"):
                st.session_state['authentication_status'] = None
                st.rerun()
        
        modify_tab, add_tab = st.tabs(["修改用户", "添加用户"])

        # 主页面标题
        st.title("管理员页面")
        users = self.db_utils.query_users(conditions="", limit=10, offset=0)
        # 删除密码列
        users = users.drop(columns=["password"])
        users["is_selected"] = False
        with modify_tab:

            config = {
                "username": st.column_config.TextColumn("用户名"),
                # "password": st.column_config.TextColumn("密码"),
                "role": st.column_config.SelectboxColumn("角色", options=["admin", "user"]),
                "is_selected": st.column_config.CheckboxColumn("是否删除")
            }
            
            edited_df = st.data_editor(users, column_config=config, key="user_data_editor")
            # 更新和删除用户按钮
            if st.button("更新和删除用户"):
                # 获取被标记为删除的行
                rows_to_delete = edited_df[edited_df["is_selected"]]
                for index, row in rows_to_delete.iterrows():
                    self.db_utils.delete_data("users", condition=f"username = '{row['username']}'")

                # 获取被更新的行
                updated_rows = edited_df[~edited_df["is_selected"]]
                original_rows = users[~users["is_selected"]]
                for index, row in updated_rows.iterrows():
                    original_row = original_rows.loc[index]
                    if row['username'] != original_row['username'] or row['role'] != original_row['role']:
                        self.db_utils.update_user(row['username'], row['role'])

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
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                self.db_utils.user_register(username, hashed_password, role)
                st.rerun()