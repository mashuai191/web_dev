#!/usr/bin/env python
# coding=utf-8

import mysql.connector

def connectdb():
    print('连接到mysql服务器...')
    # 打开数据库连接
    # 用户名:hp, 密码:Hp12345.,用户名和密码需要改成你自己的mysql用户名和密码，并且要创建数据库TESTDB，并在TESTDB数据库中创建好表Student
    db = mysql.connector.connect(user="shuai_test", passwd="P@ssw0rd1234", host='159.89.132.69', database="shuai_test", use_unicode=True)
    print('连接上了!')
    return db

def createtable(db):
    # 使用cursor()方法获取操作游标 
    cursor = db.cursor()

    # 如果存在表Sutdent先删除
    cursor.execute("DROP TABLE IF EXISTS Student")
    sql = """CREATE TABLE Student (
            ID CHAR(10) NOT NULL,
            Name CHAR(8),
            Grade INT )"""

    # 创建Sutdent表
    cursor.execute(sql)

def insertdb(db, sql_cmd):
    # 使用cursor()方法获取操作游标 
    cursor = db.cursor()

    # SQL 插入语句
    #sql = """INSERT INTO Student
    #     VALUES ('001', 'CZQ', 70),
    #            ('002', 'LHQ', 80),
    #            ('003', 'MQ', 90),
    #            ('004', 'WH', 80),
    #            ('005', 'HP', 70),
    #            ('006', 'YF', 66),
    #            ('007', 'TEST', 100)"""

    #sql = "INSERT INTO Student(ID, Name, Grade) \
    #    VALUES ('%s', '%s', '%d')" % \
    #    ('001', 'HP', 60)
    try:
        # 执行sql语句
        cursor.execute(sql_cmd)
        # 提交到数据库执行
        db.commit()
        
    except Exception, e:
        # Rollback in case there is any error
        print 'Insert data fail!'
        print e
        db.rollback()
        return False
    return True

def querydb(db, sql_cmd):
    # 使用cursor()方法获取操作游标 
    cursor = db.cursor()

    # SQL 查询语句
    #sql = "SELECT * FROM Student \
    #    WHERE Grade > '%d'" % (80)
    #sql = "SELECT * FROM Student"
    try:
        # 执行SQL语句
        cursor.execute(sql_cmd)
        # 获取所有记录列表
        results = cursor.fetchall()
        return results
    except Exception, e:
        print e
        print "Error: unable to fecth data"

def deletedb(db):
    # 使用cursor()方法获取操作游标 
    cursor = db.cursor()

    # SQL 删除语句
    sql = "DELETE FROM Student WHERE Grade = '%d'" % (100)

    try:
       # 执行SQL语句
       cursor.execute(sql)
       # 提交修改
       db.commit()
    except:
        print '删除数据失败!'
        # 发生错误时回滚
        db.rollback()

def updatedb(db, sql_cmd):
    # 使用cursor()方法获取操作游标 
    cursor = db.cursor()

    # SQL 更新语句
    #sql = "UPDATE Student SET Grade = Grade + 3 WHERE ID = '%s'" % ('003')

    try:
        # 执行SQL语句
        cursor.execute(sql_cmd)
        # 提交到数据库执行
        db.commit()
        return True
    except Exception, e:
        print '更新数据失败!', e
        # 发生错误时回滚
        db.rollback()
        return False

def closedb(db):
    db.close()

def main():
    db = connectdb()    # 连接MySQL数据库

    createtable(db)     # 创建表
    insertdb(db)        # 插入数据
    print '\n插入数据后:'
    querydb(db) 
    deletedb(db)        # 删除数据
    print '\n删除数据后:'
    querydb(db)
    updatedb(db)        # 更新数据
    print '\n更新数据后:'
    querydb(db)

    closedb(db)         # 关闭数据库

if __name__ == '__main__':
    main()
