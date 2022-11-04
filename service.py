import datetime
import pickle
import os.path
import json
from flask import jsonify

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

theclassicART = "msitprogram.net_ag1jsv1tkepjhp326dj2eqi1ps@group.calendar.google.com"


def get_credentials():
    """
    The file token.pickle stores the user's access and refresh tokens, and is
    created automatically when the authorization flow completes for the first
    time.
    If there are no (valid) credentials available, let the user log in.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def create_service(creds):
    """
    creates a service
    """
    service = build('calendar', 'v3', credentials=creds)
    return service


def format_single_event_object(event):
    """
    creates a response event object for single event
    necessary details of the event are returned
    """
    event_obj = {}
    attendees = []
    for aten in event["attendees"]:
        temp = {}
        temp["checkedIn"] = aten["comment"]
        temp["status"] = "busy" if aten["responseStatus"] == "accepted" else "free"
        temp["email"] = aten["email"].replace("+event", "")
        attendees.append(temp)

    event_obj["attendees"] = attendees
    event_obj["start"] = event["start"]
    event_obj["end"] = event["end"]
    event_obj["description"] = event["description"]
    event_obj["id"] = event["id"]
    event_obj["summary"] = event["summary"]
    event_obj["eventType"] = event["extendedProperties"]["private"]["eventType"]
    event_obj["lastUpdated"] = event["updated"]
    event_obj["created"] = event["created"]
    event_obj["eventStatus"] = event["status"]
    event_obj["location"] = event["location"]
    return event_obj


def format_event_object(events):
    """
    necessary details of the event are returned
    """
    all_the_events = []
    for event in events:
        event_obj = {}
        event_obj = format_single_event_object(event)
        all_the_events.append(event_obj)
    return all_the_events


def get_events(service):
    """
    only the events which are present in the calendar are retrieved,
    events which are deleted from the calendar will not be shown.
    """
    # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events = service.events().list(calendarId=theclassicART).execute()
    events = events.get('items', [])
    return events


def assign_status(cur_event):
    attendess = []
    for aten in cur_event["attendees"]:
        email = aten["email"]
        index = email.index("@")
        temp = {}
        temp["comment"] = "no"
        temp["email"] = email[0:index]+"+event"+email[index:]
        temp["responseStatus"] = "accepted" if cur_event["attendeeStatus"] == "busy" else "declined"
        attendess.append(temp)
    cur_event["attendees"] = attendess
    return cur_event


def event_object_change(cur_event):
    """
    creates a event object
    """
    program = ["classes", "assignment", "orientation",
               "viva", "quiz", "mentor", "training", "assessment", "test", "exam", "program"]
    personal = ["personal", "placementpractice"]
    if cur_event["eventType"] in personal:
        temp = {"eventType": cur_event["eventType"]}
        private = {"private": temp}
        cur_event["extendedProperties"] = private

    elif cur_event["eventType"] in program:
        temp = {"eventType": cur_event["eventType"]+" "+"program"}
        private = {"private": temp}
        cur_event["extendedProperties"] = private
    elif cur_event["eventType"] == "leave":
        temp = {"eventType": "leave"}
        private = {"private": temp}
        cur_event["extendedProperties"] = private

    elif cur_event["eventType"] == "placementdrive":
        temp = {"eventType": "placementdrive"}
        private = {"private": temp}
        cur_event["extendedProperties"] = private
    del cur_event["eventType"]
    cur_event = assign_status(cur_event)
    return cur_event


def create_event(service, cur_event):
    """
    to create the event
    """

    cur_event = event_object_change(cur_event)

    created_event = service.events().insert(
        calendarId=theclassicART, body=cur_event).execute()
    return created_event


def event_by_id(service, event_id):
    """
    event of a particular event_id are retrieved
    """
    event_by_id = service.events().get(
        calendarId=theclassicART, eventId=event_id).execute()

    return event_by_id


def all_events(service):
    """
    all the events are retrieved
    """
    events = service.events().list(calendarId=theclassicART).execute()
    events = events.get('items', [])

    return events


def conflict_events(service, cur_event):
    """
    checks for the conflict before an event is created
    """

    program = ["classes program", "assignment program", "orientation program", "viva program", "quiz program", "mentor program",
               "training program", "assessment program", "test program", "exam program", "program program", "placementdrive"]

    cur_event = event_object_change(cur_event)
    timeMin = cur_event["start"]["dateTime"]
    timeMax = cur_event["end"]["dateTime"]
    events = events_by_date(service, timeMin, timeMax)
    conflicts = []
    is_program = cur_event["extendedProperties"]["private"]["eventType"] in program
    for event in events:
        dc = date_conflict(event, cur_event)
        ac = attendees_conflict(event, cur_event)
        avail = 100 - len(ac) / len(event["attendees"]) * 100
        if dc and len(ac) != 0:
            room = "no"
            eventType = event["extendedProperties"]["private"]["eventType"]
            if is_program and event["location"] == cur_event["location"]:
                room = "yes"
            temp = {"status": "conflict", "availability": avail, "notavailablepersons": ",".join(ac),
                    "eventId": event["id"], "eventType": eventType, "roomConflict": room}
            conflicts.append(temp)
        else:
            room = "no"
            eventType = event["extendedProperties"]["private"]["eventType"]
            if is_program and event["location"] == cur_event["location"]:
                room = "yes"
                temp = {"status": "conflict", "availability": avail, "notavailablepersons": ",".join(ac),
                        "eventId": event["id"], "eventType": eventType, "roomConflict": room}
                conflicts.append(temp)

    return conflicts


def date_conflict(event, cur_event):
    """
    if a person is a part of two events true is returned
    else false is returned
    """

    event_start_time = datetime.datetime.strptime(
        event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
    event_end_time = datetime.datetime.strptime(
        event['end']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
    cur_event_start_time = datetime.datetime.strptime(
        cur_event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
    cur_event_end_time = datetime.datetime.strptime(
        cur_event['end']['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
    if (cur_event_start_time >= event_start_time and cur_event_start_time < event_end_time) or (cur_event_end_time <= event_start_time and cur_event_end_time > event_start_time):
        return True
    return False


def attendees_conflict(event, cur_event):
    """
    persons who are a part of two events are returned
    """

    event_emails = set()
    cur_event_emails = set()
    if 'attendees' in event:
        for aten in event['attendees']:
            if aten["responseStatus"] == "accepted":
                event_emails.add(aten['email'].replace("+event", ""))
    if 'attendees' in cur_event:
        for aten in cur_event['attendees']:
            cur_event_emails.add(aten['email'].replace("+event", ""))
    return event_emails.intersection(cur_event_emails)


def events_by_email(service, email_id):
    """
    all the events which the user is a part of are retrieved
    using emailId
    """
    all_events = get_events(service)
    events_by_email_id = []
    index = email_id.index("@")
    email_id = email_id[0:index]+"+event"+email_id[index:]
    for event in all_events:
        if "attendees" in event:
            attendees = event['attendees']
            for att in attendees:
                if email_id == att['email']:
                    events_by_email_id.append(event)

    return events_by_email_id


def events_by_date(service, timeMin, timeMax):
    """
    all the events on the particular date are retrieved
    """
    events = service.events().list(
        calendarId=theclassicART, timeMin=timeMin, timeMax=timeMax).execute()
    events = events.get('items', [])

    return events


def deleted_events(service):
    """
    all the events which are deleted from calendar are retrieved
    """
    events = service.events().list(
        calendarId=theclassicART, showDeleted=True).execute()
    events = events.get('items', [])
    deleted_events = []

    for event in events:
        if event["status"] == "cancelled":
            deleted_events.append(event)

    return deleted_events


def event_update(service, event, event_id, status):
    """
    to update the event
    """
    if len(status) == 0:
        updated_event = service.events().update(calendarId=theclassicART,
                                                eventId=event_id, body=event).execute()
        updated_event = format_event_object(updated_event)
        return updated_event
    else:
        conflicts = []
        for eve in status:
            if event_id == eve["event_id"] and len(status) == 1:
                updated_event = service.events().update(calendarId=theclassicART,
                                                        eventId=event_id, body=event).execute()
                updated_event = format_single_event_object(updated_event)
                return updated_event
            else:
                avail = 100 - len(eve["attendees"]
                                  [:-1].split(",")) / len(event["attendees"]) * 100
                temp = {"availability": avail,
                        "notavailablestudents": eve["attendees"], "eventType": eve["eventType"]}
                conflicts.append(temp)

        return jsonify(conflicts)


def available_students(service, event):
    """
    available students are returned
    """
    available = conflict_events(service, event)
    if len(available) == 0:
        return {"availability": "100"}
    else:
        return available


def events_by_date_email(service, timeMin, timeMax, email_id):
    """
    all the events on the particular date and of a particular email_id are retrieved
    """
    events = events_by_date(service, timeMin, timeMax)
    events_by_date_and_email_id = []
    for event in events:
        if "attendees" in event:
            attendees = event['attendees']
            for att in attendees:
                if email_id == att['email'].replace("+event", ""):
                    events_by_date_and_email_id.append(event)

    return events_by_date_and_email_id


if __name__ == '__main__':
    pass
