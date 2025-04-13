import streamlit as st
from Pages import AdminPage, UserPage
from Args import Args
from DBUtils.DBUtils import DBUtils

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
                    user = db_utils.user_login(username, password)  # 自动处理哈希验证
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
        self.page_handlers = {
            'showpage': self._load_showpage,
            'heatmap': self._load_heatmap,#展示功能页面的调度函数
            'toppic': self._load_toppic,
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
            self._route_page()#网站内部页面导航

    def _show_landing_page(self):
        st.markdown("# Welcome TDvis !🎉")
        st.markdown("_化学实验中心数据可视化网站_")
        if st.button("进入网站"):
            login_page = LoginPage(self.args)
            login_page.run()

    def _route_page(self):
        current_page = st.session_state.get('current_page', '')
        file_select=st.session_state.get('user_select_file', '')
        handler = self.page_handlers.get(current_page, self._default_page)#如果没有,那么就是默认界面,也就是首页
        if  file_select:
            if callable(handler):
                handler()
                #原计划是把报告界面拆分出来的,留下接口
        else:
            self._default_page()

    def _default_page(self):#进入用户界面或者管理员界面
        role = st.session_state['authentication_role']
        if role == 'admin':
            AdminPage(self.args).run()
        elif role == 'user':
            UserPage().run()

    def _load_showpage(self):
        from Pages.FunctionPages.ShowPage import ShowPage
        ShowPage().run()
    def _load_heatmap(self):
        from Pages.FunctionPages.HeatmapPage import Heatmap
        Heatmap().run()

    def _load_toppic(self):
        from Pages.FunctionPages.ToppicPage import ToppicShowPage
        ToppicShowPage().run()

    def _load_ms2(self):
        st.write("MS2 页面占位符")

    def _load_report(self):
        st.write("Report 页面占位符")

    def init_session_state(self):
        defaults = {
            'authentication_status': False,
            'authentication_username': "",
            'authentication_role': "",
            'current_page': "",
            'user_select_file': ""
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

if __name__ == "__main__":
    main_page = MainPage()
    main_page.run()