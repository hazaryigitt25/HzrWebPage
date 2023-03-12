from flask import Flask,render_template,flash,redirect,url_for,session,logging,request

from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,FloatField,IntegerField
from passlib.hash import sha256_crypt
from functools import wraps
import random


# User Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged in" in session:
            return f(*args, **kwargs)
        else:
            flash("You Have To Login To Use This Page!","danger")
            return redirect(url_for("login"))
    return decorated_function

app = Flask(__name__)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "hzbank"
app.config["MYSQL_CURSOR"] ="DictCursor"
app.secret_key = "super secret key"
app.config["SESSION_TYPE"] = "filesystem"

mysql = MySQL(app)
# Register Form
class RegisterForm(Form):
    name = StringField("Name Surname",validators=[validators.length(min = 5,message="This Is Too Short")])
    email = StringField("Email",validators=[validators.Email(message="Invalid Email")])
    password = PasswordField("Password",validators=[
        validators.DataRequired(message="You Have To Write Password"),
        validators.EqualTo(fieldname="confirm",message="Passwords Does Not Match")
    ])
    confirm = PasswordField("Password Control")
# Login Form
class LoginForm(Form):
    id = IntegerField("Id")
    password = PasswordField("Password")
# Withdraw Form
class WithdrawForm(Form):
    amount = FloatField("The Amount of Money You Will Withdraw(Max. 100000$)",validators=[validators.DataRequired(message="You Have To Write Amount"),validators.number_range(min=1,max=100000,message="You Can Make This Function Between 1 and 100000$")])
# Deposit Form
class DepositForm(Form):
    amount = FloatField("The Amount of Money You Will Deposit(Max. 100000$)",validators=[validators.DataRequired(message="You Have To Write Amount"),validators.number_range(min=1,max=100000,message="You Can Make This Function Between 1 and 100000$")])
# Transfer Form
class TransferForm(Form):
    iban = StringField("IBAN(Must Be 6 Digits)",validators=[validators.length(min=6,max=6,message="This Section Must Be 6 Digits")])
    amount = amount = FloatField("The Amount of Money You Will Transfer(Max. 100000$)",validators=[validators.DataRequired(message="You Have To Write Amount"),validators.number_range(min=1,max=100000,message="You Can Make This Function Between 1 and 100000$")])
# Change Password Form
class ChangeForm(Form):
    old_password = PasswordField("Your Password",validators=[validators.DataRequired(message="You Have To Fill Here!")])
    new_password = PasswordField("Your New Password",validators=[validators.DataRequired(message="You Have To Fill Here"),validators.EqualTo(fieldname="confirm",message="Passwords Does Not Match")])
    confirm = PasswordField("New Password Check")
# Main Page
@app.route("/")
def index():
    return render_template("index.html")

# Login Page
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        cursor = mysql.connection.cursor()
        id = form.id.data
        password_entered = form.password.data
        sorgu = "SELECT * FROM users WHERE id = %s"
        result = cursor.execute(sorgu,(id,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data[4]
            if sha256_crypt.verify(password_entered,real_password):
                session["logged in"] = True
                session["id"] = id
                session["name"] = data[1]
                session["balance"] = data[5]
                session["iban"] = data[3]
                return redirect(url_for("manage"))
            else:
                flash("Wrong Password!","danger")
                return redirect(url_for("login"))
        else:
            flash("User Could Not Found","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form = form)

# Register Page
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()
        sorgu = "SELECT iban FROM users"
        result = cursor.execute(sorgu)
        if result > 0:
            ibans = cursor.fetchall()
            
            while True:
                iban = random.randint(100000,999999)
                count = 0
                for i in ibans:
                    if iban == i:
                        count += 1
                if count == 0:
                    sorgu2 = "INSERT INTO users(name,email,iban,password,balance) VALUES(%s,%s,%s,%s,%s)"
                    iban = str(iban)
                    cursor.execute(sorgu2,(name,email,iban,password,"0"))
                    mysql.connection.commit()
                    sorgu3 = "SELECT * FROM users WHERE name = %s and email = %s"
                    cursor.execute(sorgu3,(name,email))
                    data = cursor.fetchone()
                    session["logged in"] = True
                    session["id"] = data[0]
                    session["name"] = data[1]
                    session["balance"] = data[5]
                    session["iban"] = data[3]
                    cursor.close()
                    flash("You Have Registered Successfully, Here You Are Your Bank System!","info")
                    return redirect(url_for("manage"))
        else:
            sorgu2 = "INSERT INTO users(name,email,iban,password,balance) VALUES(%s,%s,%s,%s,%s)"
            iban = random.randint(100000,999999)
            iban = str(iban)
            cursor.execute(sorgu2,(name,email,iban,password,"0"))
            mysql.connection.commit()
            sorgu3 = "SELECT * FROM users WHERE name = %s and email = %s"
            cursor.execute(sorgu3,(name,email))
            data = cursor.fetchone()
            session["logged in"] = True
            session["id"] = data[0]
            session["name"] = data[1]
            session["balance"] = data[5]
            session["iban"] = data[3]
            
            cursor.close()
            flash("You Have Registered Successfully, Here You Are Your Bank System!","info")
            return redirect(url_for("manage"))
    else:
        return render_template("register.html",form = form)
# Withdraw Function
@app.route("/withdraw",methods=["GET","POST"])
@login_required
def withdraw():
    form = WithdrawForm(request.form)
    if request.method == "POST" and form.validate():
        amount = form.amount.data
        session["amount"] = amount
        session["newbalance"] = float(session["balance"])-float(amount)
        if session["newbalance"] < 0:
            flash("You Do Not Have Enogh Money, Sorry!","danger")
            return redirect(url_for("withdraw"))
        else:
            return redirect(url_for("confirm_withdraw"))
    else:
        return render_template("withdraw.html",form = form)
# Deposit Function
@app.route("/deposit",methods=["GET","POST"])
@login_required
def deposit():
    form = DepositForm(request.form)
    if request.method == "POST" and form.validate():
        amount = form.amount.data
        new_balance = float(session["balance"])+float(amount)
        session["newbalance"] = new_balance
        session["amount"] = amount
        return redirect(url_for("confirm_deposit"))
    else:
        return render_template("deposit.html",form = form)
# Transfer Function
@app.route("/transfer",methods=["GET","POST"])
@login_required
def transfer():
    form = TransferForm(request.form)
    if request.method == "POST" and form.validate():
        iban = form.iban.data
        amount = form.amount.data
        session["amount"] = amount
        sender_money = float(session["balance"])
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE iban = %s"
        result = cursor.execute(sorgu,(iban,))
        if result > 0:
            session["sender_new_balance"] = sender_money - float(amount)
            if session["sender_new_balance"] < 0:
                flash("You Do Not Have Enough Money, Sorry!","danger")
                return redirect(url_for("transfer"))
            else:
                data = cursor.fetchone()
                session["receiver"] = data[1]
                session["new_receiver_balance"] = float(data[5]) + float(amount)
                session["receiver_id"] = data[0]
                session["receiver_email"] = data[2] 
                return redirect(url_for("confirm_transfer"))
        else:
            flash("User Could Not Found, Sorry!","warning")
            return redirect(url_for("transfer"))
    else:
        return render_template("transfer.html",form = form)
# Change Password Function
@app.route("/change_password",methods=["GET","POST"])
@login_required
def change_password():
    form = ChangeForm(request.form)
    if request.method == "POST" and form.validate():
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE id = %s"
        cursor.execute(sorgu,(session["id"],))
        data  = cursor.fetchone()
        old_password = form.old_password.data
        new_password = form.new_password.data
        if sha256_crypt.verify(old_password,data[4]):
            new_password = sha256_crypt.encrypt(new_password)
            session["newpassword"] = new_password
            return redirect(url_for("confirm_change"))
        else:
            flash("The password you have written does not match with the real one. Please! Check Again.","warning")
            return redirect(url_for("change_password"))
    else:
        return render_template("changepassword.html",form = form)
# Delete Account Function
@app.route("/delete",methods=["GET","POST"])
@login_required
def delete():
    
    if request.method == "POST":
        cursor = mysql.connection.cursor()
        sorgu = "DELETE FROM users WHERE id = %s"
        cursor.execute(sorgu,(session["id"],))
        mysql.connection.commit()
        cursor.close()
        session.clear()
        flash("You Have Been Successfully Deleted Account!","warning")
        return redirect(url_for("index"))
    else:
        return render_template("delete.html")
# Change Password Confirmation
@app.route("/change_password/confirm",methods=["GET","POST"])
@login_required
def confirm_change():
    if request.method == "POST":
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE users SET password = %s WHERE id = %s"
        cursor.execute(sorgu,(session["newpassword"],session["id"]))
        mysql.connection.commit()
        session.clear()
        cursor.close()
        flash("You Have Successfully Changed Your Password. You Have To Login Again.","info")
        return redirect(url_for("login"))
    else:
        return render_template("passwordcon.html")
# Transfer Confirm
@app.route("/transfer/confirm",methods=["GET","POST"])
@login_required
def confirm_transfer():
    if request.method == "POST":
        
        session["sender_new_balance"] = str(session["sender_new_balance"])
        session["new_receiver_balance"] = str(session["new_receiver_balance"])
        session["receiver_id"] = str(session["receiver_id"])
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE users SET balance = %s WHERE id = %s"
        cursor.execute(sorgu,(session["sender_new_balance"],session["id"]))
        mysql.connection.commit()
        cursor.execute(sorgu,(session["new_receiver_balance"],session["receiver_id"]))
        mysql.connection.commit()
        
        session["balance"] = session["sender_new_balance"]
        
        
        flash("You Have Transfered Money Successfully!","info")
        return redirect(url_for("manage"))
        
    else:
        return render_template("transfercon.html")
# Withdraw Confirm
@app.route("/withdraw/confirm",methods=["GET","POST"])
@login_required
def confirm_withdraw():
    if request.method == "POST":
        session["newbalance"] = str(session["newbalance"])
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE users SET balance = %s WHERE id = %s"
        cursor.execute(sorgu,(session["newbalance"],session["id"]))
        mysql.connection.commit()
        session["balance"] = session["newbalance"]
        cursor.close()
        flash("You Have Successfully Withdraw Money.","info")
        return redirect(url_for("manage"))
    else:
        return render_template("withdrawcon.html")
# Deposit Confirm
@app.route("/deposit/confirm",methods=["GET","POST"])
@login_required
def confirm_deposit():
    if request.method == "POST":
        session["newbalance"] = str(session["newbalance"])
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE users SET balance = %s WHERE id = %s"
        cursor.execute(sorgu,(session["newbalance"],session["id"]))
        mysql.connection.commit()
        session["balance"] = session["newbalance"]
        cursor.close()
        flash("You Have Successfully Deposit Money.","info")
        return redirect(url_for("manage"))
    else:
        return render_template("depositcon.html")
# Logout Function
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))
# Manage Page
@app.route("/manage")
@login_required
def manage():
    
    return render_template("manage.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/about_founder")
def about_f():
    return render_template("about_founder.html")



if __name__ == "__main__":
    app.run(debug=True)