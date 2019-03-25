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
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

from slugify import slugify

usb_drive_root = Path('/') / 'run' / 'media' / 'standa' / 'KINGSTON'
vinted_labels = Path('!imprimir')
vinted_labels_expired = Path('vinted_labels_expired')
vinted_labels_used = Path('vinted_labels_used')


def get_labels(user_name, password):
    imap_session = get_gmail_imap_session(password, user_name)
    email_uids = search_keywords(imap_session)

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
            search_new_labels(date, email_uid, part, sender, subject)

        # after one parsed email, send one confirmation email
        # TODO: temporarily disabled:
        # send_confirmation(password, sender, pdf_files, user_name)
        delete_mail(email_uid, imap_session)
    log_out(imap_session)
    # TODO: temporarily disabled:
    # repeat(password, user_name)


def search_new_labels(date, email_uid, part, sender, subject):
    label_expiration_date = datetime.strptime(subject[-16:], '%d/%m/%Y %H:%M')
    today = datetime.now()
    if label_expiration_date > today:
        get_body(date, email_uid, part, sender)
        get_attached_pdf(part, subject)


def get_gmail_imap_session(password, user_name):
    # instantiate IMAP4 protocol that connects over an SSL
    print('\nLogging in the gmail account...')
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
    imap_session.select('INBOX', readonly=False)
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
        header_text = f'\nMessage with UID {uid_decoded} from {sender}, received on {date}:\n'
        print('START MESSAGE'.center(len(header_text), '-'),
              header_text,
              f'\n\t{part.get_payload(decode=True).decode(encoding="utf-8")}\n')


def get_attached_pdf(part, subject):
    file_name = part.get_filename()
    if file_name and file_name.lower().endswith('.pdf'):
        payload = part.get_payload(decode=True)  # decode to get bytes-like object (False returns a string)
        print(f'\n\tRetrieving: {file_name}')
        new_file_name = rename_pdf(subject, file_name)
        save_pdf(new_file_name, payload)


def rename_pdf(subject, file_name):
    # create a folder to store pdf files
    subject_suff = subject[-16:]
    new_file_name = slugify(subject_suff) + '_' + file_name.split('-')[-1]
    return new_file_name


def save_pdf(new_file_name, payload):
    pdf_path = usb_drive_root / vinted_labels / new_file_name
    with pdf_path.open(mode='wb') as fp:
        fp.write(payload)
    print(f'\n\tSaving as "{new_file_name}"\n')


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
        msg['Subject'] = 'PDF file(s) of Vinted downloaded'
        smtp_session.sendmail(usr_gmail, [sender], msg.as_string())
        smtp_session.quit()
        print('\tDone.')


def delete_mail(email_uid, imap_session):
    imap_session.store(email_uid, '+FLAGS', '\\Deleted')  # Deletes the mail completely on Gmail.
    uid_decoded = email_uid.decode('ascii')
    print(f'\n\tEmail with UID {uid_decoded} was deleted.')


def log_out(imap_session):
    print('\n\tLogging out.\n')
    imap_session.close()
    time.sleep(.5)
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


def move_away_expired_labels():
    print(f'\nExpired labels are going to be moved to "{vinted_labels_expired.name}" folder.\n')

    vinted_labels_expired_folder, vinted_labels_folder, _ = create_folders_if_not_exist()

    for pdf in vinted_labels_folder.glob('*.pdf'):
        try:
            pdf_date = datetime.strptime(pdf.name[:10], '%d-%m-%Y')
            today = datetime.now()
            if pdf_date < today:
                pdf.replace(Path(vinted_labels_expired_folder) / pdf.name)
        except ValueError:
            print(f'\tWARNING: Date could not be parsed from a PDF file "{pdf.name}"\n')


def move_away_existing_labels():
    _, vinted_labels_folder, vinted_labels_used_folder = create_folders_if_not_exist()

    for pdf in vinted_labels_folder.glob('*.pdf'):
        print(f'\tMoving "{pdf.name}" to "{vinted_labels_used_folder.name}"')
        pdf.replace(Path(vinted_labels_used_folder) / pdf.name)


def create_folders_if_not_exist():
    # /run/media/standa/KINGSTON/vinted_labels_expired
    vinted_labels_expired_folder = usb_drive_root / vinted_labels_expired
    Path(vinted_labels_expired_folder).mkdir(exist_ok=True)
    # /run/media/standa/KINGSTON/!imprimir
    vinted_labels_folder = usb_drive_root / vinted_labels
    Path(vinted_labels_folder).mkdir(exist_ok=True)
    # /run/media/standa/KINGSTON/vinted_labels_used
    vinted_labels_used_folder = usb_drive_root / vinted_labels_used
    Path(vinted_labels_used_folder).mkdir(exist_ok=True)

    return vinted_labels_expired_folder, vinted_labels_folder, vinted_labels_used_folder


if __name__ == '__main__':
    user_name_input = input('Enter your GMail username: ')
    password_input = input('Enter your password: ')
    # password_input = getpass.getpass('Enter your password: ')
    move_away_expired_labels()
    answer = input(f'Move non-expired labels from "{vinted_labels.name}" to "{vinted_labels_used.name}"? y/n:\n')
    if answer == 'y':
        move_away_existing_labels()
    get_labels(user_name_input, password_input)
