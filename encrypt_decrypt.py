import sys,secrets
try:
    import flask_bcrypt as FLASK_B
    import itsdangerous as ITS_D
except:
    print('encrypt_decrypt import error...')
    sys.exit(0)

class PASSWORD_HASH:
    def __init__(self):
        pass
    def generate(self,password):
        try:
            return FLASK_B.generate_password_hash(password)
        except:
            print("password hash generate error")
            sys.exit(0)
    def check(self,hash_value,password):
        try:
            return FLASK_B.check_password_hash(hash_value,password)
        except:
            print('password hash check error')
            return False
        
class URL_HASH:
    def __init__(self):
        self.secret_key = '1sandeep'
        self.v_salt = 'email-verification'
        self.urls1 = ITS_D.URLSafeSerializer(self.secret_key, salt=self.v_salt)
    def getSerializedURL(self,email):
        try:
            return self.urls1.dumps(email)
        except:
            print('getSerialized error')
            sys.exit(0)
    def getSerializedURLValue(self,s_url):
        try:
            return self.urls1.loads(s_url)
        except:
            return None