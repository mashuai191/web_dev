#!/usr/bin/env python
# coding=utf-8

import mysql.connector
import logging

def connectdb():
    logging.getLogger().info('Connecting to MySQL sever...')
    # 打开数据库连接
    # dev env
    db = mysql.connector.connect(user="shuai_test", passwd="P@ssw0rd1234", host='159.89.132.69', database="shuai_test", use_unicode=True)
    # production env
    #db = mysql.connector.connect(user="root", passwd="Philips@123", host='rm-uf6s5852kgoy3842v.mysql.rds.aliyuncs.com', database="shuai_test", use_unicode=True)

    logging.getLogger().info('Connected!')

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

    try:
        # 执行sql语句
        cursor.execute(sql_cmd)
        # 提交到数据库执行
        db.commit()
        
    except Exception, e:
        # Rollback in case there is any error
        logging.getLogger().info("Error: unable to insert data")
        logging.getLogger().info(e)
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
        logging.getLogger().info("Error: unable to fecth data")
        logging.getLogger().info(e)

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
        logging.getLogger().info("Error: unable to delete data")
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
        logging.getLogger().info("Error: unable to update data")
        logging.getLogger().info(e)
        # 发生错误时回滚
        db.rollback()
        return False

def closedb(db):
    db.close()

def main():
    db = connectdb()    # 连接MySQL数据库

    createtable(db)     # 创建表
    insertdb(db)        # 插入数据
    querydb(db) 
    deletedb(db)        # 删除数据
    querydb(db)
    updatedb(db)        # 更新数据
    querydb(db)

    closedb(db)         # 关闭数据库

if __name__ == '__main__':
    main()
