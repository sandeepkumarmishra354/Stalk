import sys
from encrypt_decrypt import PASSWORD_HASH
try:
    import sqlite3
    from sqlite3 import Error
except ImportError:
    print("sqlite module needed")
    sys.exit(0)

class DATABASE:
    def __init__(self):
        try:
            self.DB = sqlite3.connect("database/creditionals.db",check_same_thread=False)
            self.CUR = self.DB.cursor()
            self.password_hash = PASSWORD_HASH()
        except Error as e:
            print(e)
            sys.exit(0)

        self.save_login_qry = "INSERT INTO LoginInfo(userName,password) VALUES(?,?)"
        self.save_usrinfo_qry = "INSERT INTO UserInfo(firstName,lastName,gender,email,userName,password)\
        VALUES(?,?,?,?,?,?)"
        self.save_image_qry = "INSERT INTO UserImage(userName,Imgpath) VALUES(?,?)"

        script = "CREATE TABLE IF NOT EXISTS UserInfo(firstName text NOT NULL,lastName text NOT NULL,\
        gender text NOT NULL,email text NOT NULL,userName text NOT NULL,password BLOB NOT NULL);\
        CREATE TABLE IF NOT EXISTS LoginInfo(userName text NOT NULL,password BLOB NOT NULL);\
        CREATE TABLE IF NOT EXISTS UserImage(userName text NOT NULL,Imgpath text NOT NULL);\
        CREATE TABLE IF NOT EXISTS EmailValidate(email text NOT NULL,validated int NOT NULL);"
        try:
            self.CUR.executescript(script)
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)
    
    def store_without_validate(self,email):
        qry = 'INSERT INTO EmailValidate(email,validated) VALUES(?,?)'
        try:
            self.CUR.execute(qry,(email,0))
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def validate_email(self,email):
        qry = "UPDATE EmailValidate SET validated=1 WHERE email='{}'".format(email)
        try:
            self.CUR.execute(qry)
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def invalidate_email(self,email):
        qry = "UPDATE EmailValidate SET validated=0 WHERE email='{}'".format(email)
        try:
            self.CUR.execute(qry)
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def isEmailValidated(self,email):
        if email == None:
            return None
        qry = "SELECT validated FROM EmailValidate WHERE email='{}'".format(email)
        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchone()
            if len(row) <= 0:
                return False
            if row[0] == 0:
                return False
            if row[0] == 1:
                return True
        except Error as e:
            print(e)
            sys.exit(0)

    def saveLoginInfo(self,username,password):
        try:
            print("login details to save:")
            print("username: {}\npassword: {}".format(username,password))
            self.CUR.execute(self.save_login_qry, (username,password))
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def getPassword(self,username):
        qry = "SELECT * FROM LoginInfo WHERE userName='{}'".format(username)
        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            if len(row) <= 0:
                return None
            else:
                return row[0][1]
        except Error as e:
            print(e)
            sys.exit(0)

    def getIndInfo(self,username,flag):
        if flag == "F":
            qry = "SELECT {} FROM UserInfo WHERE userName='{}'".format('firstName',username)
        if flag == "L":
            qry = "SELECT {} FROM UserInfo WHERE userName='{}'".format('lastName',username)
        if flag == "E":
            qry = "SELECT {} FROM UserInfo WHERE userName='{}'".format('email',username)

        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            if len(row) <= 0:
                return None
            else:
                return row[0][0]
        except Error as e:
            print(e)
            sys.exit(0)

    def getAllUsername(self):
        qry = "SELECT userName FROM UserImage"
        try:
            userDict = []
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            for r in row:
                userDict.append(r[0])
            return userDict
        except Error as e:
            print(e)
            sys.exit(0)

    def getTotal(self):
        qry = "SELECT count(ALL) FROM LoginInfo"
        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            if len(row) <= 0:
                return 0
            else:
                return row[0][0]
        except Error as e:
            print(e)
            sys.exit(0)

    def saveUserInfo(self,user_info):
        try:
            print("userInfo to save:",user_info)
            self.CUR.execute(self.save_usrinfo_qry, user_info)
            self.saveLoginInfo(user_info[4],user_info[5])
        except Error as e:
            print(e)
            sys.exit(0)

    def saveUserImage(self,username,imgpath):
        try:
            self.CUR.execute(self.save_image_qry,(username,imgpath))
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def updateUserImage(self,username,new_img_path):
        qry = "UPDATE userImage SET Imgpath='{}' WHERE userName='{}'".format(new_img_path,username)
        try:
            self.CUR.execute(qry)
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def updateLoginPassword(self,username,password):
        qry = "UPDATE LoginInfo SET password=? WHERE userName='{}'".format(username)
        try:
            self.CUR.execute(qry,(password,))
            self.DB.commit()
        except Error as e:
            print(e)
            sys.exit(0)

    def updateUserInfo(self,username,user_info):
        qry = "UPDATE UserInfo SET {}=? WHERE userName='{}'"
        for key in user_info:
            t_qry = qry.format(key,username)
            try:
                self.CUR.execute(t_qry,(user_info[key],))
            except Error as e:
                print("in for loop")
                print(e)
                sys.exit(0)
        if len(user_info) > 0:
            self.DB.commit()
        try:
            new_ps = user_info['password']
            self.updateLoginPassword(username,new_ps)
        except:
            pass

    def getUserImage(self,username):
        qry = "SELECT * FROM UserImage WHERE userName='{}'".format(username)
        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            if len(row) <= 0:
                print('image get error')
                sys.exit(0)
            else:
                return row[0][1]
        except Error as e:
            print(e)
            sys.exit(0)

    def login(self,username, password):
        qry = "SELECT * FROM LoginInfo WHERE userName='{}'".format(username)
        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            if len(row) > 0:
                return self.password_hash.check(row[0][1],password)
        except Error as e:
            print(e)
            return False

    def isUsernameAvail(self,username):
        qry = "SELECT * FROM LoginInfo WHERE userName='{}'".format(username)
        try:
            self.CUR.execute(qry)
            row = self.CUR.fetchall()
            if len(row) <= 0:
                return "AVAIL"
            else:
                return "NOT AVAIL"
        except Error as e:
            print(e)
            sys.exit(0)

    def __del__(self):
        self.DB.commit()