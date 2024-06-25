# Usage

Just follow the given help:
```
python imap2ews.py -h

usage: imap2ews.py [-h] [-v | -q] [--echo-ews] 
                   --imap-server IMAP_SERVER
                   [--imap-port IMAP_PORT] 
                   --imap-username IMAP_USERNAME
                   --imap-password IMAP_PASSWORD 
                   --imap-inbox IMAP_INBOX
                   --ews-server EWS_SERVER 
                   --ews-primary-smtp-address EWS_PRIMARY_SMTP_ADDRESS 
                   --ews-username EWS_USERNAME
                   --ews-password EWS_PASSWORD
                   
python imap2ews.py -h

usage: imap2smtp.py [-h] [-v | -q] --server SERVER --username USERNAME --password PASSWORD [--imap-port IMAP_PORT] [--smtp-port SMTP_PORT] --imap-inbox IMAP_INBOX --forward-to
                    FORWARD_TO

Forward message from an IMAP inbox/folder via SMTP

options:
  -h, --help               show this help message and exit
  -v, --verbose            be very verbose
  -q, --quiet              no logging except errors
  --server SERVER          IMAP/SMTP server name
  --username USERNAME      IMAP/SMTP username
  --password PASSWORD      IMAP/SMTP password
  --imap-port IMAP_PORT    IMAP server port
  --smtp-port SMTP_PORT    SMTP server port
  --imap-inbox IMAP_INBOX  IMAP Inbox, e.g. "INBOX.folder A.sub folder B"
  --forward-to FORWARD_TO  Email address to forward to
´´´
