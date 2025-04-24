import psycopg2
import io
from psycopg2.extras import execute_values
from sqlalchemy import create_engine
from typing import List, Tuple, Any
import pandas as pd
import polars as pl
class PostgreUtils:
    def __init__(self, args):
        """初始化数据库连接参数"""
        self.dbname = args.get_config("Database", "dbname")
        self.user = args.get_config("Database", "user")
        self.password = args.get_config("Database", "password")
        self.host = args.get_config("Database", "host")
        self.port = args.get_config("Database", "port")
        self.conn = None
        self.cursor = None
        # 新增SQLAlchemy连接
        self.engine = create_engine(f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}')

    def _connect(self):
        """建立数据库连接"""
        try:
            conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            cursor = conn.cursor()
            return conn, cursor
        except Exception as e:
            raise Exception(f"数据库连接失败: {str(e)}")

    def execute_query(self, sql: str, params: tuple = None) -> pd.DataFrame:
        try:
            conn, cursor = self._connect()
            cursor.execute(sql, params)
            if sql.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                return pd.DataFrame(data, columns=columns)
            return pd.DataFrame()
        except Exception as e:
            raise Exception(f"执行查询失败: {str(e)}\nSQL: {sql}\n参数: {params}")
        finally:
            cursor.close()
            conn.close()

    def begin_transaction(self):
        self.conn, self.cursor = self._connect()
        
    def commit_transaction(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
        
    def rollback_transaction(self):
        self.conn.rollback()
        self.cursor.close()
        self.conn.close()

    # In PostgreUtils class
    def execute_non_query(self, query: str, params=None) -> int:
        try:
            conn, cursor = self._connect()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except psycopg2.Error as e:
            print(f"Query failed: {str(e)}")
            return 0
        finally:
            cursor.close()
            conn.close()
            
    def param_placeholder(self) -> str:
        """
        返回PostgreSQL的参数占位符
        :return: 占位符字符串
        """
        return "%s"
    def create_table(self, table_name: str, columns: List[str]) -> None:
        """
        创建数据表
        :param table_name: 表名
        :param columns: 列定义列表，例如 ["id SERIAL PRIMARY KEY", "name VARCHAR(100)"]
        """
        if table_name == "users" and not columns:
            columns = ["id SERIAL PRIMARY KEY", "username VARCHAR(100)", "password VARCHAR(100)", "role VARCHAR(50)", "file_path VARCHAR(255)"]
        try:
            conn, cursor = self._connect()
            columns_str = ", ".join(columns)#存储为csv格式
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
            cursor.execute(create_table_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"创建表失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    def insert_data(self, table_name: str, columns: List[str], values: List[Any]) -> None:
        """
        插入数据
        :param table_name: 表名
        :param columns: 列名列表
        :param values: 值列表
        """
        try:
            conn, cursor = self._connect()
            columns_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            cursor.execute(insert_query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"插入数据失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def insert_batch_data(self, table_name: str, columns: List[str], values: List[Tuple[Any]]) -> None:
        """
        批量插入数据
        :param table_name: 表名
        :param columns: 列名列表
        :param values: 值列表
        """
        try:
            conn, cursor = self._connect()
            columns_str = ", ".join(columns)
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES %s"
            execute_values(cursor, insert_query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"批量插入数据失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def copy_insert(self, data: pl.DataFrame, table_name: str):
        """
        使用copy命令插入数据
        :param data: 数据框
        :param table_name: 表名
        """
        try:
            output = io.BytesIO()
            data.write_csv(output, include_header=False)
            conn, cursor = self._connect()
            output.seek(0)
            cursor.copy_from(output, table_name, sep=',', null="")
            conn.commit()
            conn.close()
        except Exception as e:
            raise Exception(f"copy插入数据失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def select_data(self, table_name: str, columns: List[str] = ["*"], condition: str = None, limit: int = None,
                    offset: int = None) -> List[Tuple]:
        """
        查询数据
        :param table_name: 表名
        :param columns: 要查询的列名列表
        :param condition: WHERE条件语句
        :param limit: 限制查询结果数量
        :param offset: 偏移量
        :return: 查询结果列表
        """
        try:
            conn, cursor = self._connect()
            columns_str = ", ".join(columns)
            select_query = f"SELECT {columns_str} FROM {table_name}"
            if condition:
                select_query += f" WHERE {condition}"
            if limit:
                select_query += f" LIMIT {limit}"
            if offset:
                select_query += f" OFFSET {offset}"
            cursor.execute(select_query)
            return cursor.fetchall()
        except Exception as e:
            raise Exception(f"查询数据失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def select_data_to_df(
        self,
        table_name: str,
        columns: List[str] = ["*"],
        condition: str = None,
        params: tuple = None,
        limit: int = None,
        offset: int = None
    ) -> pd.DataFrame:
        try:
            columns_str = ", ".join(columns)
            select_query = f"SELECT {columns_str} FROM {table_name}"
            if condition:
                select_query += f" WHERE {condition}"
            if limit:
                select_query += f" LIMIT {limit}"
            if offset:
                select_query += f" OFFSET {offset}"
            # 直接使用execute_query处理SQLAlchemy连接
            return self.execute_query(select_query, params=params)
        except Exception as e:
            raise Exception(f"查询数据失败: {str(e)}")

    def count_data(self, table_name: str, condition: str = None) -> int:
        """
        查询数据数量
        :param table_name: 表名
        :param condition: WHERE条件语句
        :return: 数据数量
        """
        try:
            conn, cursor = self._connect()
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            if condition:
                count_query += f" WHERE {condition}"
            cursor.execute(count_query)
            return cursor.fetchone()[0]
        except Exception as e:
            raise Exception(f"查询数据数量失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def delete_data(self, table_name: str, condition: str, params: tuple = None) -> None:
        """
        删除数据
        :param table_name: 表名
        :param condition: WHERE条件语句
        :param params: 参数元组(可选)
        """
        try:
            conn, cursor = self._connect()
            if params:
                delete_query = "DELETE FROM {} WHERE {}".format(table_name, condition)
                cursor.execute(delete_query, params)
            else:
                delete_query = f"DELETE FROM {table_name} WHERE {condition}"
                cursor.execute(delete_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"删除数据失败: {str(e)}")
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if conn and not conn.closed:
                conn.close()

    def drop_table(self, table_name: str) -> None:
        """
        删除表
        :param table_name: 表名
        """
        try:
            conn, cursor = self._connect()
            drop_query = f"DROP TABLE IF EXISTS {table_name}"
            cursor.execute(drop_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"删除表失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def update_data(self, table_name: str, set_clause: str, condition: str, params: tuple) -> None:
        """
        更新数据
        :param table_name: 表名
        :param set_clause: SET子句
        :param condition: WHERE条件语句
        :param params: 参数列表
        """
        try:
            self.begin_transaction()
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
            self.cursor.execute(update_query, params)
            self.commit_transaction()
        except Exception as e:
            self.rollback_transaction()
            raise Exception(f"更新数据失败: {str(e)}")
        finally:
            cursor.close()
            conn.close()
