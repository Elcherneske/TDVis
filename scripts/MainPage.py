import streamlit as st
from Pages import AdminPage, UserPage
from Args import Args
from DBUtils.DBUtils import DBUtils
from Pages.FunctionPages.ReportPage import ReportPage


class LoginPage():
    def __init__(self, args):
        self.args = args

    def run(self):
        self.show_login_page()
    @st.dialog("login")    
    def show_login_page(self):
        if not st.session_state['authentication_status']:
            st.title("登录")
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            if st.button("登录"):
                st.balloons()
                if username and password:
                    # 初始化登录方法
                    # st.session_state.update({
                    #         'authentication_status': True,
                    #         'authentication_username': username,
                    #         'authentication_role':"admin",
                    #     })
                    # st.rerun()
                    db_utils = DBUtils(self.args)
                    user = db_utils.user_login(username, password)
                    if not user.empty:
                        st.session_state.update({
                            'authentication_status': True,
                            'authentication_username': username,
                            'authentication_role': user.iloc[0]['role'],
                        })
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
                else:
                    st.error("该用户不存在")

class MainPage():
    def __init__(self):
        self.args = Args()
    def run(self):
        self.init_session_state()
        self.show_main_page()     

    def show_main_page(self):
        #进行页面导航
        if not st.session_state['authentication_status']:
            self._show_landing_page()
        else:
            #如果有选中的文件,那么就导航到报告展示的界面
            if st.session_state['user_select_file']:
                ReportPage().run()
            else:
                self._default_page()

    def _show_landing_page(self):
            st.markdown("# Welcome TDvis !🎉")
            st.markdown("**浙江大学化学系分析测试中心色谱与质谱分中心**")
            st.markdown("*Top-down质谱数据报告可视化网站*")
            if st.button("进入网站"):
                login_page = LoginPage(self.args)
                login_page.run()

    def _default_page(self):#进入用户界面或者管理员界面
        role = st.session_state['authentication_role']
        if role == 'admin':
            AdminPage(self.args).run()
        elif role == 'user':
            UserPage().run()

    def init_session_state(self):
        defaults = {
            'authentication_status': False,
            'authentication_username': "",
            'authentication_role': "",
            'user_select_file': "",
            "sample":"",
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

if __name__ == "__main__":
    main_page = MainPage()
    main_page.run()