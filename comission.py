from operator import or_
import re
import os
from sys import platform
from threading import Barrier, current_thread
from typing import NewType
from warnings import resetwarnings
from flask import Flask, app, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import session
from flask import session
from wtforms import Form, StringField, TextAreaField, PasswordField, form, validators
from wtforms.fields.core import BooleanField, FloatField, IntegerField, SelectField, SelectMultipleField
from wtforms.fields.simple import TextField
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/AhmetM/Desktop/Komisyon Hesapla/database/prod.db' 
app.secret_key = 'ybblog'
db = SQLAlchemy(app)
app.secret_key = os.urandom(16)
####DataBases

class User(db.Model):
    id  = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80))
    surname = db.Column(db.String(120))
    username = db.Column(db.String(25))
    email = db.Column(db.String(80))
    password = db.Column(db.String(40))




class Product(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    title = db.Column(db.String(80))
    buy = db.Column(db.Float)
    sell = db.Column (db.Float)
    n11_comission = db.Column(db.Integer)
    ty_comission = db.Column(db.Integer)
    hb_comission = db.Column(db.Integer)
    gg_comission = db.Column(db.Integer)
    amzn_comission = db.Column(db.Integer)
    cicek_sepeti_comission = db.Column(db.Integer)
    cargo = db.Column(db.Float)
    barcode = db.Column(db.String)
    income = db.Column(db.Float)
    categories = db.Column(db.String(80))
    tax_ratio = db.Column(db.Integer)
    user_id = db.Column(db.Integer)




####Forms
class Login(Form):
    username = StringField('User Name:',validators=[validators.DataRequired(message='This field is required')])
    password = PasswordField('Password: ',validators=[validators.DataRequired(message='This field is required')])


class SignUp(Form):
    name = StringField('Name',validators=[validators.DataRequired(message='This field is required')])
    surname = StringField('Surname',validators=[validators.DataRequired(message='This field is required')])
    username = TextField('User Name:',validators=[validators.DataRequired(message='This field is required')])
    email = EmailField('E-mail',validators=[validators.DataRequired(message='This field is required')])
    password = PasswordField('Password:',validators=[validators.DataRequired(message='This field is required'), validators.equal_to(fieldname='confirm', message='Passwords is not matching')])
    confirm = PasswordField('Confirm Your Passwor:',validators=[validators.DataRequired(message='This field is required')])


class ProductCalc(Form):
    name = TextField('Product Name:')
    barcode = TextField('Barcode')
    buy_price = FloatField(label=None,validators=[validators.DataRequired(message='This data is required.')])
    comission_rate = IntegerField(validators=[validators.DataRequired(message='This data is required.')])
    sell_price = FloatField(validators=[validators.DataRequired(message='This data is required.')])
    tax_rate = IntegerField(validators=[validators.DataRequired(message='This data is required.')])
    cargo_price = FloatField(validators=[validators.DataRequired(message='This data is required.')])
   

class Platform(Form):
    #platform = SelectField('Platform',choices = ['N11', 'Trendyol','Hepsiburada', 'Gitti Gidiyor','Amazon', 'Çicek Sepeti'],validators=[validators.Required()])
    n11 = IntegerField('N11')
    tyol= IntegerField('Trendyol')
    gg = IntegerField('Gitti Gidiyor')
    cicek_sepeti =IntegerField('Çiçek Sepeti')
    amzn =IntegerField('Amazon')
    hb =IntegerField('Hepsiburada')
    default_commission = BooleanField('Fix All With N11 Rate')


# Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            #flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))

    return decorated_function

@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    form = ProductCalc(request.form)
    plat = Platform(request.form)
    products = Product.query.all()
    if request.method == 'POST':
        n11_value = plat.n11.data
        ty = plat.tyol.data
        hb = plat.hb.data
        gg = plat.gg.data
        amzn = plat.amzn.data
        cicek_sepeti = plat.cicek_sepeti.data
        fix_commision = plat.default_commission.data
        if fix_commision == True:
            ty = n11_value
            hb = n11_value
            gg = n11_value
            amzn = n11_value
            cicek_sepeti = n11_value
        prod_name = form.name.data
        prod_barcode = form.barcode.data
        buy_price = form.buy_price.data
        sell_price = form.sell_price.data
        tax_rate = form.tax_rate.data
        cargo_price = form.cargo_price.data
        
        
        if request.form.get('calc'):

            results = calculate(n11_value,
                        ty,
                        hb,
                        gg,
                        amzn,
                        cicek_sepeti,
                        buy_price,
                        sell_price,
                        tax_rate,
                        cargo_price)
            return redirect(url_for('calculation', results = results))

        elif  request.form.get('calcsave'):
            
            user = User.query.filter_by(username = session['username']).first()
            prod = Product(title = prod_name, 
                            barcode = prod_barcode,
                            buy = buy_price,
                            sell = sell_price, 
                            cargo = cargo_price,
                            user_id = user.id, 
                            n11_comission = n11_value,
                            ty_comission = ty,
                            amzn_comission = amzn,
                            hb_comission = hb,
                            gg_comission = gg,
                            cicek_sepeti_comission = cicek_sepeti,
                            tax_ratio = tax_rate
                             )

            db.session.add(prod)
            db.session.commit()

            return redirect(url_for('index'))

        elif request.form.get('searchbtn') :
            search_keyword = request.form['searchbox']
            return redirect(url_for('search',search_keyword = search_keyword))

               
        return render_template('search.html')

    rows_per_page = 5
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username = session['username']).first()
    db_results = Product.query.filter_by(user_id = user.id).paginate(page = page, per_page = rows_per_page)

    return render_template('layout.html', products = products,form = form, plat = plat, db_results = db_results , user = user)

@app.route('/deneme')
def deneme():
    return render_template('deneme.html')

@app.route('/calculation',methods=['POST','GET'])
def  calculation():
    results = request.args.getlist('results',None)
    return render_template('calculation.html', results = results)
    

@app.route('/delete/<string:id>')
@login_required
def delete(id):
    current_user_id = User.query.filter_by(username = session['username']).first().id
    
    delete = Product.query.filter_by(id = id).first()

    if delete != 0 and current_user_id == delete.user_id:
        db.session.delete(delete)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/details/<string:id>')
@login_required
def details(id):
    product = Product.query.filter_by(id = id).first()
    user_of_that_product = Product.query.filter_by(id = id).first()
    user_name_current = User.query.filter_by(username = session['username']).first()
    # user has that product
    if (user_name_current.id == user_of_that_product.user_id):   
        results = calculate(product.n11_comission,
                            product.ty_comission,
                            product.hb_comission,
                            product.gg_comission,
                            product.amzn_comission,
                            product.cicek_sepeti_comission,
                            product.buy,
                            product.sell,
                            product.tax_ratio,
                            product.cargo)
        return render_template('calculation.html', results = results)
    else:
        # This product is not belong to that user
        return redirect(url_for('index'))


@app.route('/search', methods =  ['POST', 'GET'])
def search():
   
    if request.method == 'POST':
        pass

        return render_template('search.html')
    elif request.method == 'GET':
        key = request.args.get('search_keyword')
        ara = Product.query.filter(or_(title = key, barcode = key))
        print(ara)

        return render_template('search.html', key = key)



@app.route('/login', methods=['POST','GET'])
def login():
    form = Login(request.form)
    if request.method:
        if request.method == 'POST' and form.validate():
            if request.form.get('Login'):
                username = form.username.data
                login_user = User.query.filter_by(username =username).first()
                if login_user != None and sha256_crypt.verify(form.password.data, login_user.password):

                    session['logged_in'] = True
                    session['username'] = form.username.data

                    return redirect(url_for('index'))
    return render_template('login.html',form = form)
    
@app.route('/signup', methods=['POST','GET'])
def signup():
    form = SignUp(request.form)

    if request.method:
        if request.method =='POST' and form.validate():
            if request.form.get('signup'):
                name = form.name.data
                surname = form.surname.data
                username = form.username.data
                email = form.email.data
                password = sha256_crypt.encrypt(form.password.data)

                new_user = User(name= name, surname = surname,username = username,  password = password,email = email)

                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('index'))

    return render_template('signup.html', form=form)

@app.route('/logout')   
def logout():
    session.clear()
    return redirect(url_for('index'))

def calculate(n11, 
    ty, 
    hb, 
    gg,
    amzn, 
    cicek_sepeti, 
    buy,
    sell,
    tax,
    cargo_price,
    ):

        return (calc_n11(n11,buy,sell,tax,cargo_price),
                calc_ty(ty,buy,sell,tax,cargo_price),
                calc_hb(hb,buy,sell,tax,cargo_price),
                calc_gg(gg,buy,sell,tax,cargo_price),
                calc_amzn(amzn,buy,sell,tax,cargo_price),
                calc_cicek_sepeti(cicek_sepeti,buy,sell,tax,cargo_price)        
                )


def calc_n11(rate, buy, sell, tax, cargo):
    return sell
def calc_ty(rate, buy, sell, tax, cargo):
    return sell
def calc_hb(rate, buy, sell, tax, cargo):
    return sell
def calc_gg(rate, buy, sell, tax, cargo):
    return sell
def calc_amzn(rate, buy, sell, tax, cargo):
    return sell
def calc_cicek_sepeti(rate, buy, sell, tax, cargo):
    return sell


if __name__ == '__main__':
    db.create_all()
    
    app.run(debug= True)