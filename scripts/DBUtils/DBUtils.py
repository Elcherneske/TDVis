import pandas as pd
from .PostgreUtils import PostgreUtils
from .SqliteUtils import SqliteUtils
import hashlib

class DBUtils:
    def __init__(self,args):
        self.args = args
        db_mode = self.args.get_config("Database", "mode")
        if db_mode == "sqlite":
            self.db = SqliteUtils(self.args)
        elif db_mode == "postgresql":
            self.db = PostgreUtils(self.args)
        else:
            raise ValueError(f"不支持的数据库模式: {db_mode}")

    @staticmethod
    def encode_password(password: str) -> str:
        """_summary_
        对密码进行的哈希加密方式(后续可以该换其他的加密方式)
        """
        return hashlib.sha256(password.encode()).hexdigest()
        
    def user_login(self, username: str, password: str) -> pd.DataFrame:
        """
        用户登录
        :param username: 用户名
        :param password: 存储的加密密码
        :return: 用户信息
        """
        # 查询用户信息
        encoded_password = self.encode_password(password)
        return self.db.select_data_to_df(
            "users", 
            columns=["*"], 
            condition=f"username = '{username}' AND password = '{encoded_password}'"
        )

    def user_register(self, username: str, password: str, role: str) -> bool:
        """
        用户注册
        :param username: 用户名
        :param password: 密码
        :param role: 角色
        :return: 是否注册成功
        """

        self.db.create_table("users", columns=["username VARCHAR(100)", "password VARCHAR(100)", "role VARCHAR(100)"])

        # 检查用户是否已存在
        user_info = self.db.select_data_to_df("users", columns=["*"], condition=f"username = '{username}'")
        if not user_info.empty:
            return False  # 用户已存在，注册失败
        # todo 暂时留下文件路径的接口
        #file_path = f"files/{username}"
        # 插入新用户信息,存储加密后的密码
        encoded_password = self.encode_password(password)
        try:
            self.db.insert_data("users", columns=["username", "password", "role",], values=[username, encoded_password, role])
            return True  # 注册成功
        except Exception as e:
            print(f"注册用户失败: {str(e)}")
            return False  # 注册失败

    def query_users(self, conditions: str, limit: int, offset: int) -> pd.DataFrame:
        """
        查询用户
        :param conditions: 条件
        :param limit: 限制
        :param offset: 偏移
        :return: 查询结果DataFrame,包含数据库类型信息
        """
        try:
            # 查询用户数据
            user_info = self.db.select_data_to_df("users", columns=["*"], condition=conditions, limit=limit, offset=offset)
            # 添加数据库类型信息
            user_info.index = user_info.index+1
            return user_info
        except Exception as e:
            print(f"查询用户失败: {str(e)}")
            return pd.DataFrame()  # 查询失败，返回空DataFrame

    def update_user(self, old_username: str, new_username: str, role: str) -> bool:
        """
        更新用户
        :param old_username: 旧用户名
        :param new_username: 新用户名
        :param role: 角色
        :return: 是否更新成功
        """
        try:
            # 构建set_clause
            set_clause_parts = []
            if new_username:
                set_clause_parts.append(f"username = '{new_username}'")
            if role:
                set_clause_parts.append(f"role = '{role}'")
            set_clause = ", ".join(set_clause_parts)
            
            # 使用update_data方法执行更新操作
            condition = f"username = '{old_username}'"
            self.db.update_data("users", set_clause, condition)
            return True  # 更新成功
        except Exception as e:
            print(f"更新用户失败: {str(e)}")
            return False  # 更新失败

    def delete_data(self, table_name: str, condition: str) -> None:
        """
        删除数据
        :param table_name: 表名
        :param condition: WHERE条件语句
        """
        try:
            self.db.delete_data(table_name, condition)
        except Exception as e:
            print(f"删除数据失败: {str(e)}")
            raise Exception(f"删除数据失败: {str(e)}")
