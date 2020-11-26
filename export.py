import argparse
import os
import re
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta


def get_cli_args():
    parser = argparse.ArgumentParser(description='Export endomondo workouts')

    parser.add_argument('--login', '-l', required=True, help='Login/email to endmondo account')
    parser.add_argument('--password', '-p', required=True, help='password to endmonodo account')
    parser.add_argument('--from_date', '-f', type=lambda d: datetime.fromisoformat(d),
                        help='date from (YYYY-MM-DD HH:mm:SS) - default 2010-01-01', default=datetime.fromisocalendar(2010, 1, 1))
    parser.add_argument('--to_date', '-t', type=lambda d: datetime.fromisoformat(d),
                        help='date from (YYYY-MM-DD HH:mm:SS) - default now', default=datetime.now())
    parser.add_argument('--format', default='TCX', choices=['TCX', 'GPX'], help='format to export')
    parser.add_argument('--export_dir', default='export', help='export directory')
    return parser.parse_args()


def get_filename_from_response(response):
    cd = wr.headers.get('content-disposition')
    fname = re.findall('filename="(.+)"', cd)
    filename=fname[0]
    invalid = '<>:"/\|?* '
    for char in invalid:
        filename = filename.replace(char, ' ')
    return filename


def validate_response(response):
    if not response.ok:
        print("Error: " + response.reson)
        print("       " + response.text)
        print("URL:   " + response.url)
        exit()


if __name__ == "__main__":
    arguments = get_cli_args()

    if not os.path.exists(arguments.export_dir):
        os.makedirs(arguments.export_dir)

    session = requests.Session()
    print("Login into endomondo.")
    response = session.post('https://www.endomondo.com/rest/session', json=
    {"email": arguments.login, "password": arguments.password, "remember": False}
                            )
    validate_response(response)
    user_id = response.json()['id']
    workouts_url = f'https://www.endomondo.com/rest/v1/users/{user_id}/workouts'
    current_date = arguments.to_date
    while current_date > arguments.from_date:
        before_date = current_date - relativedelta(months=1)
        print("Fetch workouts from - to: " + before_date.isoformat() + " " + current_date.isoformat())

        workouts = session.get(workouts_url,
                               params={"before": current_date.isoformat(), "after": before_date.isoformat()})
        validate_response(workouts)
        print("Export workouts")
        for workout in workouts.json():
            workout_id = workout["id"]
            workout_export_url = f'https://www.endomondo.com/rest/v1/users/{user_id}/workouts/{workout_id}/export?format={arguments.format}'
            wr = session.get(workout_export_url)
            validate_response(wr)
            with open(os.path.join(arguments.export_dir, get_filename_from_response(wr)), 'wb') as f:
                print("Export: " + f.name)
                f.write(wr.content)
        current_date = before_date
