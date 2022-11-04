from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import json
import os
from service import create_service, get_credentials, conflict_events, create_event,  get_events, events_by_email, events_by_date, deleted_events, event_update, available_students, events_by_date_email, all_events, event_by_id, format_event_object, format_single_event_object
app = Flask(__name__)
CORS(app)

theclassicART = "msitprogram.net_ag1jsv1tkepjhp326dj2eqi1ps@group.calendar.google.com"


creds = get_credentials()

service = create_service(creds)


@app.errorhandler(404)
def page_not_found(e):
    """
    error route
    """
    return {'manchidhi': "emaina kavali ante vere route use chesko"}


@app.route("/create", methods=["POST"])
def insert_event():
    """
    to create the event
    """

    try:
        event = request.data.decode()
        event = json.loads(event)
        event = create_event(service, event)
        event = format_single_event_object(event)

        return jsonify(event)
    except Exception as ex:
        return {"status": "necessary fields are not provided , unable to create event"}


@app.route("/event/<event_id>", methods=["GET"])
def get_event_by_id(event_id):
    """
    the event is retrieved based on the eventId
    """
    try:
        event = event_by_id(service, event_id)
        event = format_single_event_object(event)

        return jsonify(event)
    except Exception:
        return {"status": "invalid eventId , unable to retrieve the event"}


@app.route("/delete/<event_id>", methods=["DELETE"])
def delete_event_by_id(event_id):
    """
    the event is deleted based on the eventId
    """
    try:
        event = service.events().delete(calendarId=theclassicART, eventId=event_id).execute()
        return {"status": "deleted"}
    except Exception:
        return {"status": "invalid eventId , unable to delete the event"}


@app.route("/allevents", methods=["GET"])
def get_all_events():
    """
    only the events which are present in the calendar are retrieved,
    events which are deleted from the calendar will not be retrieved.
    """

    try:
        events = all_events(service)
        events = format_event_object(events)
        return jsonify(events)
    except Exception:
        return {}


@app.route("/update/<event_id>", methods=["PUT"])
def update_event(event_id):
    """
    the event is updated based on the eventId
    """
    try:
        event = request.data.decode()
        event = json.loads(event)
        status = conflict_events(service, event)
        updated_event = event_update(service, event, event_id, status)

        return updated_event

    except Exception:
        return {"status": "unable to update"}


@app.route("/myevents/<email_id>", methods=["GET"])
def get_events_by_email(email_id):
    """
    all the events which the user is a part of are retrieved
    """
    try:
        events = events_by_email(service, email_id)
        events = format_event_object(events)
        return jsonify(events)
    except Exception:
        return {"status": "unable to retrieve"}


@app.route("/events/<date>", methods=["GET"])
def get_events_by_date(date):
    """
    all the events on a particular date are retrieved
    """
    try:
        timeMin = date[:10]+"T"+"00:00:00"+"+05:30"
        timeMax = date[:10]+"T"+"23:59:59"+"+05:30"
        events = events_by_date(service, timeMin, timeMax)
        events = format_event_object(events)
        return jsonify(events)
    except Exception:
        return {"status": "unable to retrieve"}


@app.route("/deletedevents", methods=["GET"])
def get_deleted_events():
    """
    all the events which are deleted from calendar are retrieved
    """
    try:
        events = deleted_events(service)
        events = format_event_object(events)

        return events
    except Exception:
        return {"status": "unable to retrieve"}


@app.route("/checkavailability", methods=["POST"])
def get_available_students():
    """
    all the events which are deleted from calendar are retrieved
    """
    try:
        event = request.data.decode()
        event = json.loads(event)

        availability = available_students(service, event)
        return jsonify(availability)
    except Exception:
        return {"status": "unable to retrieve"}


@app.route("/events/<date>/<email_id>", methods=["GET"])
def get_events_by_date_email(date, email_id):
    """
    all the events on the particular date and of a particular email_id are retrieved
    """
    try:
        timeMin = date[:10]+"T"+"00:00:00"+"+05:30"
        timeMax = date[:10]+"T"+"23:59:59"+"+05:30"
        events = events_by_date_email(service, timeMin, timeMax, email_id)
        events = format_event_object(events)

        return jsonify(events)
    except Exception:
        return {"status": "unable to retrieve"}


@app.route("/eventsrange/<start_date>/<end_date>", methods=["GET"])
def get_events_by_date_range(start_date, end_date):
    """
    all the events between particular dates are retrieved
    """
    try:
        events = events_by_date(service, start_date, end_date)
        events = format_event_object(events)

        return jsonify(events)
    except Exception:
        return {"status": "unable to retrieve"}
