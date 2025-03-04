import streamlit as st
from Pages import AdminPage, UserPage
import sqlite3 
import hashlib


class LoginPage():
    def __init__(self):
        pass

    def run(self):
        self.show_login_page()
    
    @st.dialog("login")
    def show_login_page(self):
        if not st.session_state['authentication_status']:
            st.title("登录")
            st.write("请登录")
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            if st.button("login"):
                # todo: 使用数据库验证用户名和密码
                conn = sqlite3.connect('/D:/desktop/ZJU_CHEM/TDVis/scripts/Pages/AdminPages/userinfo.db')
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                if user:
                    stored_password = user[1]  # Assuming the password is the second column in the users table
                    st.session_state['authentication_role']= user[2]
                    hashed_password = hashlib.sha256(password.encode()).hexdigest()
                    if hashed_password == stored_password:
                        st.title("登录成功")
                        st.session_state['authentication_status'] = True
                        st.session_state['authentication_username'] = username
                        st.rerun()
                    else:
                        st.write("用户名或密码错误")
                else:
                    st.write("用户名不存在")

class MainPage():
    def __init__(self):
        pass

    def run(self):
        self.init_session_state()
        self.show_main_page()

    def show_main_page(self):
        if not st.session_state['authentication_status']:
            st.title("可视化网站")
            if st.button("登录"):
                login_page = LoginPage()
                login_page.run()
        else:
            if st.session_state['authentication_role']=="管理员":
                admin_page = AdminPage()
                admin_page.run()
            else:
                user_page = UserPage()
                user_page.run()
    
    def init_session_state(self):
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = False
        
        if 'authentication_username' not in st.session_state:
            st.session_state['authentication_username'] = ""
        if 'authentication_role' not in st.session_state:
            st.session_state['authentication_role'] = ""


if __name__ == "__main__":
    main_page = MainPage()
    main_page.run()

    # 加载用户数据

