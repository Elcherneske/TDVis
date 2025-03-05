import streamlit as st

class ShowPage():
    def __init__(self):
        pass

    def run(self):
        self.show_show_page()

    def show_show_page(self):
        #todo: 展示页面(需求参考梦婷师姐的PPT)
        # 具体步骤：在本地某个路径下找到st.session_state['user_select_file']，然后读取文件，解析文件画图
        st.title("展示页面")
        with st.sidebar:
            if st.button("重新选择"):
                st.session_state['user_select_file'] = None
                st.rerun()
            if st.button("链接其他斜面"):
                st.write("链接其他斜面按钮被点击")

        st.line_chart([1, 2, 3, 4, 5])
