import pymysql.cursors

def db_connect():
    connection = pymysql.connect(host='141.98.17.127',
                                port=33309,
                                user='root',
                                password='ZXCasdQWE$%^123',
                                database='Ict_award',
                                cursorclass=pymysql.cursors.DictCursor,
                                connect_timeout=100)
    return connection

connect = db_connect()
with connect.cursor() as cursor:
    connect.commit()
    sql = f'''
    select event_id, personnel_id
    from list_in_events 
    where event_id = 1 and personnel_id = 4
    limit 1
    '''

    cursor.execute(sql)
    result = cursor.fetchone()
    if bool(result):
        print("already")
    else:
        print("authorize to add data")
    # print(result)
# name = 'phanuphong_0001'
# id_ = name.split('_')
# print(id_[-1])