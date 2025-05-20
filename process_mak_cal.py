#!/usr/bin/env python3
from ics import Calendar, Event
from datetime import datetime, timedelta
import requests
import pytz
import sys
import os


def process_ics_file(input_file, output_file, timezone_str, after_date=None):
    # Load the time zone
    target_timezone = pytz.timezone(timezone_str)

    # Map from calendar event uid to repeating rule string. python ics does not handle these natively
    rrule_from_uid = {}
    # Read the .ics file
    with open(input_file, 'r') as file:
        # Make a mapping from uuid to repeating rule
        for line in file.readlines():
            if line.startswith("END:VEVENT"):
                assert uid is not None
                rrule_from_uid[uid] = rrule
                uid = None
                rrule = None
            if line.startswith("UID:"):
                uid = line[4:-1]
            if line.startswith("RRULE:"):
                rrule = line[:-1]

    # Prepare a new calendar for filtered events
    new_calendar = Calendar()

    with open(input_file, 'r') as file:
        calendar = Calendar(file.read())

    for event in calendar.events:
        # Filter events with the specified keywords
        if after_date is not None:
            # Convert event begin time to the target timezone
            event_begin_local = event.begin.astimezone(target_timezone)
            # Check if the event is after the specified date
            if event_begin_local < after_date:
                continue
        if any(keyword in event.name for keyword in ["Call", "Education", "Evolve", "Project", "DAC", "ALPS"]):
            # Convert event to the target timezone
            event_begin_local = event.begin.astimezone(target_timezone)
            event_end_local = event.end.astimezone(target_timezone)

            # Create a new all-day event
            new_event = Event()
            new_event.name = event.name
            new_event.begin = event_begin_local.date()  # Convert to date for all-day event
            new_event.make_all_day()  # Ensure it's a full-day event
            new_event.uid = event.uid
            new_calendar.events.add(new_event)

    # Write the new calendar to a file
    with open(output_file, 'w') as file:
        for line in new_calendar.serialize_iter():
            file.write(line)
            # inject repeating rules manually as they cannot be handled by the ics python library
            if line.startswith("UID:"):
                uid = line[4:-2]
                rrule = rrule_from_uid[uid]
                if rrule is not None:
                    file.write(rrule)
                    file.write('\n')

def download_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"File {filename} downloaded successfully from {url}")
    else:
        print(f"Failed to download from {url}. Status code: {response.status_code}")
# Example usage

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 process_make_cal.py [output_file_name] [after_date (mm/dd/yyyy)]")
        exit(-1)
    makela_calendar_url="https://www.amion.com/cgi-bin/ocs?Vcal=7.1641&Lo=resident%40su&Jd=10393"
    calendar_file="resident_su1641.ics"
    download_file(makela_calendar_url, calendar_file)
    timezone_str = "America/Los_Angeles"  # Replace with your target timezone
    output_file = sys.argv[1]
    # Parse the after_date parameter from mm/dd/yyyy format
    date_str = sys.argv[2]
    after_date = datetime.strptime(date_str, '%m/%d/%Y')
    # Make the date timezone-aware by setting it to the target timezone
    after_date = pytz.timezone(timezone_str).localize(after_date)
    process_ics_file(calendar_file, output_file, timezone_str, after_date)
    os.remove(calendar_file)
    print(f"Calendar successfully filtered and saved to {output_file}.") 
    print(f"Import the {output_file} in into apple calendar, google calendar is not working")
