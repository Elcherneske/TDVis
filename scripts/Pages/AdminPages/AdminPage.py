import streamlit as st
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
        
        modify_tab, add_tab, files_tab, file_manage_tab = st.tabs(
            ["修改用户", "添加用户", "查看数据", "文件管理"]
        )
        
        users = self.db_utils.query_users(conditions="", limit=10, offset=0)
        users = users.drop(columns=["password","file_addresses"])
        users["is_selected"] = False
        with modify_tab:
            config = {
                "username": st.column_config.TextColumn("用户名"),
                "role": st.column_config.SelectboxColumn("角色", options=["user","admin"]),
                "is_selected": st.column_config.CheckboxColumn("是否删除")
            }
            
            edited_df = st.data_editor(users, column_config=config, key="user_data_editor")
            if st.button("更新和删除用户"):
                try:
                    # 删除操作
                    deleted_users = edited_df[edited_df["is_selected"]]['username'].tolist()
                    if deleted_users:
                        if not self.db_utils.delete_users(deleted_users):
                            raise ValueError("删除用户失败")
                    
                    # 更新操作
                    updated_rows = edited_df[~edited_df["is_selected"]]
                    
                    for idx in updated_rows.index:
                        row = updated_rows.loc[idx]
                        original_username = users.loc[idx, 'username']
                        original_role=users.loc[idx,'role']
                        
                        if not self.db_utils.update_user(original_username, row['username'],original_role, row['role']):
                            raise ValueError(f"更新用户 {original_username} 失败")
                    
                    st.success("用户信息已更新")
                except Exception as e:
                    st.error(f"操作失败: {str(e)}")

        with add_tab:
            add_form = st.form("add_user_form")
            username = add_form.text_input("用户名")
            password = add_form.text_input("密码", type="password")
            role = add_form.selectbox("角色", ["user", "admin"])
            # 添加用户按钮
            if add_form.form_submit_button("添加用户"):
                self.db_utils.user_register(username, password, role)
                st.rerun()
                
        with files_tab:
            #管理员实验数据查看表单
            df = FileUtils.query_files()#不加入用户名,从而获得查询所有数据的权限
            if not df.empty:
                df = df.drop_duplicates(subset=['文件名'])
                df.index = df.index + 1
                
                selected_file = st.radio(
                    "**📃请选择您要查看报告的文件:**",
                    df['文件名'],
                    index=None,
                    key="file_radio"
                )
                
                if st.button("选择文件"):
                    if selected_file:
                        st.session_state['user_select_file'] = selected_file
                        st.rerun()
                    else:
                        st.error("请先选择一个文件!")  
        with file_manage_tab:
            st.header("用户文件管理")
            
            # User selection
            user_list = self.db_utils.query_users("", 100, 0)['username'].tolist()
            selected_user = st.selectbox("选择用户", user_list)
            
            # Display current file addresses
            current_files = self.db_utils.get_file_addresses(selected_user)
            # 去除重复文件地址
            current_files = list(set(current_files))
            st.write("当前文件地址列表:")
            st.json(current_files)
            
            # File addition interface
            with st.form("add_file_form"):
                temp_file_path = st.text_input("文件路径", key="new_file_input")  # 改用中间变量
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.form_submit_button("添加单个文件"):
                        if temp_file_path:
                            if temp_file_path in current_files:
                                st.error("文件已存在，请勿重复添加")
                            else:
                                success = self.db_utils.add_file_address(selected_user, temp_file_path)
                                if success:
                                    st.session_state.new_file_input = ""  # 清空中间变量
                                    st.success(f"成功添加文件: {temp_file_path}")
                                    st.rerun()
                                else:
                                    st.error("添加文件失败")
                with col2:
                    if st.form_submit_button("批量添加文件",help="暂时只留了接口"):
                        # Implement batch file addition logic
                        pass
            
            # File removal interface
            if current_files:
                selected_files = st.multiselect("选择要删除的文件", current_files)
                if st.button("删除选中文件"):
                    # Implement file removal logic
                    updated_files = [f for f in current_files if f not in selected_files]
                    success = self.db_utils.update_file_addresses(selected_user, updated_files)
                    if success:
                        st.success("文件删除成功")
                        st.rerun()


            