import streamlit as st
from Pages import AdminPage, UserPage
from Args import Args
from DBUtils import DBUtils
import hashlib

class LoginPage():
    def __init__(self):
        pass

    def run(self):
        self.show_login_page()
    
    def show_login_page(self):
        if not st.session_state['authentication_status']:
            st.title("登录")
            st.write("请登录")
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            if st.button("login"):
                db_utils = DBUtils(self.args)
                user = db_utils.user_login(username, password)
                if user:
                    #todo: 这里需要判断用户角色
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
                    st.write("该用户不存在")
class MainPage():
    def __init__(self):
        pass

    def run(self):
        self.init_session_state()
        self.show_main_page()        
    def show_main_page(self):
        if not st.session_state['authentication_status']:
            '''# Welcome TDvis !🎉
            '''
            '''_化学实验中心数据可视化网站_'''

            if st.button("登录"):
                login_page = LoginPage()
                login_page.run()
        else:
            if st.session_state['authentication_role']=="admin":
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

