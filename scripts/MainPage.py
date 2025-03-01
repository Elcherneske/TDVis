import streamlit as st
from Pages import AdminPage, UserPage

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
            if st.button("login"):
                # todo: 使用数据库验证用户名和密码
                st.title("登录成功")
                st.session_state['authentication_status'] = True
                st.session_state['authentication_username'] = "user"
                st.rerun()
            

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
            if st.session_state['authentication_username'] == "admin":
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

if __name__ == "__main__":
    main_page = MainPage()
    main_page.run()

    # 加载用户数据

