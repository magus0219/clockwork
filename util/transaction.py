# coding:utf-8
def commit_on_success(mysql_handler):
    def _inner(func):
        def _inner2(*args, **kwargs):
            cursor = mysql_handler.get_conn().cursor()
            cursor.execute('start transaction')
            try:
                result = func(*args, **kwargs)
                cursor.execute('commit')
            except Exception, e:
                cursor.execute('rollback')
                raise e
            return result
        return _inner2
    return _inner
