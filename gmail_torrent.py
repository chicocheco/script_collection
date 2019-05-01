#! python3
# gmail_torrent.py - Remotely command to download torrents in qbittorrent via email.
# Set up qbittorrent to start downloading a '.torrent' file right away, without asking for more.

import email
import sys
import getpass
import imaplib
import os
import smtplib
import subprocess
import time
from collections import namedtuple
from email.mime.text import MIMEText

EmailData = namedtuple('EmailData', 'date sender')


def email_torrent(user_name, password):

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

    # Search for emails with "torrent" in the subject field.
    imap_session.select('INBOX', readonly=False)
    # TODO: keys = ('torrent', 'torent', 'tor', 'tr')
    search_key = 'torrent'
    result, email_data = imap_session.search(None, f'(SUBJECT {search_key})')

    # Get a list of their UIDs.
    email_uids = email_data[0].split()
    emails_found = len(email_uids)

    if emails_found > 0:
        print(f'Found {emails_found} emails with subject "{search_key}":')
    else:
        print(f'No emails with subject "{search_key}" were found.')

    torr_files = []
    # fetch each UID's entire raw message.
    for email_uid in email_uids:
        result, email_data = imap_session.fetch(email_uid, '(RFC822)')

        email_body = email.message_from_bytes(email_data[0][1])

        date = None
        sender = None
        # walk all parts of the raw message in one email
        for part in email_body.walk():
            if part.get('Date'):
                date = (email.utils.parsedate_to_datetime(part.get('Date'))).strftime('%A, %d.%m.%Y, %H:%M')
            if part.get('From'):
                sender = part.get('From')  # TODO: what if this receives nothing??
            text_included = part.get_content_type() == 'text/plain'
            if text_included:
                uid_decoded = email_uid.decode('ascii')
                print(f'Message with UID {uid_decoded} from {sender}, received on {date}:'
                      f'\n\t{part.get_payload(decode=False)}')

            file_name = part.get_filename()
            if file_name:
                payload = part.get_payload(decode=True)  # Decode to get bytes-like object (False returns a string)
                print('\n\tRetrieving: ' + file_name)
                with open(file_name, 'wb') as fp:
                    fp.write(payload)
                print('\tOpening in qbittorrent... ')
                new_file_name = os.path.abspath(file_name)
                torr_files.append(file_name)
                qbittorrent = subprocess.Popen(['qbittorrent', new_file_name])
                time.sleep(2)
                if qbittorrent.poll() is None:
                    print('\n\tDownloading...')
                    time.sleep(1)

        # after one parsed email, send one confirmation email
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
                           f'The following file(s) have been accepted and processed to download:\n\t{tf_string}\n\n'
                           f'Have a nice day,\nyour Python Robot')
            msg['To'] = email.utils.formataddr(('', sender))
            msg['From'] = email.utils.formataddr(('Python Robot', usr_gmail))
            msg['Subject'] = 'Torrent file(s) accepted and processed to download'
            smtp_session.sendmail(usr_gmail, [sender], msg.as_string())
            smtp_session.quit()
            print('\tDone.')

        imap_session.store(email_uid, '+FLAGS', '\\Deleted')  # Deletes the mail completely on Gmail.
        uid_decoded = email_uid.decode('ascii')
        print(f'\n\tEmail with UID {uid_decoded} was deleted.')

    print('\n\tLogging out.\n')
    imap_session.close()
    imap_session.logout()

    # Wait 15 minutes and repeat.
    for minute in range(-15, -2):
        print(f'Re-checking the mailbox in {abs(minute)} minutes.')
        time.sleep(60)
    else:
        print(f'Re-checking the mailbox in 1 minute.\n')
        time.sleep(60)

    print('Re-checking the mailbox now...\n')
    email_torrent(user_name, password)


if __name__ == '__main__':
    user_name = input('Enter your GMail username: ')
    password = input('Enter your password: ')
    # password = getpass.getpass('Enter your password: ')
    email_torrent(user_name, password)
