# main.py
from flask import Flask, redirect, render_template
from flask import request, make_response, g
from flask_sqlalchemy import SQLAlchemy
import hashlib,string,random,datetime
from flask_socketio import SocketIO

print("Server ready")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:1111@127.0.0.1/mysql" # change to your database URI
db = SQLAlchemy(app)
socketio = SocketIO(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login_name = db.Column(db.String(20), nullable=False, unique=True, server_default=db.FetchedValue())
    login_pwd = db.Column(db.String(32), nullable=False, server_default=db.FetchedValue())
    login_salt = db.Column(db.String(32), nullable=False, server_default=db.FetchedValue())
    # the salt is a random code used to encrypt cookie info

class Vlog(db.Model):
    __tablename__ = 'vlogs'

    id = db.Column(db.Integer, primary_key=True)
    vlog_id = db.Column(db.String(20), nullable=False, unique=True, server_default=db.FetchedValue())
    title = db.Column(db.String(32), nullable=False, server_default=db.FetchedValue())
    profile = db.Column(db.String(128), nullable=False, server_default=db.FetchedValue())
    like_counts = db.Column(db.Integer)
    comment_counts = db.Column(db.Integer)

class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(20), nullable=False, server_default=db.FetchedValue())
    vlog_id = db.Column(db.String(20), nullable=False, server_default=db.FetchedValue())

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(20), nullable=False, server_default=db.FetchedValue())
    vlog_id = db.Column(db.String(20), nullable=False, server_default=db.FetchedValue())
    content = db.Column(db.String(128), nullable=False, server_default=db.FetchedValue())
    created_time = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())

# Uncomment the code below to initialize the tables and records in the database
# db.create_all()   # create all tables
# for i in range(10): # initialize the info for the test videos
#     model_vlog = Vlog()
#     model_vlog.vlog_id = str(i)
#     model_vlog.title = "title text"+str(i)
#     model_vlog.profile = "profile text"+str(i)
#     model_vlog.like_counts = 0
#     model_vlog.comment_counts = 0
#     db.session.add(model_vlog)
#     db.session.commit()

@app.route('/video/<v_id>', methods=['GET'])
def show(v_id):
    """ show webpage that displays video with specific id"""

    user_info = check_login() # check which user is logged in.

    if 'total_vlog_count' not in g:
        g.total_vlog_count=len(Vlog.query.all()) # store the total count of vlogs into global variables

    history = Comment.query.filter_by(vlog_id=v_id) # getting comment history
    vlog_info = Vlog.query.filter_by(vlog_id=v_id).first()

    results = [] # storing comments to the list

    for i in history:
        results.append({"id":i.id,"name":i.user_name,"content":i.content,"time":i.created_time.strftime("%Y-%m-%d %H:%M:%S")})

    results.reverse() # newest comment to the top

    if user_info: # if there is a logged-in user
        like_info = Like.query.filter_by(user_name=user_info.login_name,vlog_id=v_id).first()
        if like_info:
            return render_template("video.html",
                                   total_vlog_count=g.total_vlog_count,
                                   title=vlog_info.title,
                                   profile=vlog_info.profile,
                                   comment_list=results,
                                   like=1,
                                   current_user=user_info.login_name,
                                   video_id=v_id,
                                   like_counts=vlog_info.like_counts,
                                   comment_counts=vlog_info.comment_counts)
        else:
            return render_template("video.html",
                                   total_vlog_count=g.total_vlog_count,
                                   title=vlog_info.title,
                                   profile=vlog_info.profile,
                                   comment_list=results,
                                   current_user=user_info.login_name,
                                   video_id=v_id,
                                   like_counts=vlog_info.like_counts,
                                   comment_counts=vlog_info.comment_counts)
    else: # visit site as guest
        return render_template("video.html",
                               total_vlog_count=g.total_vlog_count,
                               title=vlog_info.title,
                               profile=vlog_info.profile,
                               comment_list=results,
                               video_id=v_id,
                               like_counts=vlog_info.like_counts,
                               comment_counts=vlog_info.comment_counts)

@app.route('/login', methods=['GET',"POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")

    req = request.values
    login_name = req['login_name'] if 'login_name' in req else ''
    login_pwd = req['login_pwd'] if 'login_pwd' in req else ''

    user_info = User.query.filter_by( login_name = login_name ).first()

    if not user_info:
        return {"msg":"Username has not been registered.","code":-1}

    if user_info.login_pwd != login_pwd:
        return {"msg":"Please enter the correct password.","code":-1}

    user_info.login_salt = "".join([ random.choice( (string.ascii_letters + string.digits ) ) for i in range(8) ])
    # the salt is a random code used to encrypt cookie info, updated every time logged in to prevent the old cookie to be used for "log in"
    db.session.commit()

    m = hashlib.md5() # encrypt login password
    str = "%s-%s" % (user_info.login_pwd,user_info.login_salt)
    m.update(str.encode("utf-8"))

    if 'total_vlog_count' not in g:
        g.total_vlog_count = len(Vlog.query.all())

    response = make_response( {"msg":"Login successfully","total":g.total_vlog_count,"code":200} )
    response.set_cookie("TukTok",
                        "%s#%s"%(user_info.id,m.hexdigest()),60 * 60 *24 * 7 )
    return response

@app.route("/logout")
def logOut():
    cookies = request.cookies
    cookie_name = "TukTok"
    auth_cookie = cookies[cookie_name] if cookie_name in cookies else None

    auth_info = auth_cookie.split("#")
    user_info = User.query.filter_by(id=auth_info[0]).first()
    user_info.login_salt = "".join([ random.choice( (string.ascii_letters + string.digits ) ) for i in range(8) ])
    # update salt info to prevent the old cookie to be used for "log in"
    db.session.commit()

    response = make_response( redirect( "/login" ) )
    response.delete_cookie( "TukTok" )

    return response

@app.route('/reg', methods=['GET',"POST"])
def reg():
    if request.method=="GET":
        return render_template("Reg.html")

    req = request.values
    login_name = req['login_name'] if "login_name" in req else ""
    login_pwd = req['login_pwd'] if "login_pwd" in req else ""

    user_info = User.query.filter_by(login_name=login_name).first()
    if user_info:
        return {"msg":"This user name has already been registered, please use another one.","code":-1}

    # create new user and store in the database
    model_user = User()
    model_user.login_name = login_name
    model_user.login_pwd = login_pwd
    model_user.login_salt = "".join([ random.choice( (string.ascii_letters + string.digits ) ) for i in range(8) ])
    db.session.add(model_user)
    db.session.commit()

    return {"msg":"Registered successfully.","code":200}

# comment and like updates need to be sent to all users in real-time, use socketio to broadcast
@socketio.on('comment_update')
def comment_update(req):
    """ for new comment to be added and to show on the screen """
    user_name = req['u_name'] if "u_name" in req else ""
    vlog_id = req['v_id'] if "v_id" in req else ""
    comment_val = req['c_content'] if "c_content" in req else ""

    # create new comment and store in the database
    model_comment = Comment()
    model_comment.user_name = user_name
    model_comment.vlog_id = vlog_id
    model_comment.content = comment_val
    model_comment.created_time = datetime.datetime.now()
    db.session.add(model_comment)
    db.session.commit()

    # add comment count to vlog
    vlog_info = Vlog.query.filter_by(vlog_id=vlog_id).first()
    vlog_info.comment_counts += 1
    db.session.commit()

    comment_info = Comment.query.filter_by(user_name=user_name, vlog_id=vlog_id).order_by(
        Comment.created_time.desc()).first() # get the comment that the user applied to the video just now

    reply={"msg": "Comment sent successfully!",
     "update": {"id": comment_info.id,
                "vlog_id":comment_info.vlog_id,
                "user": comment_info.user_name,
                "comment": comment_info.content,
                "comment_counts": vlog_info.comment_counts,
                "time": comment_info.created_time.strftime("%Y-%m-%d %H:%M:%S")}}

    socketio.emit('comment_update', reply) # broadcast the update to all

@socketio.on('comment_delete')
def comment_delete(req):
    """ for comment to be deleted and to disappear on the screen """
    comment_id = req['comment_id'] if "comment_id" in req else ""

    # delete comment in the database
    comment_info = Comment.query.filter_by(id=comment_id).first()
    db.session.delete(comment_info)
    db.session.commit()

    # update comment count to vlog
    vlog_info = Vlog.query.filter_by(vlog_id=comment_info.vlog_id).first()
    vlog_info.comment_counts -= 1
    db.session.commit()

    # broadcast the update to all
    socketio.emit('comment_delete', {"cmt_id":comment_id,"vlog_id":comment_info.vlog_id, "msg": "Comment delete successfully!", "code": 200})

@socketio.on('like_update')
def like_update(req):
    """ for like to be saved and to show on the screen """
    user_name = req['u_name'] if "u_name" in req else ""
    vlog_id = req['v_id'] if "v_id" in req else ""
    like_val= req['like_val'] if "like_val" in req else ""

    if like_val=='1': # add likes
        # create like record in the database
        model_like = Like()
        model_like.user_name = user_name
        model_like.vlog_id = vlog_id
        db.session.add(model_like)
        db.session.commit()

        # add like count to vlog
        vlog_info = Vlog.query.filter_by(vlog_id=vlog_id).first()
        vlog_info.like_counts += 1
        db.session.commit()

        # broadcast the update to all
        socketio.emit('like_update', {"msg": "Liked.","user":user_name, "vlog_id":vlog_info.vlog_id, "like_counts":vlog_info.like_counts})

    else: # cancel likes
        # find delete like record in the database
        like_info = Like.query.filter_by(user_name=user_name,vlog_id=vlog_id).first()
        db.session.delete(like_info)
        db.session.commit()

        # update like count to vlog
        vlog_info = Vlog.query.filter_by(vlog_id=vlog_id).first()
        vlog_info.like_counts -= 1
        db.session.commit()

        # broadcast the update to all
        socketio.emit('like_update', {"msg": "Unliked.", "user":user_name, "vlog_id":vlog_info.vlog_id, "like_counts": vlog_info.like_counts})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

def check_login():
    """ check cookies for the login info"""
    cookies = request.cookies
    cookie_name = "TukTok"
    auth_cookie = cookies[cookie_name] if cookie_name in cookies else None
    if auth_cookie is None:
        return False

    auth_info = auth_cookie.split("#") # cookie format: id#encryted_user_info
    if len(auth_info) != 2:
        return False

    try:
        user_info = User.query.filter_by(id=auth_info[0]).first()
    except Exception:
        return False

    if user_info is None:
        return False

    m = hashlib.md5()
    str = "%s-%s" % (user_info.login_pwd,user_info.login_salt)
    m.update(str.encode("utf-8"))

    # check if cookie info matched with saved user info
    if auth_info[1] != m.hexdigest():
        return False

    return user_info