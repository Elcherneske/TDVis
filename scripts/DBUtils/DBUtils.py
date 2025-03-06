class DBUtils:
<<<<<<< Updated upstream
    def __init__(self):
        pass
    
    

=======
    def __init__(self, args):
        self.args = args
        db_mode = self.args.get_config("database", "mode")
        if db_mode == "sqlite":
            self.db = SqliteUtils(self.args)
        elif db_mode == "postgresql":
            dbname = self.args.get_config("database", "dbname")
            user = self.args.get_config("database", "user")
            password = self.args.get_config("database", "password",default="041104")
            host = self.args.get_config("database", "host", default='localhost')
            port = self.args.get_config("database", "port", default='5432')
            self.db = PostgreUtils(dbname, user, password, host, port)
        else:
            raise ValueError(f"Unsupported database mode: {db_mode}")

    def user_login(self, username: str, password: str) -> pd.DataFrame:
        """
        用户登录
        :param username: 用户名
        :param password: 存储的加密密码
        :return: 用户信息
        """
        # 查询用户信息
        user_info = self.db.select_data_to_df("users", columns=["*"], condition=f"username = '{username}'")
        # todo 在用户信息的列表中进一步添加用户文件的管理
        if not user_info.empty:
                return user_info
        else:
            return pd.DataFrame()  # 用户不存在，返回空DataFrame

    def user_register(self, username: str, password: str, role: str) -> bool:
        """
        用户注册
        :param username: 用户名
        :param password: 密码
        :param role: 角色
        :return: 是否注册成功
        """

        # 检查表是否存在，如果不存在则创建表
        if self.db.count_data("users") == -1:
            self.db.create_table("users", columns=[])

        # 检查用户是否已存在
        user_info = self.db.select_data_to_df("users", columns=["*"], condition=f"username = '{username}'")
        if not user_info.empty:
            return False  # 用户已存在，注册失败

        # todo 暂时留下文件路径的接口
        file_path = f"files/{username}"

        # 插入新用户信息
        try:
            self.db.insert_data("users", columns=["username", "password", "role", "file_path"], values=[username, password, role, file_path])
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
            user_info['database_type'] = self.args.get_config("database", "mode")
            return user_info
        except Exception as e:
            print(f"查询用户失败: {str(e)}")
            return pd.DataFrame()  # 查询失败，返回空DataFrame

    def update_user(self, username: str, role: str) -> bool:
        """
        更新用户
        :param username: 用户名
        :param role: 角色
        :return: 是否更新成功
        """
        try:
            # 构建更新用户的SQL语句
            update_query = f"UPDATE users SET role = '{role}' WHERE username = '{username}'"
            # 执行更新操作
            self.db.execute_query(update_query)
            return True  # 更新成功
        except Exception as e:
            print(f"更新用户失败: {str(e)}")
            return False  # 更新失败
