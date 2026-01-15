import psycopg2
from psycopg2 import Error, sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class SQLHandler:
    def __init__(self, host_name: str, user_name: str, user_password: str, database_name: str = None, ssl_ca=None):
        self.host_name = host_name
        self.username = user_name
        self.password = user_password
        self.database_name = database_name
        self.ssl_ca = ssl_ca
        self.connection = self._create_server_connection(
            host_name, user_name, user_password, database_name)

    def _create_server_connection(self, host_name: str, user_name: str, user_password: str, database_name: str = None):
        connection = None
        try:
            connection = psycopg2.connect(
                host=host_name,
                user=user_name,
                password=user_password,
                database=database_name if database_name else 'postgres',
                sslmode='require' if self.ssl_ca else 'prefer'
            )
            print("PostgreSQL Database connection successful")
        except Error as err:
            print(f"Error: '{err}'")
        return connection

    def get_connection(self):
        return self.connection

    def _create_database(self, cursor, database_name: str):
        try:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(
                    sql.Identifier(database_name)
                )
            )
        except Error as err:
            print(f"Failed creating database: {err}")
            exit(1)

    def _load_database(self, database_name: str):
        try:
            cursor = self.connection.cursor()
        except Error as err:
            print(f"Failed to load database: {err}")
            exit(1)
        try:
            print(f"Database {database_name} loaded successfully")
        except Error as err:
            print(f"Database {database_name} does not exist")
            print(err)
            exit(1)

    def create_table(self, name: str, column: str):
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            cursor.execute(f"CREATE TABLE {full_table_name} ({column})")
            self.connection.commit()
            print(f"Table {name} created successfully")
        except Error as err:
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def insert_row(self, name: str, column: str, data: tuple):
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {full_table_name} ({column}) VALUES ({placeholders})"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data Inserted:", data)
        except Error as err:
            print("Error inserting data")
            print(err)
            self.connection.rollback()
            # Check for duplicate key errors (PostgreSQL uses different error codes)
            if "duplicate key" in str(err).lower() or "unique constraint" in str(err).lower():
                return True  # Treat duplicate as success for compatibility
            return False
        finally:
            cursor.close()
        return True

    def close_connection(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
            print("PostgreSQL connection is closed")

    def delete_row(self, name: str, column: str, data: tuple):
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            query = f"DELETE FROM {full_table_name} WHERE {column} = %s"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data Deleted:", data)
        except Error as err:
            print("Error deleting data")
            print(err)
            self.connection.rollback()
            return False
        finally:
            cursor.close()
        return True

    def clear_table(self, name: str):
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            cursor.execute(f"DELETE FROM {full_table_name}")
            self.connection.commit()
            print("Table cleared successfully")
        except Error as err:
            print("Error clearing table")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def reset_auto_increment(self, name: str):
        cursor = self.connection.cursor()
        try:
            # PostgreSQL uses sequences instead of AUTO_INCREMENT
            full_table_name = f"patchwork_archive.{name}"
            sequence_name = f"patchwork_archive.{name}_id_seq"
            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1")
            self.connection.commit()
            print("Sequence reset successfully")
        except Error as err:
            print("Error resetting sequence")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def copy_rows_to_new_table(self, name: str, new_name: str, column: str):
        cursor = self.connection.cursor()
        try:
            # Prefix table names with schema
            full_table_name = f"patchwork_archive.{name}"
            full_new_table_name = f"patchwork_archive.{new_name}"
            cursor.execute(
                f"INSERT INTO {full_new_table_name} ({column}) SELECT {column} FROM {full_table_name}"
            )
            self.connection.commit()
            print("Rows copied successfully")
        except Error as err:
            print("Error copying rows")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def drop_table(self, name: str):
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            cursor.execute(f"DROP TABLE {full_table_name}")
            self.connection.commit()
            print("Table dropped successfully")
        except Error as err:
            print("Error dropping table")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def check_row_exists(self, name: str, column_name: str, value: str):
        """
        Checks if a row exists in a table
        """
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            cursor.execute(f"SELECT * FROM {full_table_name} WHERE {column_name} = %s", (value,))
            result = cursor.fetchone()
            if result:
                return True
            else:
                return False
        except Error as err:
            print("Error checking row")
            print(err)
            return False
        finally:
            cursor.close()

    def update_row(self, name: str, search_column: str, search_val: str, replace_col: str, replace_value: str):
        """
        Updates a row in a table
        """
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            query = f"UPDATE {full_table_name} SET {replace_col} = %s WHERE {search_column} = %s"
            # PostgreSQL handles UTF-8 natively, no need to encode
            cursor.execute(query, (replace_value, search_val))
            self.connection.commit()
            print("Row updated successfully")
        except Error as err:
            print("Error updating row")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def update_multiple_columns(self, name: str, search_column: str, search_val: str, update_dict: dict):
        """
        Updates multiple columns in a row with parameterized query
        :param name: table name
        :param search_column: column to search by
        :param search_val: value to search for
        :param update_dict: dictionary of column:value pairs to update
        """
        cursor = self.connection.cursor()
        try:
            # Prefix table name with schema
            full_table_name = f"patchwork_archive.{name}"
            
            # Build SET clause with parameterized placeholders
            set_clause = ", ".join([f"{col} = %s" for col in update_dict.keys()])
            query = f"UPDATE {full_table_name} SET {set_clause} WHERE {search_column} = %s"
            
            # Create values tuple (update values + search value)
            values = tuple(update_dict.values()) + (search_val,)
            
            cursor.execute(query, values)
            self.connection.commit()
            print("Multiple columns updated successfully")
        except Error as err:
            print("Error updating multiple columns")
            print(err)
            self.connection.rollback()
        finally:
            cursor.close()

    def execute_query(self, query: str):
        cursor = self.connection.cursor()
        try:
            # Add schema prefix if needed (replace bare table names with schema.table)
            modified_query = self._add_schema_prefix(query)
            cursor.execute(modified_query)
            self.connection.commit()
            try:
                result = cursor.fetchall()
                return result
            except:
                return None
        except Error as err:
            print("Error executing query")
            print(err)
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def get_query_result(self, query: str):
        cursor = self.connection.cursor()
        try:
            # Add schema prefix if needed
            modified_query = self._add_schema_prefix(query)
            cursor.execute(modified_query)
            result = cursor.fetchall()
            return result
        except Error as err:
            print("Error executing query")
            print(err)
            return None
        finally:
            cursor.close()

    def _add_schema_prefix(self, query: str) -> str:
        """
        Helper method to add schema prefix to table names in queries
        This is a simple implementation that handles common cases
        """
        # List of tables that need schema prefix
        tables = ['songs', 'files', 'romanized', 'channels', 'views', 'archive_log',
                  'archive_queue', 'archive_queue_auth', 'archive_worker_auth',
                  'worker_status', 'kv']

        modified_query = query
        for table in tables:
            # Handle FROM/JOIN clauses
            modified_query = modified_query.replace(f" FROM {table} ", f" FROM patchwork_archive.{table} ")
            modified_query = modified_query.replace(f" FROM {table}\n", f" FROM patchwork_archive.{table}\n")
            modified_query = modified_query.replace(f"FROM {table} ", f"FROM patchwork_archive.{table} ")

            # Handle UPDATE clauses
            modified_query = modified_query.replace(f"UPDATE {table} ", f"UPDATE patchwork_archive.{table} ")

            # Handle INSERT clauses
            modified_query = modified_query.replace(f"INTO {table} ", f"INTO patchwork_archive.{table} ")
            modified_query = modified_query.replace(f"INTO {table}(", f"INTO patchwork_archive.{table}(")

            # Handle DELETE clauses
            modified_query = modified_query.replace(f"DELETE FROM {table} ", f"DELETE FROM patchwork_archive.{table} ")

        return modified_query


if __name__ == "__main__":
    server = SQLHandler("localhost", "postgres", "password", "patchwork_archive")
