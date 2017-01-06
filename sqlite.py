#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import os.path

DB_NAME = "path/of/database"

class Sqlite3:
    def __init__(self):
        if not os.path.isfile(DB_NAME):
            self.open()
            self.createUserTable()
            self.createMonthlyTable()
            self.commit()
            self.close()

    def open(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn_cursor = self.conn.cursor()

    def close(self):
        self.conn_cursor.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def addTable(self, table, column):
        self.conn_cursor.execute("CREATE TABLE IF NOT EXISTS "+str(table)+str(column))

    # def insertColumn(self, table, column, value):
        # self.conn_cursor.execute("INSERT INTO "+table+column+" VALUES"+value)

    def createUserTable(self):
        self.addTable("User", "(_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, userId TEXT, notifyDate INT, timestamp TEXT)")

    def createMonthlyTable(self):
        self.addTable("Monthly", "(_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, userId TEXT, months TEXT, kwh INT, price FLOAT, timestamp TEXT)")

    def updateTable(self, table, column, value, indexName, indexValue):
        self.conn_cursor.execute("UPDATE ? SET ?=? WHERE ?=?",(table,column,value,indexName,indexValue))

    def insertMonthly(self, monthlyDic):
        self.open()
        self.conn_cursor.execute('''INSERT INTO Monthly (userId, months, kwh, price, timestamp) VALUES(?,?,?,?,?)''',(monthlyDic['userId'], monthlyDic['months'], monthlyDic['kwh'], monthlyDic['price'], monthlyDic['timestamp']))
        self.commit()
        self.close()

    def fetchMonthly(self, userId, months):
        self.open()
        self.conn_cursor.execute('''SELECT * FROM Monthly WHERE userId=? AND months=?''',(userId, months))
        userMonthly = self.conn_cursor.fetchone()
        self.commit()
        self.close()
        return userMonthly

