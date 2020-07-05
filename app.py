from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import os
import json
import random
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "tianjin"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://test:123456@47.105.166.136/yufan?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
loginmanager = LoginManager(app)
loginmanager.session_protection = "strong"
loginmanager.login_view = "login"

db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    meta = {
        "collection": "user",  # 表名
        "ordering": ["-id"],  # id是正序还是倒序
        "strict": True  # 自动修改表内容
    }
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    username = db.Column(db.String(18), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(18), nullable=False)
    floder = db.Column(db.String(80), nullable=False)

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash,password)

# db.create_all()
basedir = os.path.abspath(os.path.dirname(__file__))
download_floder = os.path.join(basedir, "upload")
print(download_floder)


def url_list(filename):
    return "<li><a href='{}'>{}</a><input style='float:right' type='button' id='{}' value='删除' onclick='delete_file(event)'></li>".format("/download/"+filename, filename, filename)


@loginmanager.user_loader
def get_user(user_id):
    return User.query.filter_by(id=user_id).first()


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        err_msg = {
            "result": "NO"
        }
        param = json.loads(request.data.decode("utf-8"))
        username = param.get("username", "")
        password = param.get("password", "")
        nickname = param.get("nickname", "")
        print(username,password,nickname)
        if not username:
            err_msg["msg"] = "缺少用户名"
            return jsonify(err_msg)
        if not password:
            err_msg["msg"] = "缺少密码"
            return jsonify(err_msg)
        if not nickname:
            err_msg["msg"] = "缺少昵称"
            return jsonify(err_msg)
        user = User.query.filter_by(username=username).first()
        print(user)
        if not user:
            random_floder = random.randint(0, 10000)
            while random_floder in os.listdir(download_floder):
                random_floder = random.randint(0, 10000)
            user = User(username=username, nickname=nickname,
                        floder=str(random_floder))
            user.hash_password(password)
            os.mkdir(os.path.join(download_floder, user.floder))
            db.session.add(user)
            db.session.commit()
            db.session.close()
            return jsonify({
                "result": "OK"
            })
        else:
            err_msg["msg"] = "用户已经注册"
            return jsonify(err_msg)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        err_msg = {
            "result": "NO"
        }
        param = json.loads(request.data.decode("utf-8"))
        username = param.get("username", "")
        password = param.get("password", "")
        if not username:
            err_msg["msg"] = "缺少用户名"
            return jsonify(err_msg)
        if not password:
            err_msg["msg"] = "缺少密码"
            return jsonify(err_msg)
        user = User.query.filter_by(username=username).first()
        if not user:
            err_msg["msg"] = "用户尚未注册"
            return jsonify(err_msg)
        if not user.verify_password(password):
            err_msg["msg"] = "密码错误"
            return jsonify(err_msg)
        login_user(user)
        return jsonify({
            "result": "OK",
            "next_url": "/"
        })


@app.route("/upload", methods=["POST","GET"])
@login_required
def upload():
    f = request.files["file"]
    if not os.path.exists(os.path.join(download_floder, current_user.floder)):
        os.mkdir(os.path.join(download_floder, current_user.floder))
    f.save(os.path.join(download_floder, current_user.floder, f.filename))
    print(os.path.join(download_floder, current_user.floder, f.filename))
    return "上传成功"


@app.route("/get_list", methods=["GET"])
@login_required
def get_list():
    if not os.path.exists(os.path.join(download_floder, current_user.floder)):
        os.mkdir(os.path.join(download_floder, current_user.floder))
    file_list = os.listdir(os.path.join(download_floder, current_user.floder))
    return jsonify(list(map(url_list, file_list)))


@app.route("/download/<string:filename>")
@login_required
def download(filename):
    if os.path.isfile(os.path.join(download_floder, current_user.floder, filename)):
        return send_from_directory(os.path.join(download_floder, current_user.floder), filename, as_attachment=True)


@app.route("/delete/<string:filename>")
@login_required
def delete_file(filename):
    if os.path.isfile(os.path.join(download_floder, current_user.floder, filename)):
        os.remove(os.path.join(download_floder, current_user.floder, filename))
        return jsonify({
            "result": "OK"
        })
    else:
        return jsonify({
            "result": "NO",
            "msg": "文件不存在"
        })


if __name__ == "__main__":
    if not os.path.exists(download_floder):
        os.makedirs(download_floder)
    app.run()
