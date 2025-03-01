import psycopg2
from typing import List, Tuple, Any, Optional

class PostgreUtils:
    def __init__(self, dbname: str, user: str, password: str, host: str = 'localhost', port: str = '5432'):
        """初始化数据库连接参数"""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """建立数据库连接"""
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise Exception(f"数据库连接失败: {str(e)}")

    def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_table(self, table_name: str, columns: List[str]) -> None:
        """
        创建数据表
        :param table_name: 表名
        :param columns: 列定义列表，例如 ["id SERIAL PRIMARY KEY", "name VARCHAR(100)"]
        """
        try:
            columns_str = ", ".join(columns)
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
            self.cursor.execute(create_table_query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"创建表失败: {str(e)}")

    def insert_data(self, table_name: str, columns: List[str], values: List[Any]) -> None:
        """
        插入数据
        :param table_name: 表名
        :param columns: 列名列表
        :param values: 值列表
        """
        try:
            columns_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, values)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"插入数据失败: {str(e)}")

    def select_data(self, table_name: str, columns: List[str] = ["*"], 
                    condition: str = None) -> List[Tuple]:
        """
        查询数据
        :param table_name: 表名
        :param columns: 要查询的列名列表
        :param condition: WHERE条件语句
        :return: 查询结果列表
        """
        try:
            columns_str = ", ".join(columns)
            select_query = f"SELECT {columns_str} FROM {table_name}"
            if condition:
                select_query += f" WHERE {condition}"
            self.cursor.execute(select_query)
            return self.cursor.fetchall()
        except Exception as e:
            raise Exception(f"查询数据失败: {str(e)}")

    def delete_data(self, table_name: str, condition: str) -> None:
        """
        删除数据
        :param table_name: 表名
        :param condition: WHERE条件语句
        """
        try:
            delete_query = f"DELETE FROM {table_name} WHERE {condition}"
            self.cursor.execute(delete_query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"删除数据失败: {str(e)}")

    def drop_table(self, table_name: str) -> None:
        """
        删除表
        :param table_name: 表名
        """
        try:
            drop_query = f"DROP TABLE IF EXISTS {table_name}"
            self.cursor.execute(drop_query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"删除表失败: {str(e)}") 