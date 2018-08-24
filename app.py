import sys,secrets,os
from datetime import datetime
from db_manager import DATABASE
#from email_manager import SEND_MAIL
try:
    from flask import Flask,render_template,request,url_for,redirect,Response
    from flask_socketio import SocketIO,send,emit
    from werkzeug import secure_filename
    import flask_login as FL
    #from flask_session import Session
except ImportError:
    print("flask & flask_socketio must be installed")
    sys.exit(0)

class SERVER:

    def __init__(self):
        #self.outer_instance = self
        self.createFolders()
        self.secret_key = secrets.token_hex(15)
        self.image_path = 'static/user_info/user_img/'
        self.image_path_for_db = 'user_info/user_img/'
        self.default_male = 'user_info/default_img/user-male.png'
        self.default_female = 'user_info/default_img/user-female.png'
        self.serverCert = 'ssl/cert.pem'
        self.serverKey = 'ssl/key.pem'
        self.restricted_symbol = ('`','~','!','#','$','%','^','&','*','(',')','-','_','=','+',
            '[','{',']','}','|',';',':',"'",'"','<',',','>','/','?')
        self.ssl_cert = (self.serverCert,self.serverKey)
        self.database = DATABASE()
        self.app = Flask(__name__)
        self.app.secret_key = self.secret_key
        self.app.config['MAX_CONTENT_LENGTH'] = 5*1024*1024 # 5 MB maximum
        #self.app.config['SESSION_TYPE'] = 'filesystem'
        #self.app.config['SECRET_KEY'] = self.secret_key
        #Session(self.app)
        self.socketio = SocketIO(self.app)
        self.login_manager = FL.LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = '/'
        self.setLoginSession()
        self.setRoute()
        self.setErrorHandler()
        self.setSocketIOEvent()
        self.setJinjaFunction()

    class User(FL.UserMixin):
        def __init__(self,username,password):
            self.id = username
            self.password = password
            self.db = DATABASE()
        
        @classmethod
        def get(self,usrnm,pswrd,outer):
            status = outer.database.login(usrnm,pswrd)
            if not status:
                return None
            else:
                return outer.User(usrnm,pswrd)

    def setLoginSession(self):
        @self.login_manager.user_loader
        def load_user(username):
            password = self.database.getPassword(username)
            if password:
                return self.User.get(username,password,self)
            else:
                return None

    def createFolders(self):
        os.makedirs('database',exist_ok=True)
        os.makedirs('static/user_info/user_img',exist_ok=True)

    def setJinjaFunction(self):
        self.app.jinja_env.globals.update(getYear=self.getYear)
        self.app.jinja_env.globals.update(getAllUsername=self.database.getAllUsername)
        self.app.jinja_env.globals.update(getTotal=self.database.getTotal)
        self.app.jinja_env.globals.update(getUserImage=self.database.getUserImage)
        self.app.jinja_env.globals.update(getIndInfo=self.database.getIndInfo)

    def getYear(self):
        return datetime.now().year

    def start_server(self):
        self.app.debug = True
        self.socketio.run(self.app,host='0.0.0.0',port=80)
    
    def saveUserData(self,form):
        user_info = (form['fname'],form['lname'],form['gender'],form['email'],form['username'],form['pswrd1'])
        self.database.saveUserInfo(user_info)

    def setErrorHandler(self):
        @self.app.errorhandler(404)
        def notFound_404(e_code):
            return render_template('404.html'),404

    def setRoute(self):
        @self.app.route('/<route>',defaults={'route':'home'})
        def home_page(route):
            if route == 'home':
                if FL.current_user.is_authenticated:
                    return redirect(url_for('chat_page',usrnm=FL.current_user.get_id()))
                return render_template('index.html')
            else:
                if FL.current_user.is_authenticated:
                    return redirect(url_for('chat_page',usrnm=FL.current_user.get_id()))
                return render_template('index.html')
            
        @self.app.route('/')
        def home():
            if FL.current_user.is_authenticated:
                return redirect(url_for('chat_page',usrnm=FL.current_user.get_id()))
            return render_template('index.html')

        @self.app.route('/logout/')
        def logout():
            FL.logout_user()
            return redirect(url_for('home'))

        @self.app.route('/signup_page/')
        def signup_page():
            return render_template('signup.html')

        @self.app.route('/login/',methods=['POST','GET'])
        def login():
            status = None
            if request.method == "POST":
                status = self.database.login(request.form['username'],request.form['password'])
                if status:
                    username = request.form['username']
                    user = self.User(username,request.form['password'])
                    user.id = username
                    FL.login_user(user)
                    return redirect(url_for('chat_page',usrnm=username))
                else:
                    return render_template('index.html',error="username or password is incorrect")
            else:
                status = self.database.login(request.form['username'],request.form['password'])
                if status:
                    username = request.form['username']
                    user = self.User(username,request.form['password'])
                    user.id = username
                    FL.login_user(user)
                    return redirect(url_for('chat_page',usrnm=username))
                else:
                    return render_template('index.html',error="username or password is incorrect")

        @self.app.route('/signup/',methods=['POST','GET'])
        def signup():
            if request.method == "POST":
                form = request.form
                user_info = (form['fname'],form['lname'],form['gender'],form['email'],form['username'],form['pswrd1'])
                for symbol in self.restricted_symbol:
                    if symbol in form['username']:
                        error = "{} symbol is not allowed in username".format(symbol)
                        return render_template('signup.html',error=error)

                self.database.saveUserInfo(user_info)
                try:
                    f = request.files['user_img']
                    original_name = secure_filename(f.filename)
                    tmp = original_name.split('.')
                    extension = tmp[len(tmp)-1]
                    extension = '.'+extension
                    filename = form['username']+extension
                    tmp_file = self.image_path_for_db+filename
                    filename = self.image_path + filename
                    f.save(filename)
                    self.database.saveUserImage(form['username'],tmp_file)
                except:
                    if form['gender'] == 'male':
                        self.database.saveUserImage(form['username'],self.default_male)
                    else:
                        self.database.saveUserImage(form['username'],self.default_female)
                
                username = request.form['username']
                user = self.User(username,request.form['pswrd1'])
                user.id = username
                FL.login_user(user)
                return redirect(url_for('chat_page',usrnm=username))

        @self.app.route('/chat_page/<usrnm>')
        @FL.login_required
        def chat_page(usrnm):
            if FL.current_user.get_id() != usrnm:
                return "permission denied..."
            #userimg = self.database.getUserImage(usrnm)
            return render_template('chat-page.html',username=usrnm)

        @self.app.route('/profile/<user>')
        @FL.login_required
        def profile(user):
            if FL.current_user.get_id() != user:
                return "permission denied..."
            return render_template('profile.html',username=user)

        @self.app.route('/profile/<user>/update/',methods=['POST'])
        @FL.login_required
        def update(user):
            if FL.current_user.get_id() != user:
                return 'permission denied...'
            form = request.form
            fname = form['fname']
            lname = form['lname']
            email = form['email']
            new_password = form['pswrd']
            try:
                img_file = form['new_img']
            except KeyError:
                img_file = "not empty"
            if len(new_password) < 6 and len(new_password) != 0:
                return render_template('profile.html',username=FL.current_user.get_id(),error="password must be 6 digit long")
            user_info = {}
            if len(img_file) != 0:
                f = request.files['new_img']
                original_name = secure_filename(f.filename)
                tmp = original_name.split('.')
                extension = tmp[len(tmp)-1]
                extension = '.'+extension
                filename = user+extension
                tmp_file = self.image_path_for_db+filename
                filename = self.image_path + filename
                f.save(filename)
                self.database.updateUserImage(user,tmp_file)

            f_data = len(fname)+len(lname)+len(email)+len(new_password)+len(img_file)
            if f_data == 0:
                return redirect(url_for('profile',user=user))

            if fname:
                user_info['firstName'] = fname
            if lname:
                user_info['lastName'] = lname
            if email:
                user_info['email'] = email
            if new_password:
                user_info['password'] = new_password

            self.database.updateUserInfo(user,user_info)
            return redirect(url_for('profile',user=user))

        @self.app.route('/forget_pswrd/')
        def forget_pswrd():
            return "forget password"

        @self.app.route('/check_username',methods=['POST','GET'])
        def check_username():
            if request.method == "POST":
                return self.database.isUsernameAvail(request.form['username'])
            if request.method == "GET":
                return self.database.isUsernameAvail(request.form['username'])

    def setSocketIOEvent(self):
        @self.socketio.on('connect')
        def connect():
            print("new connect")

        @self.socketio.on('signup',namespace='/signup_page/')
        def signup_page(msg):
            print(msg)

        @self.socketio.on('disconnect')
        def disconnect():
            print("disconnect")
        @self.socketio.on('message')
        def unnamed_event_msg(msg):
            print("unnamed event_msg: "+msg)
            return msg
        @self.socketio.on('json')
        def unnamed_event_msg(json):
            print("unnamed event_json: ",json)

def Main():
    server = SERVER()
    server.start_server()

if __name__ == "__main__":
    Main()
