import flask
from flask import Flask, request, \
    redirect, url_for, \
    render_template, \
    make_response, session,abort

app = Flask(__name__)
app.secret_key = 'any random string'


# @app.route('/')
# def index():
#     if 'username' in session:
#         username = session['username']
#         return '已经登录用户：%s'%username
#     else:
#         return "还没有登录，请登录<a href='./login'></b>" + \
#                "click here to log in</b></a>"

@app.route('/')
def index():
    # abort(401)
    # user = request.form['username']
    return render_template('index.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username']!='admin' or request.form['password']!='admin':
            error = '用户名密码错误，请再试一次'
        else:
            flask.flash('登录成功')
            return redirect(url_for('index'))
    return render_template('login.html',error=error)

@app.route('/outlogin')
def outlogin():
    session.pop('username',None)
    return redirect(url_for('index'))

@app.route('/setcookie',methods=['POST','GET'])
def setcookie():
    if request.method == "POST":
        user = request.form['name']
        resp = make_response(render_template('readcookie.html'))
        resp.set_cookie('userID',user)
        return resp
    
@app.route('/getcookie')
def getcookie():
    name = request.cookies.get('userID')
    return '<h1>welcome %s</h1>'%name

@app.route('/result',methods=['POST','GET'])
def result():
    if request.method == "POST":
        result = request.form
        return render_template("result.html",result = result)

@app.route('/success/<name>')
def success(name):
    return 'welcome %s'%name

@app.route('/hello/<user>')
def hello_name(user):
    return render_template('hello.html',name=user)


# @app.route('/login',methods=['POST','GET'])
# def login():
#     if request.method=="POST":
#         user = request.form['name']
#         return redirect(url_for('success',name=user))
#     else:
#         user = request.args.get('name')
#         return redirect(url_for('success',name=user))

if __name__ == '__main__':
    # app.add_url_rule("/","index/<name>",recognazi)
    app.run('0.0.0.0',5000,True)
    
