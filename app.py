import sys,secrets,os,threading
from datetime import datetime
from db_manager import DATABASE
from encrypt_decrypt import PASSWORD_HASH, URL_HASH
from email_manager import EMAIL_MANAGER
try:
    from flask import Flask,render_template,request,url_for,redirect,Response,jsonify
    from flask_socketio import SocketIO,send,emit
    from werkzeug import secure_filename
    import flask_login as FL
except:
    print("flask & flask_socketio must be installed")
    sys.exit(0)

class SERVER:
    onlineUsers = []
    onlineUsersDetails = {}
    def __init__(self):
        self.createFolders()
        self.secret_key = secrets.token_hex(15)
        self.image_path = 'static/user_info/user_img/'
        self.image_path_for_db = 'user_info/user_img/'
        self.default_male = 'user_info/default_img/user-male.png'
        self.default_female = 'user_info/default_img/user-female.png'
        self.restricted_symbol = ('`','~','!','#','$','%','^','&','*','(',')','-','_','=','+',
            '[','{',']','}','|',';',':',"'",'"','<',',','>','/','?')
        self.app = Flask(__name__)
        self.app.secret_key = self.secret_key
        self.app.config['MAX_CONTENT_LENGTH'] = 10*1024*1024 # 10 MB maximum
        self.app.config['MAIL_SERVER']='smtp.mail.yahoo.com'
        self.app.config['MAIL_PORT'] = 465
        self.app.config['MAIL_USERNAME'] = 'your@email.com'
        self.app.config['MAIL_PASSWORD'] = 'secret-password'
        self.app.config['MAIL_USE_TLS'] = False
        self.app.config['MAIL_USE_SSL'] = True
        self.app.config['MAIL_DEFAULT_SENDER'] = 'your@email.com'
        self.database = DATABASE()
        self.password_hash = PASSWORD_HASH()
        self.url_hash = URL_HASH()
        self.email_manager = EMAIL_MANAGER(self.app)
        self.socketio = SocketIO(self.app)
        self.login_manager = FL.LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = '/'
        self.login_manager.session_protection = 'strong'
        self.setLoginSession()
        self.setRoute()
        self.setErrorHandler()
        self.setSocketIOEvent()
        self.setJinjaFunction()

    class User(FL.UserMixin):
        def __init__(self,username):
            self.id = username
        
        @classmethod
        def get(self,usrnm,outer):
            status = outer.database.isUsernameAvail(usrnm)
            if status != 'AVAIL':
                if usrnm not in SERVER.onlineUsers:
                    SERVER.onlineUsers.append(usrnm)
                if usrnm not in SERVER.onlineUsersDetails:
                    SERVER.onlineUsersDetails[usrnm] = request.user_agent.string
                print("new",usrnm)
                return outer.User(usrnm)
            else:
                return None

    def setLoginSession(self):
        @self.login_manager.user_loader
        def load_user(username):
            status = self.database.isUsernameAvail(username)
            if status != 'AVAIL':
                return self.User.get(username,self)
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
        self.app.jinja_env.globals.update(onlineUsers=SERVER.onlineUsers)
        self.app.jinja_env.globals.update(length=self.length)

    def getYear(self):
        return datetime.now().year

    def length(self,data):
        if data:
            return len(data)-1
        else:
            return 0

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
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                print(request.environ['REMOTE_ADDR'],'RRRRRR')
            else:
                print(request.environ['HTTP_X_FORWARDED_FOR'],'XXXXXX')
            if FL.current_user.is_authenticated:
                return redirect(url_for('chat_page',usrnm=FL.current_user.get_id()))
            return render_template('index.html')

        @self.app.route('/verify/<token>')
        def email_verification(token):
            print(token)
            email = self.url_hash.getSerializedURLValue(token)
            if email and not self.database.isEmailValidated(email):
                self.database.validate_email(email)
                return "email {} verified now you can login...".format(email)
            else:
                return 'something went wrong please try again...'

        @self.app.route('/logout/')
        @FL.login_required
        def logout():
            username = FL.current_user.get_id()
            FL.logout_user()
            try:
                while username in SERVER.onlineUsers:
                    SERVER.onlineUsers.remove(username)
                while username in SERVER.onlineUsersDetails:
                    del SERVER.onlineUsersDetails[username]
                print("removed...")
            except:
                print('online user removel error:: {}'.format(username))
            print("online: ",SERVER.onlineUsers)
            id_to_remove = "#id"+username
            data = {'id':id_to_remove,'total_online':len(SERVER.onlineUsers)-1}
            self.socketio.emit('new_offline',data,namespace='/chat_page/',broadcast=True)
            return redirect(url_for('home'))

        @self.app.route('/signup_page/')
        def signup_page():
            return render_template('signup.html')

        @self.app.route('/login/',methods=['POST','GET'])
        def login():
            status = None
            if request.method == "POST":
                t_usrnm = request.form['username']
                email = self.database.getIndInfo(t_usrnm,'E')
                val_status = self.database.isEmailValidated(email)
                if val_status != None and not val_status:
                    return "firstly go and verify your email then come back..."
                status = self.database.login(request.form['username'],request.form['password'])
                if status:
                    username = request.form['username']
                    if username in SERVER.onlineUsers:
                        return render_template('alreadyLoggedin.html',device_details=SERVER.onlineUsersDetails[username])
                    user = self.User(username)
                    FL.login_user(user)
                    return redirect(url_for('chat_page',usrnm=username))
                else:
                    return render_template('index.html',error="username or password is incorrect")
            else:
                status = self.database.login(request.form['username'],request.form['password'])
                if status:
                    username = request.form['username']
                    user = self.User(username)
                    user.id = username
                    FL.login_user(user)
                    return redirect(url_for('chat_page',usrnm=username))
                else:
                    return render_template('index.html',error="username or password is incorrect")

        @self.app.route('/signup/',methods=['POST','GET'])
        def signup():
            if request.method == "POST":
                form = request.form
                thrd = threading.Thread(target=self.email_manager.send_mail,args=(form['email'],))
                thrd.start()
                pswrd_hash = self.password_hash.generate(form['pswrd1'])
                user_info = (form['fname'],form['lname'],form['gender'],form['email'],form['username'],pswrd_hash)
                for symbol in self.restricted_symbol:
                    if symbol in form['username']:
                        error = "{} symbol is not allowed in username".format(symbol)
                        return render_template('signup.html',error=error)

                self.database.saveUserInfo(user_info)
                self.database.store_without_validate(form['email'])
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
                
                return 'check your email and verify it...'

        @self.app.route('/chat_page/<usrnm>')
        @FL.login_required
        def chat_page(usrnm):
            if FL.current_user.get_id() != usrnm:
                return "permission denied..."
            return render_template('chat-page.html',username=FL.current_user.get_id())

        @self.app.route('/profile/<user>')
        @FL.login_required
        def profile(user):
            if FL.current_user.get_id() != user:
                return "permission denied..."
            return render_template('profile.html',username=user)

        @self.app.route('/profile/<user>/update/',methods=['POST'])
        @FL.fresh_login_required
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
                pswrd_hash = self.password_hash.generate(new_password)
                user_info['password'] = pswrd_hash

            self.database.updateUserInfo(user,user_info)
            return redirect(url_for('profile',user=user))

        @self.app.route('/forget_pswrd/')
        @FL.login_required
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

        @self.socketio.on('chat_connect',namespace='/chat_page/')
        @FL.login_required
        def signup_page(msg):
            element = "<a id={} style='text-align: center' href='#'\
            class='w3-animate-bottom w3-text-blue w3-bar-item w3-button'>\
            <img src='{}' class='w3-image w3-circle' width='50px'>&nbsp;{}</a>"
            user = FL.current_user.get_id()
            img_path = '/static/{}'.format(self.database.getUserImage(user))
            ele = element.format('id'+user,
                        url_for('static',filename=self.database.getUserImage(user)),user)
            data = {'element':ele,'sender':user,'total_online':len(SERVER.onlineUsers)-1}
            emit('new_online',data,broadcast=True)

        @self.socketio.on('disconnect',namespace='/chat_page/')
        @FL.login_required
        def chat_dis():
            try:
                while FL.current_user.get_id() in SERVER.onlineUsers:
                    SERVER.onlineUsers.remove(FL.current_user.get_id())
                while FL.current_user.get_id() in SERVER.onlineUsersDetails:
                    del SERVER.onlineUsersDetails[FL.current_user.get_id()]
            except:
                pass
            id_to_remove = "#id{}".format(FL.current_user.get_id())
            data = {'id':id_to_remove,'total_online':len(SERVER.onlineUsers)-1}
            emit('new_offline',data,broadcast=True)

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
