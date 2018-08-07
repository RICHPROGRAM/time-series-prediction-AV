from flask import Flask, render_template, flash, request, session, url_for, Markup, redirect, send_from_directory, json
from werkzeug.utils import secure_filename
import os
import razorpay
import random

from flask_login import login_user
from flask_sqlalchemy import SQLAlchemy
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/upwork'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'qwertyuioplkjhgfdsazxcvbnm'

db = SQLAlchemy(app)


class Users(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    ngo = db.Column(db.String(100))
    slug = db.Column(db.String(100))
    contact = db.Column(db.String(15))

class Team(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    ngo = db.Column(db.String(100))
    photo = db.Column(db.String(100))
    name = db.Column(db.String(100))
    text = db.Column(db.String(1000))

class Action(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    ngo = db.Column(db.String(100))
    image = db.Column(db.String(100))
    headline = db.Column(db.String(100))
    text = db.Column(db.String(1000))

class User_event(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    ngo = db.Column(db.String(100))
    image = db.Column(db.String(100))
    headline = db.Column(db.String(100))
    text = db.Column(db.String(1000))
    verified = db.Column(db.String(10))

class Masterdb(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    logo = db.Column(db.String(100))
    image1 = db.Column(db.String(100))
    image2 = db.Column(db.String(100))
    ngo = db.Column(db.String(100))
    slug = db.Column(db.String(100))
    main_title = db.Column(db.String(100))
    main_text = db.Column(db.String(1000))
    sub_title = db.Column(db.String(100))
    sub_text = db.Column(db.String(1000))
    contact = db.Column(db.String(1000))
    address = db.Column(db.String(100))
    email = db.Column(db.String(100))
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(100))
    account_num = db.Column(db.String(20))
    bank_name = db.Column(db.String(100))
    branch = db.Column(db.String(100))
    ifsc_code = db.Column(db.String(20))
    upi = db.Column(db.String(100))

class Volunteer(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    ngo = db.Column(db.String(100))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    mobile = db.Column(db.String(100))

# do easy_install razorpay or
#    pip install razorpay

client = razorpay.Client(auth=("rzp_test_hkRpWpxuYIk9AO", "welLolgjWvehdXJ2YWCvBO4o"))

resp = client.payment.fetch_all()


def send_confirmation_code(to_number):
    verification_code = generate_code()
    print(verification_code)
    send_sms(to_number, verification_code)
    session['verification_code'] = verification_code
    return verification_code

def generate_code():
    return str(random.randrange(100000, 999999))

def send_sms(mob, msg):

    import http.client, urllib
    conn = http.client.HTTPConnection("api.msg91.com")
    msg = urllib.parse.quote( msg)

    conn.request("GET",
                 "/api/sendhttp.php?sender=ONENGO&route=4&mobiles=" + mob + "&authkey=224766AEtRuPUQC5JQ5b40a400&country=91&message=Your%201NGO%20OTP%20is%20"+msg)

    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

@app.route('/charge', methods=['POST'])
def app_charge():
    amount = 5100
    payment_id = request.form['razorpay_payment_id']
    client.payment.capture(payment_id, amount)
    return json.dumps(client.payment.fetch(payment_id))


@app.route("/edit_mode/<string:slug>", methods=['GET', 'POST'])
def edit_mode(slug):
    user = Users.query.filter_by(slug=slug).first()
    data = Masterdb.query.filter_by(slug=slug).first()
    db.session.query(User_event).delete()
    db.session.commit()
    filename = ""
    if request.method == 'POST':
        try:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = request.form.get('image')
        except Exception as e:
            print("Form without file " + str(e))

        ngo_name = data.ngo
        image = str(filename)
        print(image)
        headline = str(request.form.get('headline'))
        text = str(request.form.get('text'))
        posts = User_event(ngo=ngo_name, image=image, headline=headline, text=text, verified ='0')
        db.session.add(posts)
        db.session.commit()
        send_confirmation_code(user.contact)
        session['user_email'] = user.email
        print(session['user_email'])
        session['process'] = 'add_event'
        information = "The OTP has been sent to your registered mobile number!"
        return redirect(url_for('confirmation', slug=user.slug, information=information))
    post = Masterdb.query.filter_by(slug=slug).first()
    act = Action.query.filter_by(ngo=post.ngo).all()
    return render_template("edit_mode.html", act=act, post=post, slug=slug)


@app.route('/confirmation', methods=['GET', 'POST'])
def confirmation():
    print(session['verification_code'])
    information = request.args.get('information')
    if request.method == 'POST':
        xyz = request.form.get('verification_code')
        if xyz == session['verification_code']:
            session['logged_in'] = True
            print(session['process'])
            user = Users.query.filter_by(email=session['user_email']).first()
            if session['process'] == 'add_event':
               data = User_event.query.filter_by(verified ='0').first()
               print(data)
               posts = Action(ngo=data.ngo, image=data.image, headline=data.headline, text=data.text )
               db.session.add(posts)
               db.session.commit()
               return redirect(url_for('.website', post_slug=user.slug))
            else:
                if session['process'] == 'login':
                    post = Masterdb.query.filter_by(slug=user.slug).first()
                    if (post is None):
                        return redirect(url_for('.edit_test', sno='0', slug_data=user.slug, ngo_data=user.ngo))
                    else:
                        return redirect(url_for('.edit_test', sno=post.sno))
        else:
            error = "Wrong code. Please try again."
            return render_template('otp_login.html', error=error)
    return render_template('otp_login.html', information=information)

@app.route('/resend_otp', methods=['GET', 'POST'])
def resend_otp():
    user = Users.query.filter_by(email=session['user_email']).first()
    print(user)
    send_confirmation_code(user.contact)
    information =" The OTP has been resent on the registered mobile number"
    return redirect(url_for('.confirmation', information=information))


@app.route("/profile/<string:slug>", methods=['GET', 'POST'])
def profile(slug):
    slug = slug
    post = Masterdb.query.filter_by(slug=slug).first()
    if session['username'] == 'Potnis':
        print(session['username'])
        if request.method == 'POST':
            post = Users.query.filter_by(slug=slug).first()
            post.contact = request.form.get('contact')
            post.email = request.form.get('email')
            post.password = request.form.get('password')
            db.session.commit()

        user = Users.query.filter_by(slug=slug).first()
        num = Masterdb.query.filter_by(slug=slug).first().sno
        return render_template("profile.html", user=user, num=num)
    else:
        return redirect(url_for('.edit_test', sno=post.sno))

UPLOAD_FOLDER = 'static/image'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4' ''])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def volunteer(var_ngo):

    if request.method == 'POST':
        req_name = request.form.get('name')
        req_email = request.form.get('email')
        req_mobile = request.form.get('mobile')

    post = Volunteer(ngo=var_ngo, name=req_name, email=req_email, mobile=req_mobile)
    db.session.add(post)
    db.session.commit()
    success = True
    return (success)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        ngo_name = request.form.get('ngo')
        ngo_slug = request.form.get('slug')
        email = request.form.get('email')
        contact = request.form.get('contact')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        check_ngo = Users.query.filter_by(ngo = ngo_name).first()
        check_slug = Users.query.filter_by(slug = ngo_slug).first()
        check_email = Users.query.filter_by(email = email).first()

        if (password == confirm_password) and check_email is None and check_ngo is None:
           post = Users(slug=ngo_slug, ngo =ngo_name, email= email, password= password, contact=contact)
           db.session.add(post)
           db.session.commit()
           session['logged_in'] = True
           return redirect(url_for('.edit_test', sno='0', slug_data = post.slug, ngo_data = post.ngo))
        else:
           error = "Password does not match the confirm password or the NGO/email has already been registered"
           return render_template('signup.html', error = error)
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        registered_user = Users.query.filter_by(email=email, password=password).first()
        if registered_user is None:
           print('none')
           error ='Username or Password is invalid'
           return render_template('signin.html', error = error)
        else:
          session['logged_in'] = True
          print('logged_in')
          session['process'] = 'login'
          send_confirmation_code(registered_user.contact)
          session['user_email'] = registered_user.email
          print(session['user_email'])
          information = "The OTP has been sent to your registered mobile number!"
          return redirect(url_for('confirmation', slug=registered_user.slug, information=information))
    return render_template('signin.html')


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit_test(sno):
        slug_data = request.args.get('slug_data')
        ngo_data = request.args.get('ngo_data')

        if session.get('logged_in') == True:

            if request.method == 'POST':
                try:
                  file = request.files['logo_file']
                  if file.filename == '':
                    logo_image = request.form.get('logo')
                  if file and allowed_file(file.filename):
                    logo_image = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_image))
                  else:
                    logo_image = request.form.get('logo')
                except Exception as e:
                       print("Form without file " + str(e))

                try:
                  file = request.files['image1_file']
                  if file.filename == '':
                    image1_img = request.form.get('image1')
                  if file and allowed_file(file.filename):
                    image1_img = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image1_img))
                  else:
                    image1_img = request.form.get('image1')
                except Exception as e:
                       print("Form without file " + str(e))

                try:
                  file = request.files['image2_file']
                  if file.filename == '':
                    image2_img = request.form.get('image2')
                  if file and allowed_file(file.filename):
                    image2_img = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image2_img))
                  else:
                    image2_img = request.form.get('image2')
                except Exception as e:
                       print("Form without file " + str(e))


                req_ngo = ngo_data
                req_slug = slug_data
                req_logo = str(logo_image)
                req_image1 = str(image1_img)
                req_image2 = str(image2_img)
                req_main_title = request.form.get('main_title')
                req_main_text = request.form.get('main_text')
                req_sub_title = request.form.get('sub_title')
                req_sub_text = request.form.get('sub_text')
                req_address = request.form.get('address')
                req_contact = request.form.get('contact')
                req_email = request.form.get('email')
                req_bank_name = request.form.get('bank_name')
                req_branch = request.form.get('branch')
                req_account_num = request.form.get('account_num')
                req_ifsc_code = request.form.get('ifsc_code')
                req_upi = request.form.get('upi')
                req_cb = request.form.get('checkbox')

                if sno == '0':
                    post = Masterdb(ngo=req_ngo, slug=req_slug, logo=req_logo, image1=req_image1, image2=req_image2,
                                    main_title=req_main_title, main_text=req_main_text,
                                    sub_title=req_sub_title, sub_text=req_sub_text, address=req_address,
                                    contact=req_contact, email=req_email, bank_name=req_bank_name,
                                    branch=req_branch, account_num=req_account_num, ifsc_code=req_ifsc_code,
                                    upi=req_upi, cb=req_cb)
                    db.session.add(post)
                    db.session.commit()

                else:
                    post = Masterdb.query.filter_by(sno=sno).first()
                    post.logo = req_logo
                    post.image1 = req_image1
                    post.image2 = req_image2
                    post.main_title = req_main_title
                    post.main_text = req_main_text
                    post.sub_title = req_sub_title
                    post.sub_text = req_sub_text
                    post.address = req_address
                    post.contact = req_contact
                    post.email = req_email
                    post.account_num = req_account_num
                    post.bank_name = req_bank_name
                    post.branch = req_branch
                    post.ifsc_code = req_ifsc_code
                    post.upi = req_upi
                    post.cb = req_cb
                    db.session.commit()

                no = str(post.sno)
                return redirect('/edit/' + no)

        post = Masterdb.query.filter_by(sno=sno).first()

        if sno != '0':
            team_mem = Team.query.filter_by(ngo = post.ngo).all()
            act= Action.query.filter_by(ngo = post.ngo).all()
            return render_template("edit.html", team_mem=team_mem, act=act, post=post, sno=sno)
        else:
            return render_template("edit.html", sno=sno, slug = slug_data, ngo = ngo_data, post=post)



@app.route("/")
def home():
    return render_template("land.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/<post_slug>', methods=['GET', 'POST'])
def website(post_slug):
    success = False
    print(post_slug)
    content = Masterdb.query.filter_by(slug=post_slug).first()
    if content is None:
        print('ok')
    else:
        print('no')
    if request.method == 'POST':
        success = volunteer(content.ngo)
        print(success)

    act = Action.query.filter_by(ngo=content.ngo).all()
    posts = Team.query.filter_by(ngo=content.ngo).all()
    if posts is not None and act is not None:
        return render_template("replicate.html", post=posts, act=act, content=content, success = success)
    else:
       if posts is None and act is not None:
          return render_template("replicate.html", act=act, content=content, success = success)
       else:
         if act is None and posts is not None:
            return render_template("replicate.html", post=posts, content=content, success = success)
         else:
           return render_template("replicate.html", content=content, success = success)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username=='Potnis' and password=='Gururaj':
            session['username'] = username
            session['logged_in'] = True

    if 'username' in session and session['username'] == 'Potnis':
        posts = db.session.query(Masterdb).all()
        return render_template('dashboard.html', posts=posts)
    else:
        return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    UPLOAD_FOLDER = 'static/image'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4' ''])
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    if request.method == 'POST':
            # check if the post request has the file part
         if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
         file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
         if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
         if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return 'file uploaded successfully'

@app.route('/team/<string:sno>', methods=['GET', 'POST'])
def team(sno):
    filename = ""
    if request.method == 'POST':
        try:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = request.form.get('photo')
        except Exception as e:
            print("Form without file " + str(e))

        data = Masterdb.query.filter_by(sno=sno).first()
        ngo_name = data.ngo
        name = str(request.form.get('name'))
        photo_name = str(filename)
        text = str(request.form.get('text'))

        posts = Team(ngo=ngo_name, name=name, photo=photo_name, text=text)
        db.session.add(posts)
        db.session.commit()

    return redirect('/edit/' + sno)

@app.route('/edit/<string:sno>/team/delete/<string:post_name>', methods=['GET', 'POST'])
def team_delete(sno, post_name):
    data = Masterdb.query.filter_by(sno =sno).first()
    ngo_name = data.ngo
    posts = Team.query.filter_by(name=post_name, ngo = ngo_name).first()
    db.session.delete(posts)
    db.session.commit()
    return redirect('/edit/' + sno)

@app.route('/action/<string:sno>', methods=['GET', 'POST'])
def action(sno):
    filename = ""
    if request.method == 'POST':
        try:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = request.form.get('image')
        except Exception as e:
            print("Form without file " + str(e))

        data = Masterdb.query.filter_by(sno=sno).first()
        ngo_name = data.ngo
        image = str(filename)
        headline = str(request.form.get('headline'))
        text = str(request.form.get('text'))


        posts = Action( ngo=ngo_name, image=image, headline=headline, text=text )
        db.session.add(posts)
        db.session.commit()

    return redirect('/edit/' + sno)

@app.route('/edit/<string:sno>/action/delete/<string:post_headline>', methods=['GET', 'POST'])
def action_delete(sno, post_headline):
    data = Masterdb.query.filter_by(sno=sno).first()
    ngo_name = data.ngo
    posts = Action.query.filter_by(headline=post_headline, ngo=ngo_name).first()
    db.session.delete(posts)
    db.session.commit()
    return redirect('/edit/' + sno)


@app.route('/website_delete', methods =['GET', 'POST'])
def website_delete():
    if request.method == 'POST':
      sno = request.form['id']
      posts = Masterdb.query.filter_by(sno = sno).first()
      db.session.delete(posts)
      db.session.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
   session.pop('username', None)
   return redirect('/dashboard')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404  # Not Found

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html', error=str(error)), 500  # Internal Server Error

if __name__== "__main__":
 app.run()
