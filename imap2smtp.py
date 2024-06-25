import argparse
import imaplib
import logging
import smtplib


def put_message(rfc8622_data, forward_to, server, username, password, smtp_port):
    with smtplib.SMTP(server, smtp_port) as smtp_server:
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(username, password)
        rfc8622_data = rfc8622_data.replace(b'\r\nSubject: ', b'\r\nSubject: [NOT FOUND] ')
        smtp_server.sendmail(username, forward_to, rfc8622_data)


def transfer_messages(server, username, password, imap_inbox, forward_to, imap_port, smtp_port,
                      imap_timeout=120, only_flagged=True, **kwargs):
    account_imap = imaplib.IMAP4(server, imap_port, timeout=imap_timeout)
    account_imap.login(username, password)
    if kwargs['verbose']:
        for inbox in account_imap.list()[1]:
            logging.debug('Listing folders: %s', inbox)
    for inbox in imap_inbox:
        account_imap.select(inbox)
        logging.debug('Searching IMAP inbox %s for %s messages ...', inbox, 'flagged' if only_flagged else 'all')
        status, messages = account_imap.search(None, '(FLAGGED)' if only_flagged else '(ALL)')
        if status != 'OK':
            raise Exception('Could not get messages from IMAP at %s', inbox)
        messages = messages[0].split()
        logging.debug('Iterating %s %s messages ...', len(messages), 'flagged' if only_flagged else 'all')
        for num in messages:
            status, data = account_imap.fetch(num, '(RFC822 BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            if status != 'OK':
                raise Exception('Could not get properties from message %s in %s', num, inbox)

            rfc822_data = data[0][1]
            message_id = data[1][1].strip()
            logging.info('Forwarding %s in %s via SMTP', message_id, inbox)
            put_message(rfc822_data, forward_to, server, username, password, smtp_port)

            logging.info('Removing flag from %s', message_id)
            status, _ = account_imap.store(num, '-FLAGS', '(\\Flagged)')
            if status != 'OK':
                raise Exception('Could not remove flagged for message %s in %s', num, inbox)
    account_imap.close()
    account_imap.logout()


def parse_command_line():
    parser = argparse.ArgumentParser(description='Forward message from an IMAP inbox/folder via SMTP')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='be very verbose')
    group.add_argument('-q', '--quiet', action='store_true', help='no logging except errors')

    parser.add_argument('--server', required=True, help='IMAP/SMTP server name')
    parser.add_argument('--username', required=True, help='IMAP/SMTP username')
    parser.add_argument('--password', required=True, help='IMAP/SMTP password')
    parser.add_argument('--imap-port', type=int, default=143, help='IMAP server port')
    parser.add_argument('--smtp-port', type=int, default=587, help='SMTP server port')
    parser.add_argument('--imap-inbox', required=True, action='append',
                        help='IMAP Inbox, e.g. "INBOX.folder A.sub folder B"')

    parser.add_argument('--forward-to', required=True, help='Email address to forward to')

    return parser.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(module)s %(levelname)s %(message)s')
    formatter = logging.Formatter('%(asctime)s %(module)s %(levelname)s %(message)s')
    fileHandler = logging.FileHandler('imap2smtp.log', mode='a')
    fileHandler.setFormatter(formatter)
    logging.getLogger().addHandler(fileHandler)
    arguments = parse_command_line()
    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if arguments.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    logging.debug('Start transfer of messages ...')
    transfer_messages(**arguments.__dict__)
    logging.debug('Completed.')
