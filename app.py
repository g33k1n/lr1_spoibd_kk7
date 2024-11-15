from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from bot import bot
import config

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/start_bot')
def start_bot():
    bot.send_message_to_all("Bot is now active!")
    return "Bot started"


if __name__ == '__main__':
    app.run(debug=True)
