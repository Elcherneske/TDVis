class MainPage():
    def __init__(self):
        self.args = Args()
        # 定义子页面路由表（未来扩展在此添加）
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
        """未登录时的首页"""
        st.markdown("# Welcome TDvis !🎉")
        st.markdown("_化学实验中心数据可视化网站_")
        if st.button("登录"):
            login_page = LoginPage(self.args)
            login_page.run()

    def _route_page(self):
        """动态路由到子页面"""
        current_page = st.session_state.get('current_page', '')
        handler = self.page_handlers.get(current_page, self._default_page)
        handler() if callable(handler) else handler.run()

    def _default_page(self):
        """默认回退到角色对应页面"""
        role = st.session_state['authentication_role']
        st.session_state['current_page'] = role
        st.rerun()

    #--------------- 预留子页面接口 ---------------
    def _load_ms1(self):
        from Pages.UserPages import MS1Page  # 假设 MS1Page 存在
        MS1Page().run()

    def _load_ms2(self):
        from Pages.UserPages import MS2Page  # 假设 MS2Page 存在
        MS2Page().run()

    def _load_report(self):
        from Pages.UserPages import ReportPage  # 假设 ReportPage 存在
        ReportPage().run()

    def _load_heatmap(self):
        from Pages.UserPages.Heatmap_showpage import Heatmap
        Heatmap().run()

    def init_session_state(self):
        """初始化所有会话状态"""
        defaults = {
            'authentication_status': False,
            'authentication_username': "",
            'authentication_role': "",
            'current_page': ""
        }
        for key, value in defaults.items():
            if key not in st.session_state: