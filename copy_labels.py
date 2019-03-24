"""
- plug in the USB stick first...

- log in to a gmail account - done
- search for emails with a particular subject or containing pdfs that can be securely identified - done
- download them - done
- rename each file to consist of a last date the package has to be sent (retrieve the date from the PDF name
or subject name or email body) - done
- on the USB stick, place all previous labels to a label "old" or "used" within "!imprimir" and IF a particular pdf
label consist of a date that has passed, delete it
- copy the new label pdfs to a folder, being named properly
- unmout the USB stick



"""

# ! python3
# gmail_torrent.py - Remotely command to download torrents in qbittorrent via email.
# Set up qbittorrent to start downloading a '.torrent' file right away, without asking for more.

import email
# import getpass
import imaplib
import os
import smtplib
import subprocess
from pathlib import Path
import sys
import time
from collections import namedtuple
from email.mime.text import MIMEText

from slugify import slugify
EmailData = namedtuple('EmailData', 'date sender')


def get_labels(user_name, password):
    imap_session = get_gmail_imap_session(password, user_name)
    email_uids = search_keywords(imap_session)

    pdf_files = []
    # fetch each UID's entire raw message.
    for email_uid in email_uids:
        result, email_data = imap_session.fetch(email_uid, '(RFC822)')
        email_body = email.message_from_bytes(email_data[0][1])

        date = None
        sender = None
        subject = None
        # walk all parts of the raw message in one email
        for part in email_body.walk():
            date, sender, subject = get_metadata(date, part, sender, subject)
            get_body(date, email_uid, part, sender)
            get_attached_pdf_file(part, subject)

        # after one parsed email, send one confirmation email
        send_confirmation(password, sender, pdf_files, user_name)
        # delete_mail(email_uid, imap_session)
    logout(imap_session)
    repeat(password, user_name)


def get_gmail_imap_session(password, user_name):
    # instantiate IMAP4 protocol that connects over an SSL
    imap_session = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        result, account_details = imap_session.login(user_name, password)
    except imaplib.IMAP4.error:
        print('Invalid credentials!')
        sys.exit()
    if result != 'OK':
        print('Not able to sign in!')
        sys.exit()
    else:
        print('Login status: ' + result)
    return imap_session


def search_keywords(imap_session):
    # Search for emails with "torrent" in the subject field.
    imap_session.select('INBOX', readonly=True)
    # TODO: keys = ('torrent', 'torent', 'tor', 'tr')
    search_key = 'Utilizar+antes+del'
    result, email_data = imap_session.search(None, f'(SUBJECT {search_key})')
    # Get a list of their UIDs.
    email_uids = email_data[0].split()
    emails_found = len(email_uids)
    if emails_found > 0:
        print(f'Found {emails_found} emails with subject "{search_key}":')
    else:
        print(f'No emails with subject "{search_key}" were found.')
    return email_uids


def get_metadata(date, part, sender, subject):
    if part.get('Date'):
        date = (email.utils.parsedate_to_datetime(part.get('Date'))).strftime('%A, %d.%m.%Y, %H:%M')
    if part.get('From'):
        sender = part.get('From')
    if part.get('Subject'):
        subject = email.header.decode_header(part.get('Subject'))[0][0].decode('utf-8')
    return date, sender, subject


def get_body(date, email_uid, part, sender):
    text_included = part.get_content_type() == 'text/plain'
    if text_included:
        uid_decoded = email_uid.decode('ascii')
        # TODO: fix formatting
        print(70 * '-', 'START MESSAGE', 70 * '-',
              f'\nMessage with UID {uid_decoded} from {sender}, received on {date}:\n',
              f'\n\t{part.get_payload(decode=True).decode(encoding="utf-8")}\n')


def get_attached_pdf_file(part, subject):
    file_name = part.get_filename()
    if file_name and file_name.lower().endswith('.pdf'):
        payload = part.get_payload(decode=True)  # Decode to get bytes-like object (False returns a string)
        print(f'\n\tRetrieving: {file_name} \n')

        # create a folder to store pdf files
        Path('pdf_files').mkdir(exist_ok=True)
        subject_suff = subject[-35:]
        new_file_name = slugify(subject_suff) + '.pdf'

        pdf_path = Path('pdf_files') / Path(new_file_name)
        with pdf_path.open(mode='wb') as fp:
            fp.write(payload)


def send_confirmation(password, sender, torr_files, user_name):
    if torr_files:
        print('\n\tSending confirmation email back to the sender...')
        tf_string = '\n\t'.join(torr_files)
        torr_files.clear()
        smtp_session = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_session.ehlo()
        smtp_session.starttls()
        smtp_session.login(user_name, password)
        usr_gmail = user_name + '@gmail.com'
        msg = MIMEText(f'Hi!\n\n'
                       f'The following file(s) have been downloaded:\n\t{tf_string}\n\n'
                       f'Have a nice day,\nyour Python Robot')
        msg['To'] = email.utils.formataddr(('', sender))
        msg['From'] = email.utils.formataddr(('Python Robot', usr_gmail))
        msg['Subject'] = 'PDF file(s) accepted and processed to download'
        smtp_session.sendmail(usr_gmail, [sender], msg.as_string())
        smtp_session.quit()
        print('\tDone.')


def delete_mail(email_uid, imap_session):
    imap_session.store(email_uid, '+FLAGS', '\\Deleted')  # Deletes the mail completely on Gmail.
    uid_decoded = email_uid.decode('ascii')
    print(f'\n\tEmail with UID {uid_decoded} was deleted.')


def logout(imap_session):
    print('\n\tLogging out.\n')
    imap_session.close()
    imap_session.logout()


def repeat(password, user_name):
    # Wait 15 minutes and repeat.
    for minute in range(-15, -2):
        print(f'Re-checking the mailbox in {abs(minute)} minutes.')
        time.sleep(60)
    else:
        print(f'Re-checking the mailbox in 1 minute.\n')
        time.sleep(60)
    print('Re-checking the mailbox now...\n')
    get_labels(user_name, password)


if __name__ == '__main__':
    user_name = input('Enter your GMail username: ')
    password = input('Enter your password: ')
    # password = getpass.getpass('Enter your password: ')
    get_labels(user_name, password)
