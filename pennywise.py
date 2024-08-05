import telebot
from telebot import types
import sqlite3
from datetime import datetime

# Telegram Bot API Token
TOKEN = 'token'
bot = telebot.TeleBot(TOKEN)

# Database setup
conn = sqlite3.connect('finance_bot.db', check_same_thread=False)
cursor = conn.cursor()

def initialize_db():
    # Create tables for income, expenses, budgets, goals, and progress
    cursor.execute('''CREATE TABLE IF NOT EXISTS income (
                      user_id INTEGER,
                      amount REAL,
                      category TEXT,
                      date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                      user_id INTEGER,
                      amount REAL,
                      category TEXT,
                      date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
                      user_id INTEGER,
                      category TEXT,
                      amount REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS goals (
                      user_id INTEGER,
                      goal_name TEXT,
                      target_amount REAL,
                      deadline DATE)''')
    conn.commit()

initialize_db()

# Function to create an inline keyboard
def make_inline_keyboard(buttons):
    markup = types.InlineKeyboardMarkup()
    for button in buttons:
        markup.add(types.InlineKeyboardButton(text=button[0], callback_data=button[1]))
    return markup

# /start command with inline keyboard
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = "🌟 Welcome to your Personal Finance and Budget Tracking Bot! 🌟"
    buttons = [
        ("💰 Income", "income"),
        ("💸 Expense", "expense"),
        ("📋 Plan Budget", "plan_budget"),
        ("🎯 Goals", "set_goal"),
        ("🔍 Track Progress", "track_progress"),
        ("📊 Status Report", "status_report"),
        ("🔄 Reset Data", "reset_data")
    ]
    markup = make_inline_keyboard(buttons)
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)


    # Callback handler for inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id

    if call.data == "income":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add", callback_data="add_income"),
                   types.InlineKeyboardButton("❌Delete", callback_data="delete_income"))
        bot.send_message(call.message.chat.id, "💲 Choose an action for Income:", reply_markup=markup)

    elif call.data == "expense":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add", callback_data="add_expense"),
                   types.InlineKeyboardButton("❌Delete", callback_data="delete_expense"))
        bot.send_message(call.message.chat.id, "💲 Choose an action for Expense:", reply_markup=markup)

    elif call.data == "add_income":
        msg = bot.send_message(call.message.chat.id, "🖊️ Enter the amount and category of the income (e.g., 500 Salary):")
        bot.register_next_step_handler(msg, process_add_income, user_id)

    elif call.data == "add_expense":
        msg = bot.send_message(call.message.chat.id, "🖊️ Enter the amount and category of the expense (e.g., 30 Food):")
        bot.register_next_step_handler(msg, process_add_expense, user_id)

    elif call.data == "delete_income":
        msg = bot.send_message(call.message.chat.id, "🖊️ Enter the amount and category of the income entry to delete (e.g., 500 Salary):")
        bot.register_next_step_handler(msg, process_delete_income, user_id)

    elif call.data == "delete_expense":
        msg = bot.send_message(call.message.chat.id, "🖊️ Enter the amount and category of the expense entry to delete (e.g., 30 Food):")
        bot.register_next_step_handler(msg, process_delete_expense, user_id)

    elif call.data == "plan_budget":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add", callback_data="add_budget"),
               types.InlineKeyboardButton("❌ Delete", callback_data="delete_budget"),
               types.InlineKeyboardButton("👀 View", callback_data="view_budgets"))
        bot.send_message(call.message.chat.id, "💲 Choose an action for Budget:", reply_markup=markup)

    elif call.data == "add_budget":
        process_add_budget(call, call.from_user.id)

    elif call.data == "delete_budget":
        process_delete_budget(call, call.from_user.id)

    elif call.data == "view_budgets":
        process_view_budgets(call, call.from_user.id)

    elif call.data.startswith("view_") and call.data.endswith("_budget"):
        category = call.data.split("_")[1]
        process_view_specific_budget(call.message, user_id, category)

    elif call.data == "view_all_budgets":
        process_view_all_budgets(call.message, user_id)

    elif call.data == "set_goal":
        instructions = "ℹ️ To add progress towards a goal, register it as an Income with the category name matching the goal ℹ️"
        choose_action_message = "\n\n💲 Choose an option for Goals:"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add", callback_data="add_goal"),
                types.InlineKeyboardButton("❌ Delete", callback_data="delete_goal"),
                types.InlineKeyboardButton("👀 View", callback_data="view_goals"))
        bot.send_message(call.message.chat.id, instructions + choose_action_message, reply_markup=markup)

    elif call.data == "add_goal":
        process_add_goal(call, call.from_user.id)

    elif call.data == "delete_goal":
        process_delete_goal(call, call.from_user.id)

    elif call.data == "view_goals":
        process_view_goals(call, call.from_user.id)

    elif call.data == "track_progress":
        goals = get_all_goals(user_id)
        markup = types.InlineKeyboardMarkup()
        for goal in goals:
            markup.add(types.InlineKeyboardButton(goal[0], callback_data=f"goal_{goal[0]}"))
        markup.add(types.InlineKeyboardButton("All Goals", callback_data="all_goals"))
        bot.send_message(call.message.chat.id, "🔘 Select a goal to track its progress:", reply_markup=markup)

    elif call.data.startswith("goal_"):
        goal_name = call.data.split("goal_")[1]
        process_specific_goal_progress(call.message, user_id, goal_name)

    elif call.data == "all_goals":
        process_all_goals_progress(call.message, user_id)

    elif call.data == "track_progress":
        msg = bot.send_message(call.message.chat.id, "🖊️ Enter the goal name to track its progress (e.g., Vacation):")
        bot.register_next_step_handler(msg, process_track_progress, user_id)

    elif call.data == "status_report":
        process_status_report(call.message, user_id)

    elif call.data == "reset_data":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Yes, reset my data", callback_data="reset_yes"),
                   types.InlineKeyboardButton("❌ No", callback_data="reset_no"))
        bot.send_message(call.message.chat.id, "🤔 Are you sure you want to reset all your data? This action cannot be undone 🤔", reply_markup=markup)

    elif call.data == "reset_yes":
        reset_user_data(user_id)
        bot.answer_callback_query(call.id, "✅ Your data has been reset ✅")

    elif call.data == "reset_no":
        bot.answer_callback_query(call.id, "❌ Data reset cancelled ❌")

# functions for processing each action

#add income
def process_add_income(message, user_id):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        category = ' '.join(parts[1:])
        date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO income (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                       (user_id, amount, category, date))
        conn.commit()
        bot.reply_to(message, "✅ Income recorded successfully ✅")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#add expense
def process_add_expense(message, user_id): # expense
    try:
        parts = message.text.split()
        amount = float(parts[0])
        category = ' '.join(parts[1:])
        date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                       (user_id, amount, category, date))
        conn.commit()
        bot.reply_to(message, "✅ Expense recorded successfully ✅")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#delete income
def process_delete_income(message, user_id):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        category = ' '.join(parts[1:])
        cursor.execute("DELETE FROM income WHERE user_id = ? AND amount = ? AND category = ?",
                       (user_id, amount, category))
        if cursor.rowcount > 0:
            conn.commit()
            bot.reply_to(message, "✅ Income entry deleted successfully ✅")
        else:
            bot.reply_to(message, "❌ No matching income entry found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#delete expense
def process_delete_expense(message, user_id):
    try:
        parts = message.text.split()
        amount = float(parts[0])
        category = ' '.join(parts[1:])
        cursor.execute("DELETE FROM expenses WHERE user_id = ? AND amount = ? AND category = ?",
                       (user_id, amount, category))
        if cursor.rowcount > 0:
            conn.commit()
            bot.reply_to(message, "✅ Expense entry deleted successfully ✅")
        else:
            bot.reply_to(message, "❌ No matching expense entry found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#plan budget menu
def process_plan_budget(message, user_id):
    try:
        parts = message.text.split()
        category = parts[0]
        amount = float(parts[1])
        cursor.execute("INSERT INTO budgets (user_id, category, amount) VALUES (?, ?, ?)",
                       (user_id, category, amount))
        conn.commit()
        bot.reply_to(message, "✅ Budget added successfully ✅")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#add budget
def process_add_budget(call, user_id):
    msg = bot.send_message(call.message.chat.id, "🖊️ Enter the budget category and amount (e.g., Entertainment 200):")
    bot.register_next_step_handler(msg, process_plan_budget, user_id)

#delete budget
def process_delete_budget(call, user_id):
    msg = bot.send_message(call.message.chat.id, "🖊️ Enter the budget category to delete:")
    bot.register_next_step_handler(msg, process_remove_budget, user_id)

#view budgets
def process_view_budgets(call, user_id):
    budgets = get_all_budgets(user_id)
    if not budgets:
        bot.send_message(call.message.chat.id, "❌ No budgets found ❌")
    else:
        markup = types.InlineKeyboardMarkup()
        for category, _ in budgets:
            markup.add(types.InlineKeyboardButton(category, callback_data=f"view_{category}_budget"))
        markup.add(types.InlineKeyboardButton("View All", callback_data="view_all_budgets"))
        bot.send_message(call.message.chat.id, "🔘 Select a budget category to view or view all:", reply_markup=markup)

#view specific budget(view menu)
def process_view_specific_budget(message, user_id, category):
    try:
        cursor.execute("SELECT amount FROM budgets WHERE user_id = ? AND category = ?", (user_id, category))
        amount = cursor.fetchone()[0]
        bot.reply_to(message, f"Budget for {category}: {amount}")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#view all budgets(view menu)
def process_view_all_budgets(message, user_id):
    try:
        budgets = get_all_budgets(user_id)
        if budgets:
            reply = "All Budgets:\n"
            for category, amount in budgets:
                reply += f" - {category}: {amount}\n"
            bot.reply_to(message, reply)
        else:
            bot.reply_to(message, "❌ No budgets found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#remove budget
def process_remove_budget(message, user_id):
    category = message.text.strip()
    try:
        cursor.execute("DELETE FROM budgets WHERE user_id = ? AND category = ?", (user_id, category))
        if cursor.rowcount > 0:
            conn.commit()
            bot.reply_to(message, f"✅ Budget category '{category}' deleted successfully ✅")
        else:
            bot.reply_to(message, "❌ No such budget category found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")


def get_all_budgets(user_id):
    cursor.execute("SELECT category, amount FROM budgets WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

#goals menu
def process_set_goal(message, user_id):
    try:
        parts = message.text.split()
        goal_name = parts[0]
        target_amount = float(parts[1])
        deadline = parts[2]  # Expected in YYYY-MM-DD format
        cursor.execute("INSERT INTO goals (user_id, goal_name, target_amount, deadline) VALUES (?, ?, ?, ?)",
                       (user_id, goal_name, target_amount, deadline))
        conn.commit()
        bot.reply_to(message, f"💲 Goal '{goal_name}' set with a target of {target_amount} by {deadline}.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#add goal
def process_add_goal(call, user_id):
    msg = bot.send_message(call.message.chat.id, "🖊️ Enter the goal name, target amount, and deadline (e.g., Vacation 1000 2023-12-25):")
    bot.register_next_step_handler(msg, process_set_goal, user_id)

#delete goal
def process_delete_goal(call, user_id):
    msg = bot.send_message(call.message.chat.id, "🖊️ Enter the goal name to delete:")
    bot.register_next_step_handler(msg, process_remove_goal, user_id)

#view goals
def process_view_goals(call, user_id):
    goals = get_all_goals(user_id)
    if goals:
        reply = "Your Goals:\n"
        for goal in goals:
            reply += f" - {goal[0]}\n"
        bot.send_message(call.message.chat.id, reply)
    else:
        bot.send_message(call.message.chat.id, "❌ No goals found ❌")

#remove goal
def process_remove_goal(message, user_id):
    goal_name = message.text.strip()
    try:
        cursor.execute("DELETE FROM goals WHERE user_id = ? AND goal_name = ?", (user_id, goal_name))
        if cursor.rowcount > 0:
            conn.commit()
            bot.reply_to(message, f"Goal '{goal_name}' deleted successfully.")
        else:
            bot.reply_to(message, "❌ No such goal found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

def get_all_goals(user_id):
    cursor.execute("SELECT goal_name FROM goals WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

#view specific goal
def process_specific_goal_progress(message, user_id, goal_name):
    try:
        cursor.execute("SELECT target_amount, deadline FROM goals WHERE user_id = ? AND goal_name = ?",
                       (user_id, goal_name))
        goal_data = cursor.fetchone()
        if goal_data:
            target_amount, deadline = goal_data
            cursor.execute("SELECT SUM(amount) FROM income WHERE user_id = ? AND category = ?",
                           (user_id, goal_name))
            income_sum = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category = ?",
                           (user_id, goal_name))
            expense_sum = cursor.fetchone()[0] or 0
            current_amount = income_sum - expense_sum
            progress_message = f"Progress for '{goal_name}':\nTarget: {target_amount}\nCurrent: {current_amount}\nDeadline: {deadline}"
            bot.reply_to(message, progress_message)
        else:
            bot.reply_to(message, "❌ No such goal found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#view all goals
def process_all_goals_progress(message, user_id):
    try:
        cursor.execute("SELECT goal_name, target_amount, deadline FROM goals WHERE user_id = ?", (user_id,))
        all_goals = cursor.fetchall()
        if all_goals:
            progress_message = "Progress for all goals:\n"
            for goal_name, target_amount, deadline in all_goals:
                cursor.execute("SELECT SUM(amount) FROM income WHERE user_id = ? AND category = ?",
                               (user_id, goal_name))
                income_sum = cursor.fetchone()[0] or 0
                cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category = ?",
                               (user_id, goal_name))
                expense_sum = cursor.fetchone()[0] or 0
                current_amount = income_sum - expense_sum
                progress_message += f"\nGoal '{goal_name}':\n - Target: {target_amount}\n - Current: {current_amount}\n - Deadline: {deadline}"
            bot.reply_to(message, progress_message)
        else:
            bot.reply_to(message, "❌ No goals found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#track progress
def process_track_progress(message, user_id):
    try:
        goal_name = message.text.strip()
        cursor.execute("SELECT target_amount, deadline FROM goals WHERE user_id = ? AND goal_name = ?",
                       (user_id, goal_name))
        goal_data = cursor.fetchone()
        if goal_data:
            target_amount, deadline = goal_data
            cursor.execute("SELECT SUM(amount) FROM income WHERE user_id = ? AND category = ?",
                           (user_id, goal_name))
            income_sum = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category = ?",
                           (user_id, goal_name))
            expense_sum = cursor.fetchone()[0] or 0
            current_amount = income_sum - expense_sum
            progress_message = f"Progress for '{goal_name}':\nTarget: {target_amount}\nCurrent: {current_amount}\nDeadline: {deadline}"
            bot.reply_to(message, progress_message)
        else:
            bot.reply_to(message, "❌ No such goal found ❌")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#status report
def process_status_report(message, user_id):
    try:
        # Fetch income and expenses
        cursor.execute("SELECT SUM(amount) FROM income WHERE user_id = ?", (user_id,))
        total_income = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,))
        total_expenses = cursor.fetchone()[0] or 0

        # Fetch budgets
        cursor.execute("SELECT category, amount FROM budgets WHERE user_id = ?", (user_id,))
        budgets = cursor.fetchall()

        # Fetch goals
        cursor.execute("SELECT goal_name, target_amount, deadline FROM goals WHERE user_id = ?", (user_id,))
        all_goals = cursor.fetchall()

        # Construct the report
        report = "💼 Financial Status Report:\n"
        report += f"📈 Total Income: {total_income}\n"
        report += f"📉 Total Expenses: {total_expenses}\n"

        report += "📋 Budgets:\n"
        if budgets:
            for category, amount in budgets:
                report += f" - {category}: {amount}\n"
        else:
            report += " - None\n"

        report += "🎯 Goals Progress:\n"
        if all_goals:
            for goal_name, target_amount, deadline in all_goals:
                cursor.execute("SELECT SUM(amount) FROM income WHERE user_id = ? AND category = ?",
                               (user_id, goal_name))
                income_sum = cursor.fetchone()[0] or 0
                cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category = ?",
                               (user_id, goal_name))
                expense_sum = cursor.fetchone()[0] or 0
                current_amount = income_sum - expense_sum
                report += f" - {goal_name}: Current: {current_amount} / Target: {target_amount} (Deadline: {deadline})\n"
        else:
            report += " - None\n"

        bot.reply_to(message, report)
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

#reset data
def reset_user_data(user_id):
    try:
        cursor.execute("DELETE FROM income WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        bot.reply_to(message, f"An error occurred: {e}")

bot.polling()