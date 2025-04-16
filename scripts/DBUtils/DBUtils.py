import json  # Add json module import
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
        """
        try:
            # 参数化查询防止SQL注入
            user_info = self.db.select_data_to_df(
                "users", 
                columns=["*"], 
                condition="username = %s",  # 占位符方式
                params=(username,)
            )
            
            if not user_info.empty:
                return False

            encoded_password = self.encode_password(password)
            # 使用参数化插入
            return self.db.insert_data(
                "users",
                columns=["username", "password", "role","file_addresses"],
                values=(username, encoded_password, role,'[]' )
            )
        except Exception as e:
            print(f"注册失败: {str(e)}")
            return False
        
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
            return pd.DataFrame()  

    def update_user(self, old_username: str, new_username: str, new_role: str) -> bool:
        """
        更新用户信息
        :param old_username: 原始用户名
        :param new_username: 新用户名（可为空表示不修改）
        :param new_role: 新角色（可为空表示不修改）
        :return: 是否更新成功
        """
        try:
            # 根据数据库类型选择占位符
            if isinstance(self.db, PostgreUtils):
                placeholder = "%s"
            elif isinstance(self.db, SqliteUtils):
                placeholder = "?"
            else:
                raise ValueError("Unsupported database type")

            # 构建 SET 子句和参数列表
            set_clauses = []
            params = []

            if new_username:
                set_clauses.append(f"username = {placeholder}")
                params.append(new_username)
            if new_role:
                set_clauses.append(f"role = {placeholder}")
                params.append(new_role)

            # 没有需要更新的字段则直接返回成功
            if not set_clauses:
                return True

            # 构建完整的UPDATE语句
            set_clause = ", ".join(set_clauses)
            condition = f"username = {placeholder}"
            params.append(old_username)

            query = f"UPDATE users SET {set_clause} WHERE {condition}"

            # 执行参数化查询
            result = self.db.execute_query(query, params=params)
            return result.rowcount > 0

        except Exception as e:
            print(f"更新用户失败: {str(e)}")
            return False
        
    def add_file_address(self, username: str, file_path: str) -> bool:
        #自动将双引号过滤掉,确保能够被识别为windows中的地址
        sanitized_path = file_path.replace('"', '')  # Remove all double quotes
        
        try:
            if isinstance(self.db, PostgreUtils):
                placeholder = "%s"
            elif isinstance(self.db, SqliteUtils):
                placeholder = "?"
            else:
                raise ValueError("Unsupported database type")
            
            array_append_expr = self.json_array_append("file_addresses", "$", placeholder)
            query = (
                f"UPDATE users SET file_addresses = {array_append_expr} "
                f"WHERE username = {placeholder}"
            )
            
            params = (sanitized_path, username)  # Use sanitized path
            
            self.db.execute_non_query(query, params=params)
            return True
                
        except Exception as e:
            print(f"Failed to add file address: {str(e)}")
            return False

    def get_file_addresses(self, username: str) -> list:
        try:
            result = self.db.select_data_to_df(
                "users",
                columns=["file_addresses"],
                condition="username = %s",  # PostgreSQL 使用 %s 占位符
                params=(username,),
                limit=0,
                offset=0
            )
            return result.iloc[0]['file_addresses'] if not result.empty else []
        except Exception as e:
            print(f"Error retrieving file addresses: {str(e)}")
            return []

    def update_file_addresses(self, username: str, file_addresses: list) -> bool:
        """
        Update file addresses for a user
        :param username: The username to update
        :param file_addresses: List of file addresses
        :return: True if successful, False otherwise
        """
        try:
            # Convert list to JSON string
            file_addresses_json = json.dumps(file_addresses)
            
            # Build update query
            query = "UPDATE users SET file_addresses = %s WHERE username = %s"
            
            # Execute query
            self.db.execute_non_query(query, (file_addresses_json, username))
            return True
        except Exception as e:
            print(f"Failed to update file addresses: {str(e)}")
            return False

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

    def json_array_append(self, column: str, path: str, placeholder: str) -> str:
        if isinstance(self.db, PostgreUtils):
            return f"{column}::jsonb || jsonb_build_array({placeholder})"
        elif isinstance(self.db, SqliteUtils):
            return f"json_insert({column}, '$[#]', {placeholder})"
        else:
            raise ValueError("Unsupported database type")