import pandas as pd
from .SqliteUtils import SqliteUtils
from .PostgreUtils import PostgreUtils

class DBUtils:
    def __init__(self, args):
        self.args = args
        if self.args.get_config("database", "mode") == "sqlite":
            self.db= SqliteUtils(self.args)
        elif self.args.get_config("database", "mode") == "postgresql":
            self.db = PostgreUtils(self.args)
    
    def user_login(self, username: str, password: str) -> pd.DataFrame:
        """
        用户登录
        :param username: 用户名
        :param password: 密码
        :return: 用户信息
        """
        pass

    def user_register(self, username: str, password: str) -> bool:
        """
        用户注册
        :param username: 用户名
        :param password: 密码
        :return: 是否注册成功
        """
        pass

    def query_users(self, conditions: str, limit: int, offset: int) -> pd.DataFrame:
        """
        查询用户
        :param conditions: 条件
        :param limit: 限制
        :param offset: 偏移
        """
        pass
    
    def update_user(self, username: str, role: str) -> bool:
        """
        更新用户
        :param username: 用户名
        :param role: 角色
        """
        pass
