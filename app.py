from flask import Flask,render_template,request,flash,redirect,url_for,session,make_response
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import json
import os
from flask_mail import Mail
import random
pin =10
with open("config.json",'r') as c:
    dict=json.load(c)['config']
app=Flask(__name__)
app.config["UPLOAD_PATH"]="E:/"
app.secret_key='secret-key'
app.config.update(MYSQL_USER=dict["user_uri"],
MySQL_PASSWORD=dict["password_uri"],
MYSQL_HOST=dict["host_uri"],
MYSQL_DB= dict["db_uri"])
mysql=MySQL(app)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = dict["username"],
    MAIL_PASSWORD = dict["password"]
)
mail=Mail(app)
bcrypt=Bcrypt(app)
# global COOKIE_TIME_OUT
COOKIE_TIME_OUT=60*5
@app.route('/')
def nav():
        return render_template('nav.html',input=dict)
@app.route('/login')
def login():
    if 'user' in session:

        return redirect(url_for('post'))

    return render_template('login.html')
@app.route('/loged_in',methods=['GET','POST'])
def post():
    if 'user' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM post')
        post = cur.fetchall()
        return render_template('dashboard.html', post=post)

    user_name = request.form.get('nm')
    password1 = request.form.get('password')
    remember=request.form.getlist('userchoice')
    if user_name in request.cookies:
        username1=request.cookies.get('uname')
        password2=request.cookies.get('pass')
        cur=mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE username=%s',(username1,))
        user=cur.fetchone()
        if user and bcrypt.check_password_hash(user[3],password2):
            session['user']=user[0]
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM post')
            post = cur.fetchall()
            cur.close()
            flash('loged in successfully')
            return render_template('dashboard.html', post=post)
        else:
            flash('Incorrect Password')
            return redirect('/login')
    if user_name and password1:

        cur = mysql.connection.cursor()
        post=cur.execute('SELECT * FROM users WHERE name=%s',[user_name])
        if post>0:
            data=cur.fetchone()
            password=data[3]
            if bcrypt.check_password_hash(password,password1):
                session['user'] = data[0]
                if remember:
                    resp=make_response(render_template('dashboard.html'))
                    resp.set_cookie('uname',user_name, max_age=COOKIE_TIME_OUT)
                    resp.set_cookie('pass',password1, max_age=COOKIE_TIME_OUT)
                    resp.set_cookie('rem','checked', max_age=COOKIE_TIME_OUT)
                    return  resp
                else:
                    cur=mysql.connection.cursor()
                    cur.execute('SELECT * FROM post')
                    post=cur.fetchall()
                    cur.close()
                    flash('loged in successfully')
                    return render_template('dashboard.html', post=post)
            else:
                flash('Incorrect Password')
                return redirect('/login')
        else:
            flash('No username found')
            return render_template('login.html', messege="Please enter correct information")
    else:
        flash('invalid username or password')
        return redirect('/login')

@app.route('/edit/<string:input>',methods=['GET','POST'])
def edit(input):
    if 'user' in session:
        if input=="adding_post":
            return render_template('add.html')
        else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM post WHERE slug=%s', (input,))
            post=cur.fetchall()
            return render_template('edit.html', post=post)

    else:
        return redirect(url_for('login'))


@app.route('/update',methods=['GET','POST'])
def update():
    if 'user' in session:
        if request.method=='POST':
            title=request.form.get('title')
            id=request.form.get('id')
            content=request.form.get('content')
            creator=request.form.get('creator')
            slug=request.form.get('slug')
            cur=mysql.connection.cursor()
            cur.execute('UPDATE post SET title=%s,slug=%s,content=%s,creator=%s,id=%s WHERE id=%s',(title,slug,content,creator,id,id))
            mysql.connection.commit()
            cur.close()

                # return render_template('edit.html', post=post)

            return redirect(url_for('post'))
    else:
        return redirect(url_for('login'))
    return redirect('/login')
@app.route('/add',methods=['GET','POST'])
def add():
    if 'user' in session:

        if request.method=='POST':
            title=request.form.get('title')
            content=request.form.get('content')
            id=request.form.get('id')
            slug=request.form.get('slug')
            creator=request.form.get('creator')
            cur=mysql.connection.cursor()
            cur.execute('INSERT INTO post(id,title,slug,creator,content) VALUE(%s,%s,%s,%s,%s)',(id,title,slug,creator,content))
            mysql.connection.commit()
            cur.close()
            flash('added successfully')

            return redirect(url_for('post'))


    else:
        return redirect(url_for('post'))
    return redirect(url_for('login'))
@app.route('/delete/<string:srno>',methods=['GET','POST'])
def delete(srno):
    if 'user' in session:

        cur=mysql.connection.cursor()
        cur.execute('DELETE FROM post WHERE srno=%s',(srno,))
        mysql.connection.commit()
        cur.close()
        flash('deleted succesfully')
        return redirect(url_for('post'))

    else:
        return redirect(url_for('post'))
@app.route('/upload',methods=['GET','POST'])
def upload():
    if 'user' in session:
        if request.method=='POST':
            for file in request.files.getlist('file_name'):
                            # file=request.files['file_name']  #(this is used when uploding single file)
                file.save(os.path.join(app.config["UPLOAD_PATH"],file.filename))
                flash('Uploaded Successfully')
                return redirect(url_for('post'))


        else:

            return redirect(url_for('post'))
    return redirect(url_for('post'))
@app.route('/log_out')
def log_out():
    if 'user' in session:
        session.pop('user')
        flash('Loged out Successfully')
        return  redirect(url_for('nav'))

# -----------------***************From Registration.py*******************------------
@app.route('/register')
def register():
    return render_template('info.html')
@app.route('/registered',methods=['GET','POST'])
def registered():
    if request.method=='POST':
        name=request.form.get('username')
        email=request.form.get('email')
        mobile=request.form.get('number')
        password=request.form.get('password')
        dob=request.form.get('dob')
        confirm_password = request.form.get('confirm_password')
        if confirm_password != password:
            flash(" Confirm Password did not match")
            return redirect('/register')
        cur=mysql.connection.cursor()
        num=cur.execute('SELECT * FROM users WHERE name=%s',(name,))
        if num>0:
            flash('This username is not available')
            return redirect('register')
        else:
            cur=mysql.connection.cursor()
            cur.execute('INSERT INTO users(name,email,mobile,password,dob) VALUE(%s,%s,%s,%s,%s)',
                        (name,email,mobile,bcrypt.generate_password_hash(password),dob))
            mysql.connection.commit()
            cur.close()
            flash('Registered successfully')
            return redirect(url_for('login'))
@app.route("/forget",methods=['POST','GET'])
def forget():
    return render_template('forgetpassword.html')
@app.route('/otp',methods=['POST','GET'])
def otp():

    if request.method=='POST':
        email=request.form.get('email')
        cur=mysql.connection.cursor()
        num=cur.execute('SELECT email FROM users WHERE email=%s',(email,))

        if num>0:
            otp = random.randint(10000, 50000)
            global pin
            pin=otp
            mail.send_message('Reseting Password', sender='ak188269@gamil.com',
                              recipients=[email],
                              body= 'We have get request to resete your account password,Enter the Otp provided to change your password'+
                                    '\nYour OTP for password reset is:- '+str(pin))
            return render_template('otp.html')

    return redirect(url_for('forget'))


    # return render_template('otp.html')
@app.route('/reset',methods=['POST','GET'])
def reset():
    if request.method=='POST':
        num=int(request.form.get('otp'))
        if num==pin:
            return render_template('newpassword.html')
        else:
            flash(' You entered wrong OTP')
            return render_template('otp.html')
    return redirect(url_for('home'))
@app.route('/newpass',methods=['POST','GET'])
def newpass():
    if request.method=='POST':
        password=request.form.get('password')
        username=request.form.get('username')
        cur = mysql.connection.cursor()
        cur.execute('UPDATE users SET password=%s WHERE name=%s', (bcrypt.generate_password_hash(password),username))
        mysql.connection.commit()
        cur.close()
        flash('Password Reset Successfully')
        return redirect(url_for('login'))
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)