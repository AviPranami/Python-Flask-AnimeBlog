from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug import secure_filename
from datetime import datetime
import json
import os
import math

with open('config.json') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(15), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12))
    email = db.Column(db.String(50), nullable=False)

class Posts(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    image_name = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(12))

@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')

    if(not str(page).isnumeric()):
        page = 1
    page = int(page)

    posts = posts[(page-1)*int(params['no_of_posts']):((page-1)*int(params['no_of_posts'])+ int(params['no_of_posts']))]
    if (page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif (page == last):
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/dashboard', methods = ["GET","POST"])
def dashboard():
    if ('user' in session and session['user'] == params['admin-user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == "POST":
        # redirect to admin panel
        username = request.form.get('uname')
        userpass = request.form.get('upass')

        if (username == params['admin-user'] and userpass == params['admin-password']):
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)

@app.route('/edit/<string:sr_no>', methods = ["GET","POST"])
def edit(sr_no):
    if ('user' in session and session['user'] == params['admin-user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image_name = request.form.get('image_name')
            date = datetime.now()

            if sr_no == '0':
                post = Posts(title=box_title, slug=slug, tagline=tagline, content=content, image_name=image_name, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sr_no=sr_no).first()
                post.title = box_title
                post.tagline = tagline
                post.slug = slug
                post.content = content
                post.image_name = image_name
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sr_no)
        post = Posts.query.filter_by(sr_no=sr_no).first()
        return render_template('edit.html', params=params, sr_no=sr_no, post=post)

@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin-user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded sucessfully!!"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/delete/<string:sr_no>', methods = ["GET","POST"])
def delete(sr_no):
    if ('user' in session and session['user'] == params['admin-user']):
        post = Posts.query.filter_by(sr_no=sr_no).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')


@app.route('/post/<string:post_slug>', methods = ["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route('/contact', methods=["GET","POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(),email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message from ' + name,
                            sender = email ,
                            recipients = [params['gmail-user']],
                            body = message + '\n' + phone

        )

    return render_template('contact.html', params=params)

if __name__ == '__main__':
    app.run(debug=True)