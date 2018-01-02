import click
import os
import sendgrid
import urllib.request
from bs4 import BeautifulSoup
from sendgrid.helpers.mail import *


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


@click.command()
@click.argument('email')
@click.argument('keywords') # space delimited
def rfdwatch(email, keywords):
    rfd_soup = BeautifulSoup(urllib.request.urlopen("https://forums.redflagdeals.com/hot-deals-f9/").read(), "html.parser")
    topic_links = rfd_soup.select('.topiclist .topic_title_link')

    for topic_link in topic_links:
        title = topic_link.get_text().strip()

        matching_keyword = get_matching_keyword(title, keywords.split())

        if matching_keyword is not None:
            print('keyword "{}" found, sending alert email to {}'.format(matching_keyword, email))
            send_alert(matching_keyword, topic_link, email)            


if __name__ == '__main__':
    rfdwatch()
