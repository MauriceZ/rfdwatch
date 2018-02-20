import click
import os
import sendgrid
import sqlite3
import time
import urllib.request
from bs4 import BeautifulSoup
from sendgrid.helpers.mail import *


HOURS_TO_STORE = 24
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rfdwatch.db')

def hours_to_seconds(hours):
    return hours * 3600


def get_matching_keyword(s, keywords):
    for k in keywords:
        if k.lower() in s.lower():
            return k

    return None


def send_alert(keyword, topic_link, email):
    title = topic_link.get_text().strip()
    link = 'https://forums.redflagdeals.com' + topic_link.get('href')
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    from_email = Email(email)
    to_email = Email(email)
    subject = 'RFDWatch – Match for keyword "{}" found!'.format(keyword)
    content = Content('text/html', 'RFD Link: <a href="{}">{}</a>'.format(link, title))
    mail = Mail(from_email, subject, to_email, content)

    response = sg.client.mail.send.post(request_body=mail.get())
    print('Email sent to {}'.format(email))
    print(response.status_code)
    print(response.body)
    print(response.headers)


def db_contains(keyword, url_path, db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''SELECT count(*) FROM matches WHERE keyword = ? AND url_path = ?''', (keyword, url_path))
    contains = cursor.fetchone()[0] > 0
    conn.close()

    return contains


def store_match(keyword, url_path, db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.execute('''INSERT INTO matches(keyword, url_path, timestamp) VALUES (?, ?, ?)''', (keyword, url_path, int(time.time())))
    conn.commit()
    conn.close()


@click.group()
def cli():
    pass


@cli.command('setupdb')
@click.option('--path', '-p', default=DEFAULT_DB_PATH)
def setup_db(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE matches (keyword text, url_path text, timestamp integer)''')
    conn.commit()
    conn.close()
    print("DB created at {}".format(DEFAULT_DB_PATH))


@cli.command('cleandb')
@click.option('--path', '-p', default=DEFAULT_DB_PATH)
@click.option('--hours', '-h', default=12)
def clean_db(path, hours):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    oldest_time = int(time.time()) - hours_to_seconds(hours)
    n = cursor.execute('''DELETE FROM matches WHERE timestamp <= ?''', (oldest_time,)).rowcount
    conn.commit()
    conn.close()

    if n > 0:
        print("{} matches deleted".format(n))


@cli.command('watch')
@click.argument('email')
@click.argument('keywords') # space delimited
@click.pass_context
def rfdwatch(ctx, email, keywords):
    ctx.invoke(clean_db)

    rfd_soup = BeautifulSoup(urllib.request.urlopen("https://forums.redflagdeals.com/hot-deals-f9/").read(), "html.parser")
    topic_links = rfd_soup.select('.topiclist .topic_title_link')

    for topic_link in topic_links:
        title = topic_link.get_text().strip()

        matching_keyword = get_matching_keyword(title, keywords.split())

        if matching_keyword is not None and not db_contains(matching_keyword, topic_link.get('href')):
            print('keyword "{}" found, sending alert email to {}'.format(matching_keyword, email))
            send_alert(matching_keyword, topic_link, email)
            store_match(matching_keyword, topic_link.get('href'))


if __name__ == '__main__':
    cli()
