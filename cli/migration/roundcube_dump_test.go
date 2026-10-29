package migration

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

const dump = `--
-- PostgreSQL database dump
--

COPY public.users (user_id, username, mail_host, created, last_login, failed_login, failed_login_counter, language, preferences) FROM stdin;
1	alice	localhost	2026-10-27 10:00:00+00	\N	\N	\N	en_US	a:0:{}
2	bob	localhost	2026-10-27 10:00:00+00	\N	\N	\N	en_US	a:0:{}
\.

COPY public.contacts (contact_id, changed, del, name, email, firstname, surname, vcard, words, user_id) FROM stdin;
1	2026-10-27 10:00:00+00	0	Carol Contact	carol@example.com	Carol	Contact	BEGIN:VCARD\nVERSION:3.0\nN:Contact;Carol;;;\nFN:Carol Contact\nEMAIL;TYPE=INTERNET;TYPE=HOME:carol@example.com\nEND:VCARD	 carol contact carol@example.com	1
2	2026-10-27 10:00:00+00	1	Gone	gone@example.com	\N	\N	\N	\N	1
3	2026-10-27 10:00:00+00	0	Dave	dave@example.com	\N	\N	\N	\N	2
\.
`

func TestRoundcubeDump_Contacts(t *testing.T) {
	path := filepath.Join(t.TempDir(), "dump.sql")
	assert.NoError(t, os.WriteFile(path, []byte(dump), 0644))

	contacts, err := NewRoundcubeDump(path).Contacts()
	assert.NoError(t, err)
	assert.Len(t, contacts["alice"], 1)
	assert.Equal(t, "Carol Contact", contacts["alice"][0].Name)
	assert.Contains(t, contacts["alice"][0].Card(), "FN:Carol Contact\r\n")
	assert.Contains(t, contacts["alice"][0].Card(), "UID:roundcube-1\r\nEND:VCARD\r\n")

	assert.Len(t, contacts["bob"], 1)
	assert.Contains(t, contacts["bob"][0].Card(), "EMAIL;TYPE=INTERNET:dave@example.com\r\n")
}

func TestRoundcubeDump_Missing(t *testing.T) {
	contacts, err := NewRoundcubeDump(filepath.Join(t.TempDir(), "missing.sql")).Contacts()
	assert.NoError(t, err)
	assert.Empty(t, contacts)
}
