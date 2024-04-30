from cs50 import SQL
from datetime import datetime, date
from flask import Flask, redirect, render_template, jsonify, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required


# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///accounting_app.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


## User accounts - Registr, Login, Loogout
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # bunches of checking go here
        username = request.form.get("username")
        password = request.form.get("password")
        error = ""

        if not username:
            error = "Missing username."
            return render_template("register.html", username=username, password=password, error=error)
        if not password:
            error = "Missing password."
            return render_template("register.html", username=username, password=password, error=error)

        check_username = db.execute("SELECT id FROM users WHERE username = ?", username)
        if check_username:
            error = "Username has already been taken."
            return render_template("register.html", username=username, password=password, error=error)
        if len(password) < 8:
            error = "Password must contain at least 8 characters."
            return render_template("register.html", username=username, password=password, error=error)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # bunches of checking go here
        username = request.form.get("username")
        password = request.form.get("password")
        error = ""

        if not username:
            error = "Missing username"
            return render_template("login.html", username=username, password=password, error=error)
        if not password:
            error = "Missing password"
            return render_template("login.html", username=username, password=password, error=error)

        user = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(user) != 1 or not check_password_hash(user[0]["hash"], password):
            error = "Invalid username and/or password."
            return render_template("login.html", username=username, password=password, error=error)

        session["user_id"] = user[0]["id"]

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


## User's transaction data
# Global context for more than one path - Overview total cards, Add Transaction Form category select options
@app.context_processor
def overview():
    if session.get("user_id") is not None:
        totals = db.execute("SELECT SUM(IIF(type='income', amount, 0)) AS incomes, SUM(IIF(type='expense', amount, 0)) AS expenses, SUM(amount) AS balance FROM transactions WHERE user_id = ?", session["user_id"])[0]
        for key in totals:
            if totals[key] is None:
                totals[key] = "£0"
            else:
                if totals[key] >= 1000000000 or totals[key] <= -1000000000:
                    totals[key] = str(round(totals[key] / 1000000000, 1)) + "B"
                elif totals[key] >= 1000000 or totals[key] <= -1000000:
                    totals[key] = str(round(totals[key] / 1000000, 1)) + "M"
                elif totals[key] >= 10000 or totals[key] <= -10000:
                    totals[key] = str(round(totals[key] / 1000, 1)) + "k"
                else:
                    totals[key] = str(round(totals[key], 2))
                totals[key] = ("£" + totals[key]).replace("£-", "-£")

        today = date.today().strftime('%Y-%m-%d')

        income_categories = db.execute("SELECT name FROM categories WHERE user_id = ? AND type = 'income' ORDER BY name", session["user_id"])
        expense_categories = db.execute("SELECT name FROM categories WHERE user_id = ? AND type = 'expense' ORDER BY name", session["user_id"])
        categories = {
            "income": income_categories,
            "expense": expense_categories,
        }

        return dict(totals=totals, today=today, categories=categories)
    return dict()


# Create, update, delete transaction data
@app.route("/addcategory", methods=["POST"])
@login_required
def addcategory():
    type = request.form.get("type")
    category = request.form.get("category")

    # validations
    # type
    if not type:
        return jsonify({"status": "error", "message": "Transaction type is required."}), 400
    if type not in ["income", "expense"]:
        return jsonify({"status": "error", "message": "Transaction must be either income or expense."}), 400

    #category
    if not category:
        return jsonify({"status": "error", "message": "Category cannot be empty."}), 400
    existing_categories = db.execute("SELECT name FROM categories WHERE user_id = ? AND type = ?", session["user_id"], type)
    if category in [row["name"] for row in existing_categories]:
        return jsonify({"status": "error", "message": "This category already exists."}), 400

    db.execute("INSERT INTO categories (user_id, type, name) VALUES (?, ?, ?)", session["user_id"], type, category)
    return jsonify({"status": "success"}), 200


@app.route("/editcategory",  methods=["POST"])
@login_required
def editcategory():
    old_category = request.form.get("old_category")
    category = request.form.get("category")

    try:
        db.execute("UPDATE categories SET name = ? WHERE user_id = ? AND id = ?", category, session["user_id"], old_category)
        return jsonify({"status": "success"}), 200
    except:
        return jsonify({"status": "error", "message": "Failed to update the category."}), 200



@app.route("/deletecategory", methods=["POST"])
@login_required
def deletecategory():
    category = request.form.get("category")

    try:
        db.execute("DELETE FROM transactions WHERE user_id = ? AND category_id = ?", session["user_id"], category)
        db.execute("DELETE FROM categories WHERE user_id = ? AND id = ?", session["user_id"], category)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(str(e))
        return jsonify({"status": "error"}), 400


def validate_transaction(date, type, category, amount):
    # validations
    # date:
    if not date:
        return {"status": "error", "message": "Date is required."}
    try:
        datetime.fromisoformat(date) # check if date is in YYYY-mm-dd format
    except ValueError:
        return {"status": "error", "message": "Date is not in date format."}

    # type:
    if not type:
        return {"status": "error", "message": "Transaction type is required."}
    if type not in ["income", "expense"]:
        return {"status": "error", "message": "Transaction must be either income or expense."}

    # category
    if not category:
        return {"status": "error", "message": "Category is required."}
    existing_categories = db.execute("SELECT name FROM categories WHERE user_id = ? AND type = ?", session["user_id"], type)
    if category not in [row["name"] for row in existing_categories]:
        return {"status": "error", "message": "Invalid category. Please choose from your existing categories or add a new category."}

    # amount
    if not amount:
        return {"status": "error", "message": "Amount is required."}
    try:
        amount = float(amount)
    except ValueError:
        return {"status": "error", "message": "Amount must be a number."}
    if amount < 0:
        return {"status": "error", "message": "Amount cannot be smaller then 0."}

    return None

@app.route("/addtransaction", methods=["POST"])
@login_required
def addtransaction():
    date = request.form.get("date")
    type = request.form.get("type")
    category = request.form.get("category")
    description = request.form.get("description")
    amount = request.form.get("amount")

    result = validate_transaction(date, type, category, amount)

    if result:
        return jsonify(result), 400

    # Max decimal as 5
    amount = round(float(amount), 5)

    # make amount negative if type is expense
    if type == "expense":
        amount = -amount

    category = db.execute("SELECT id FROM categories WHERE user_id = ? AND name = ?",
                          session["user_id"], category)[0]["id"]

    db.execute("INSERT INTO transactions (user_id, type, date, category_id, description, amount) VALUES (?, ?, ?, ?, ?, ?)",
               session["user_id"], type, date, category, description, amount)
    return jsonify({"status": "success"}), 200


@app.route("/edittransaction", methods=["POST"])
@login_required
def edittransaction():
    date = request.form.get("date")
    type = request.form.get("type")
    category = request.form.get("category")
    description = request.form.get("description")
    amount = request.form.get("amount")
    id = request.form.get("id")

    result = validate_transaction(date, type, category, amount)

    if result:
        return jsonify(result), 400

    # Max decimal as 5
    amount = round(float(amount), 5)

    # make amount negative if type is expense
    if type == "expense":
        amount = -amount

    # get category id by name
    category = db.execute("SELECT id FROM categories WHERE user_id = ? AND name = ?", session["user_id"], category)[0]["id"]

    db.execute(
        "UPDATE transactions SET date = ?, type = ?, category_id = ?, description = ?, amount = ? WHERE id = ?",
        date, type, category, description, amount, id)
    return jsonify({"status": "success"}), 200


@app.route("/deletetransaction", methods=["POST"])
@login_required
def deletetransaction():
    id = request.form.get("id")
    try:
        db.execute("DELETE FROM transactions WHERE id = ?", id)
        return jsonify({"status": "success"}), 200
    except:
        return jsonify({"status": "error"}), 400




# Transactions List
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # values for month select lists:
    months = db.execute("SELECT DISTINCT DATE(date, 'start of month') AS month FROM transactions WHERE user_id = ? ORDER BY month DESC", session["user_id"])
    months = [row["month"] for row in months]

    # set values of type and selected_month depending on request method
    # if method is POST, use user's selected value
    if request.method == "POST":
        type = request.form.get("type")
        selected_month = datetime.strptime(request.form.get("month"), "%b %Y").strftime("%Y-%m-%d") # change date format from "MMM YYYY" to "YYYY-mm-dd"

        # validations to prevent any broken value --> redirect to "/" (reset as default value):
        if not type or not selected_month:
            return redirect("/")
        if type not in ["income", "expense"]:
            return redirect("/")
        if selected_month not in months:
            return redirect("/")
    # else if method is GET, make the values as default values
    else:
        if not months:
            months = None
            return render_template("index.html", months=months)

        type = "expense"
        selected_month = months[0]

    # get transactions according to the values of type and selected_month
    transactions = db.execute(
        "SELECT t.id, t.type, t.date, c.name AS category, t.description, t.amount FROM transactions AS t LEFT JOIN categories AS c ON t.category_id = c.id WHERE t.type = ? AND DATE(date, 'start of month') = ? AND t.user_id = ? ORDER BY t.date DESC, t.id DESC",
        type, selected_month, session["user_id"])
    # format amount with £ sign
    for transaction in transactions:
        transaction["amount"] = ("£" + str(abs(transaction["amount"]))).replace("£-", "-£")

    # group transactions by date
    grouped_transactions = {}
    for transaction in transactions:
        date = transaction["date"]
        if date in grouped_transactions:
            grouped_transactions[date].append(transaction)
        else:
            grouped_transactions[date] = [transaction]
    grouped_transactions = {datetime.fromisoformat(k).strftime("%d %b %Y"): v
                            for k, v in grouped_transactions.items()}

    # format month from "YYYY-mm-dd" to "MMM YYYY"
    months = [datetime.fromisoformat(m).strftime("%b %Y") for m in months]
    selected_month = datetime.fromisoformat(selected_month).strftime("%b %Y")
    print(selected_month)

    return render_template("index.html", months=months, type=type, selected_month=selected_month, grouped_transactions=grouped_transactions)


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # values for month select lists:
    months = db.execute("SELECT DISTINCT DATE(date, 'start of month') AS month FROM transactions WHERE user_id = ? ORDER BY month DESC", session["user_id"])
    months = [row["month"] for row in months]

    if request.method == "POST":
        type = request.form.get("type")
        chart_month = request.form.get("chart_month")

        if type not in ["income", "expense"]:
            return redirect("/dashboard")

        try:
            chart_month = datetime.strptime(chart_month, "%b %Y").strftime("%Y-%m-%d")
        except ValueError:
            return redirect("/dashboard")

    else:
        if not months:
            months = None
            return render_template("/dashboard.html", months=months, sums=[], names=[])

        type = "expense"
        chart_month = months[0]


    total_by_category = db.execute("SELECT c.name, SUM(amount) AS total FROM transactions AS t LEFT JOIN categories AS c ON t.category_id = c.id WHERE t.user_id = ? AND t.type = ? AND DATE(t.date, 'start of month') = ? GROUP BY c.name", session["user_id"], type, chart_month)
    sums = [abs(row["total"]) for row in total_by_category]
    names = [row["name"] for row in total_by_category]

    chart_month = datetime.fromisoformat(chart_month).strftime("%b %Y")
    months = [datetime.fromisoformat(month).strftime("%b %Y") for month in months]

    return render_template("dashboard.html", type=type, chart_month=chart_month, months=months, sums=sums, names=names)


# Categories
@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        type = request.form.get("type")

        if type not in ["income", "expense"]:
            return redirect("/categories")

    else:
        type = "expense"

    categories = db.execute("SELECT id, name FROM categories WHERE user_id = ? AND type = ?", session["user_id"], type)
    return render_template("categories.html", type=type, categories=categories)
