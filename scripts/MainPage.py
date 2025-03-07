import streamlit as st
from Pages import AdminPage, UserPage
from Args import Args
from DBUtils.DBUtils import DBUtils
import hashlib

class LoginPage():
    def __init__(self, args):
        self.args = args  # 接收从MainPage传递的args对象
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
                if username and password:
                    # st.session_state['authentication_status'] = True
                    # st.session_state['authentication_username'] = username
                    # st.session_state['authentication_role'] = "admin"
                    db_utils = DBUtils(self.args)
                    user = db_utils.user_login(username, password)
                    if not user.empty:
                        # 使用列名获取密码
                        stored_password = user.iloc[0]['password']
                        # 使用列名获取角色
                        hashed_password = hashlib.sha256(password.encode()).hexdigest()
                        if hashed_password == stored_password:
                            st.title("登录成功")
                            st.session_state['authentication_status'] = True
                            st.session_state['authentication_username'] = username
                            st.session_state['authentication_role'] = user.iloc[0]['role']
                            st.rerun()  # 使用 st.experimental_rerun() 重定向到相应的页面
                        else:
                            st.write("用户名或密码错误")
                    else:
                        st.write("该用户不存在")
        else:
            st.rerun()  # 如果已经登录，重定向到相应的页面

class MainPage():
    def __init__(self):
        self.args = Args()

    def run(self):
        self.init_session_state()
        self.show_main_page()     

    def show_main_page(self):
        if not st.session_state['authentication_status']:
            '''# Welcome TDvis !🎉
            '''
            '''_化学实验中心数据可视化网站_'''

            if st.button("登录"):
                login_page = LoginPage(self.args)  
                login_page.run()
        else:
            if st.session_state['authentication_role']=="admin":
                admin_page = AdminPage(self.args)  
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
