import streamlit as st
from Pages import AdminPage, UserPage
from Args import Args
from DBUtils.DBUtils import DBUtils
import hashlib

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
                if username and password:
                    db_utils = DBUtils(self.args)
                    user = db_utils.user_login(username, password)
                    if not user.empty:
                        stored_password = user.iloc[0]['password']
                        hashed_password = hashlib.sha256(password.encode()).hexdigest()
                        if hashed_password == stored_password:
                            st.session_state.update({
                                'authentication_status': True,
                                'authentication_username': username,
                                'authentication_role': user.iloc[0]['role'],
                                'current_page': user.iloc[0]['role']
                            })
                            st.rerun()
                        else:
                            st.error("用户名或密码错误")
                    else:
                        st.error("该用户不存在")

class MainPage():
    def __init__(self):
        self.args = Args()
        self.page_handlers = {
            'admin': AdminPage(self.args),
            'user': UserPage(),
            'heatmap': self._load_heatmap,
            'ms1': self._load_ms1,
            'ms2': self._load_ms2,
            'report': self._load_report
        }

    def run(self):
        self.init_session_state()
        self.show_main_page()     

    def show_main_page(self):
        if not st.session_state['authentication_status']:
            self._show_landing_page()
        else:
            self._route_page()

    def _show_landing_page(self):
        st.markdown("# Welcome TDvis !🎉")
        st.markdown("_化学实验中心数据可视化网站_")
        if st.button("进入网站"):
            login_page = LoginPage(self.args)
            login_page.run()

    def _route_page(self):
        current_page = st.session_state.get('current_page', '')
        handler = self.page_handlers.get(current_page, self._default_page)
        # 显式处理角色页面
        if isinstance(handler, (AdminPage, UserPage)):
            handler.run()
        elif callable(handler):
            handler()
        else:
            self._default_page()

    def _default_page(self):
        role = st.session_state['authentication_role']
        st.session_state['current_page'] = role
        st.rerun()

    def _load_heatmap(self):
        from Pages.UserPages.Heatmap_showpage import Heatmap
        Heatmap().run()

    def _load_ms1(self):
        st.write("MS1 页面占位符")

    def _load_ms2(self):
        st.write("MS2 页面占位符")

    def _load_report(self):
        st.write("Report 页面占位符")

    def init_session_state(self):
        defaults = {
            'authentication_status': False,
            'authentication_username': "",
            'authentication_role': "",
            'current_page': ""
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

if __name__ == "__main__":
    main_page = MainPage()
    main_page.run()