import streamlit as st
import pandas as pd
<<<<<<< Updated upstream
import sqlite3
import hashlib
=======
from DBUtils import DBUtils
>>>>>>> Stashed changes


class AdminPage():
    def __init__(self):
        pass

    def run(self):
        self.show_admin_page()

    def show_admin_page(self):
        # 侧边栏退出按钮
        with st.sidebar:
            if st.button("退出"):
                st.session_state['authentication_status'] = None
                st.rerun()

        # 主页面标题
        st.title("管理员页面")

        # 用户列表
        # Connect to the database
        conn = sqlite3.connect('/D:/desktop/ZJU_CHEM/TDVis/scripts/Pages/AdminPages/userinfo.db')
        c = conn.cursor()

<<<<<<< Updated upstream
        # Fetch all users from the database
        c.execute("SELECT username, role FROM users")
        users = c.fetchall()

        #Create a DataFrame from the fetched data
        df = pd.DataFrame(users, columns=["username", "role"])
        df["is_selected"] = False

        config = {
            "username": st.column_config.TextColumn("用户名"),
            "password": st.column_config.TextColumn("密码"),
            "role": st.column_config.TextColumn("角色"),
            "is_selected": st.column_config.CheckboxColumn("是否删除")
        }

        edited_df = st.data_editor(df, column_config=config, key="user_data_editor")

        # Close the connection
        conn.close()

        # 更新和删除用户按钮
        if st.button("更新和删除用户"):
            # Connect to the database
            conn = sqlite3.connect('userinfo.db')
            c = conn.cursor()

            # Update or delete users based on the DataFrame content
            for index, row in edited_df.iterrows():
                if row["is_selected"]:
                    c.execute("DELETE FROM users WHERE username = ?", (row["username"],))
                else:
                    c.execute("UPDATE users SET username = ?, role = ? WHERE username = ?", 
                              (row["username"], row["role"], row["username"]))

            conn.commit()
            conn.close()
            st.success("用户更新和删除成功!")
            st.rerun

        # 添加用户表单
        add_form = st.form("add_form",clear_on_submit=True)
        username=add_form.text_input("用户名")
        password=add_form.text_input("密码",type="password")
        role=add_form.selectbox("角色", options=["管理员", "普通用户"])

        # 添加用户按钮
        if add_form.form_submit_button("添加用户"):
            st.write("添加用户")
            # Hash the password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Connect to the database
            conn = sqlite3.connect('userinfo.db')
            c = conn.cursor()

            # Create table if it doesn't exist
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')

            # Check if the username already exists
            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            if c.fetchone():
                st.error("用户名已存在!")
            else:
                # Insert the new user
                c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                          (username, hashed_password, role))
                st.success("用户添加成功!")
            st.rerun
            
            # Commit the changes and close the connection
            conn.commit()
            c.close()
            conn.close()
=======
            edited_df = st.data_editor(users, column_config=config, key="user_data_editor")
            # 更新和删除用户按钮
            if st.button("更新和删除用户"):
                #todo:这里需要判断更新还是删除，同时要判断哪些要更新，哪些要删除，在调用对应的接口
                
                
                db_utils.update_user(edited_df)
                st.rerun()
            
        with add_tab:
            # 添加用户表单
            add_form = st.form("add_form", clear_on_submit=True)
            username = add_form.text_input("用户名")
            password = add_form.text_input("密码", type="password")
            role = add_form.selectbox("角色", options=["admin", "user"])
            add_form = st.form("add_form", clear_on_submit=True)
            username = add_form.text_input("用户名")
            password = add_form.text_input("密码", type="password")
            role = add_form.selectbox("角色", options=["admin", "user"])

            # 添加用户按钮
            if add_form.form_submit_button("添加用户"):
                db_utils.user_register(username, password, role)
                st.rerun()
>>>>>>> Stashed changes
