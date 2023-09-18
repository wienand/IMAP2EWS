import argparse
import datetime
import imaplib
import logging

import exchangelib

account_ews = None


class PidTagMessageFlags(exchangelib.ExtendedProperty):
    property_tag = 0x0E07
    property_type = 'Integer'


def put_message(rfc8622_data, ews_server, ews_username, ews_password, ews_primary_smtp_address, **_):
    global account_ews
    if account_ews is None:
        credentials = exchangelib.Credentials(username=ews_username, password=ews_password)
        config = exchangelib.Configuration(server=ews_server, credentials=credentials)
        account_ews = exchangelib.Account(primary_smtp_address=ews_primary_smtp_address,
                                          config=config, autodiscover=False,
                                          access_type=exchangelib.DELEGATE)
        exchangelib.Message.register("tag_message_flags", PidTagMessageFlags)

    message = exchangelib.Message(
        account=account_ews,
        folder=account_ews.inbox,
        mime_content=rfc8622_data,
        tag_message_flags=1
    )

    message.save()


def transfer_messages(imap_server, imap_username, imap_password, imap_inbox, imap_port=143, imap_timeout=120,
                      only_unseen=True, **kwargs):
    account_imap = imaplib.IMAP4(imap_server, imap_port, timeout=imap_timeout)
    account_imap.login(imap_username, imap_password)
    account_imap.select(imap_inbox)
    logging.debug('Searching IMAP inbox %s for %s messages ...', imap_inbox, 'unseen' if only_unseen else 'all')
    status, messages = account_imap.search(None, '(UNSEEN)' if only_unseen else '(ALL)')
    if status != 'OK':
        raise Exception('Could not get messages from IMAP at %s', imap_inbox)
    messages = messages[0].split()
    logging.debug('Iterating %s %s messages ...', len(messages), 'unseen' if only_unseen else 'all')
    for num in messages:
        status, data = account_imap.fetch(num, '(RFC822 BODY[HEADER.FIELDS (MESSAGE-ID)])')
        if status != 'OK':
            raise Exception('Could not get properties from message %s in %s', num, imap_inbox)

        rfc822_data = data[0][1]
        message_id = data[1][1].strip()
        logging.info('Transferring %s to EWS', message_id)
        put_message(rfc822_data, **kwargs)

        logging.debug('Marking %s as read', message_id)
        status, _ = account_imap.store(num, '+FLAGS', '(\\Seen)')
        if status != 'OK':
            raise Exception('Could not set seen flag for message %s in %s', num, imap_inbox)

    account_imap.close()
    account_imap.logout()


def main(args):
    transfer_messages(**args.__dict__)


def parse_command_line():
    parser = argparse.ArgumentParser(description='Transfer message from IMAP inbox/folder to EWS/Exchange mailbox')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='be very verbose')
    group.add_argument('-q', '--quiet', action='store_true', help='no logging except errors')
    parser.add_argument('--echo-ews', action='store_true', help='show debug from using EWS API')

    parser.add_argument('--imap-server', required=True, help='IMAP server name')
    parser.add_argument('--imap-port', type=int, default=143, help='IMAP server port')
    parser.add_argument('--imap-username', required=True, help='IMAP username')
    parser.add_argument('--imap-password', required=True, help='IMAP password')
    parser.add_argument('--imap-inbox', required=True, help='IMAP Inbox, e.g. "INBOX.folder A.sub folder B"')

    parser.add_argument('--ews-server', required=True, help='EWS server name')
    parser.add_argument('--ews-primary-smtp-address', required=True, help='EWS primary smtp address of mailbox')
    parser.add_argument('--ews-username', required=True, help='EWS username')
    parser.add_argument('--ews-password', required=True, help='EWS password')

    return parser.parse_args()


if __name__ == '__main__':
    startTimestamp = datetime.datetime.now()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(module)s %(levelname)s %(message)s')
    formatter = logging.Formatter('%(asctime)s %(module)s %(levelname)s %(message)s')
    fileHandler = logging.FileHandler('imap2ews.log', mode='a')
    fileHandler.setFormatter(formatter)
    logging.getLogger().addHandler(fileHandler)
    arguments = parse_command_line()
    if not arguments.echo_ews:
        logging.getLogger('exchangelib').setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("spnego").setLevel(logging.INFO)
        logging.getLogger("tzlocal").setLevel(logging.INFO)

    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if arguments.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    main(arguments)
