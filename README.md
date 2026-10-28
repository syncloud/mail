# mail
Syncloud mail, contacts and calendars based on [Stalwart](https://stalw.art) and the [Bulwark](https://bulwarkmail.org) webmail

- Stalwart (from the [cyberb/stalwart](https://github.com/cyberb/stalwart) `syncloud` branch) serves SMTP, IMAP, POP3, ManageSieve, JMAP, CalDAV and CardDAV, authenticates against the platform LDAP and has its admin interface at `/admin`.
- Bulwark is the webmail at `/`, talking JMAP to Stalwart.
- nginx joins both behind `$SNAP_COMMON/web.socket`; everything internal is a Unix socket.

## Configuration

Stalwart keeps its settings in its own database. The install and post-refresh hooks start it in recovery mode and apply them through the API (`cli/stalwart/provisioner.go`), so there are no config files to edit on a device; use `/admin` or change the provisioner.

## Upgrading from the Postfix/Dovecot/Roundcube snap

The `migrate` service imports every maildir under `$SNAP_DATA/box` and the Roundcube contacts from the pre-refresh database dump, then writes `$SNAP_DATA/migration/done`. It resumes where it stopped, and the old maildirs are left in place.
