from flask import Flask, redirect, url_for, render_template, request
from orchestrator import Orchestrator
app = Flask(__name__)

STATION = "10"
HOST_URL = "http://192.168.0.65:5000/events"
CONVEYOR = f"http://192.168.{STATION}.2"
ROBOT = f"http://192.168.{STATION}.1"

options = ["Draw1", "Draw2", "Draw3", "Draw4", "Draw5", "Draw6", "Draw7", "Draw8", "Draw9"]

history = []
ws_obj = Orchestrator(CONVEYOR, ROBOT, HOST_URL)
@app.route('/', methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        selected_choices = request.form.getlist('choices')
        ws_obj.store_order(selected_choices[0])
        history.insert(0, selected_choices)

    return render_template("flask_index.html",
                           options=options, history=history, station=STATION, conveyor=CONVEYOR, robot=ROBOT)

@app.route("/clear_history")
def clear_history():
    history.clear()
    return redirect(url_for("home"))

@app.route("/events", methods=["POST"])
def event_handler():
    if request.method == "POST":
        ws_obj.event_handler(request.json)
    return "Success", 202

@app.route('/calibrate')
def calibrate():
    ws_obj.calibrate()
    return redirect(url_for("home"))



@app.route('/subscribe')
def subscribe_event():
    ws_obj.subscribe_notif()

    return redirect(url_for("home"))


@app.route('/unsubscribe')
def unsubscribe_event():
    ws_obj.unsubscribe_notif()
    return redirect(url_for("home"))

@app.route('/subscriberobot')
def subscribe_event_robot():
    ws_obj.sub_robot()

    return redirect(url_for("home"))


@app.route('/unsubscriberobot')
def unsubscribe_event_robot():
    ws_obj.unsub_robot()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(host="192.168.0.65", port=5000)
