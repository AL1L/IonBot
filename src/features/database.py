import sqlite3
import warnings

import pymysql
from buildabot import Feature
import threading

meta = {
    'class': 'Database',
    'name': 'Database',
    'description': 'Use a database'
}

class Query(object):

    def __init__(self, context):
        self.context = context

    def fetch(self, *args, **kwargs) -> list:
        pass

    def fetch_many(self, *args, **kwargs) -> list:
        pass

    def fetch_all(self, *args, **kwargs) -> list:
        pass

    def close(self):
        pass

    def __iter__(self, *args, **kwargs):
        return self

    def __next__(self):
        fetch = self.fetch()
        if fetch is None:
            raise StopIteration
        return fetch


class Database(Feature):

    def __init__(self, fm, m):
        super().__init__(fm, m)
        self.cursors = []
        self.type: str = 'SQLite'
        self.threads = {}

    def disconnect(self, thread=None):
        if thread is None:
            thread = threading.get_ident()

        if thread not in self.threads:
            return

        database = self.threads[thread]

        if self.type == 'SQLite':
            database.close()
        elif self.type == 'MySQL':
            database.close()

        del self.threads[thread]

    def db(self, thread=None):
        if thread is None:
            thread = threading.get_ident()

        if thread in self.threads:
            return self.threads[thread]

        self.type = self.config['type']

        if self.type == 'SQLite':
            self.threads[thread] = sqlite3.connect(self.config['database'])
        elif self.type == 'MySQL':
            self.threads[thread] = pymysql.connect(host=self.config['host'],
                                            user=self.config['user'],
                                            passwd=self.config['password'],
                                            db=self.config['database'],
                                            cursorclass=pymysql.cursors.Cursor,
                                            autocommit=True)
        else:
            raise ValueError('Invalid database type')

        return self.threads[thread]

    async def on_enable(self):
        self.db()

    async def on_disable(self):
        self.disconnect()

    def execute(self, *args, no_return=False, disconnect=False, **kwargs) -> Query:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            try:
                if self.type == 'SQLite':
                    cursor = self.db().cursor()
                    self.cursors.append(cursor)
                    sql = args[0].replace('%s', '?').replace('%d', '?').replace("AUTO_INCREMENT", "AUTOINCREMENT")
                    cursor.execute(sql, *args[1:], **kwargs)
                    self.commit()
                    if not no_return:
                        return SqliteQuery(cursor)
                    else:
                        cursor.close()
                elif self.type == 'MySQL':
                    cursor = self.db().cursor()
                    self.cursors.append(cursor)
                    sql = args[0].replace('?', '%s')
                    cursor.execute(sql, *args[1:], **kwargs)
                    self.commit()
                    if not no_return:
                        return MySQLQuery(cursor)
                    else:
                        cursor.close()
                        self.commit()
            except pymysql.err.InterfaceError:
                self.logger.debug('InterfaceError, database must have been closed. Reconnecting to database')
                self.disconnect()
                return self.execute(*args, no_return=no_return, **kwargs)
            except pymysql.err.OperationalError as e:
                if e.args[0] == 2013 or e.args[0] == 2006:
                    self.logger.debug('Lost connection to MySQL server during query. Reconnecting to database')
                    self.disconnect()
                    return self.execute(*args, no_return=no_return, **kwargs)
                else:
                    raise e

    def commit(self):
        if self.type == 'SQLite':
            self.db().commit()
        else:
            for c in self.cursors:
                c.close()
            self.cursors = []


class SqliteQuery(Query):

    def __init__(self, context):
        super().__init__(context)

    def fetch(self, *args, **kwargs):
        return self.context.fetchone(*args, **kwargs)

    def fetch_many(self, *args, **kwargs):
        return self.context.fetchmany(*args, **kwargs)

    def fetch_all(self, *args, **kwargs):
        return self.context.fetchall(*args, **kwargs)

    def close(self):
        self.context.close()


class MySQLQuery(Query):

    def __init__(self, context):
        super().__init__(context)

    def fetch(self, *args, **kwargs):
        return self.context.fetchone(*args, **kwargs)

    def fetch_many(self, *args, **kwargs):
        return self.context.fetchmany(*args, **kwargs)

    def fetch_all(self, *args, **kwargs):
        return self.context.fetchall(*args, **kwargs)

    def close(self):
        self.context.close()
