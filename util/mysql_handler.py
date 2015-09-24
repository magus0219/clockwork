# coding:utf-8
from DBUtils.PooledDB import PooledDB
from conf.server import MYSQL_DATABASES
import MySQLdb
from conf.server import ENVION as _eviron

class MysqlHandler(object):
    __dbpools = {}  # 连接池
    
    def __init__(self, conn):
        self.__conn = conn
    
    def select(self, sql):
        cursor = self.__conn.cursor()
        count = cursor.execute(sql)
        return count, cursor.fetchall()
    
    def select_count(self, sql):
        cursor = self.__conn.cursor()
        count = cursor.execute(sql)
        return count
    
    def select_unique(self, sql):
        cursor = self.__conn.cursor()
        count = cursor.execute(sql)
        if count :
            return cursor.fetchall()[0][0]
        return None
    
    def update(self, sql):
        cursor = self.__conn.cursor()
        count = cursor.execute(sql)
        cursor.execute('commit')
        return count
    
    def delete(self, sql):
        cursor = self.__conn.cursor()
        count = cursor.execute(sql)
        cursor.execute('commit')
        return count
    
    def insert(self, sql):
        cursor = self.__conn.cursor()
        count = cursor.execute(sql)
        cursor.execute('commit')
        return count
    
    def get_connection(self):
        return self.__conn
    
    @staticmethod
    #===========================================================================
    # create_by_instance    根据实例名返回DBHandler对象
    #    @instance    实例名，settings.DATABASES的键
    #===========================================================================
    def create_by_instance(instance):
        if instance not in MysqlHandler.__dbpools:
            MysqlHandler.__dbpools[instance] = PooledDB(creator=MySQLdb,
                                          mincached=MYSQL_DATABASES[instance]['MINCACHED'],
                                          maxcached=MYSQL_DATABASES[instance]['MAXCACHED'],
                                          
                                          host=MYSQL_DATABASES[instance]['HOST'],
                                          port=MYSQL_DATABASES[instance]['PORT'],
                                          user=MYSQL_DATABASES[instance]['USER'],
                                          passwd=MYSQL_DATABASES[instance]['PASSWORD'],
                                          
                                          db=MYSQL_DATABASES[instance]['DBNAME'],
                                          use_unicode=True,
                                          charset='utf8')
        return MysqlHandler(MysqlHandler.__dbpools[instance].connection())

def get_conn():            
    return MysqlHandler.create_by_instance(_eviron)