package migration

import (
	"errors"
	"fmt"
	"os"
	"path"
	"time"

	"go.uber.org/zap"
	"hooks/stalwart"
)

type Migration struct {
	dataDir string
	domain  string
	client  *stalwart.Client
	logger  *zap.Logger
}

func New(dataDir, domain string, client *stalwart.Client, logger *zap.Logger) *Migration {
	return &Migration{dataDir: dataDir, domain: domain, client: client, logger: logger}
}

func (m *Migration) DoneFile() string {
	return path.Join(m.stateDir(), "done")
}

func (m *Migration) Run() error {
	if _, err := os.Stat(m.DoneFile()); err == nil {
		m.logger.Info("migration already done")
		return nil
	}
	if err := m.client.Wait(2 * time.Minute); err != nil {
		return err
	}
	if err := os.MkdirAll(m.stateDir(), 0700); err != nil {
		return err
	}
	users, err := m.users()
	if err != nil {
		return err
	}
	for _, user := range users {
		if err := m.mail(user); err != nil {
			return fmt.Errorf("mail of %s: %w", user, err)
		}
	}
	if err := m.contacts(); err != nil {
		return err
	}
	m.logger.Info("migration done", zap.Strings("users", users))
	return os.WriteFile(m.DoneFile(), []byte(time.Now().UTC().Format(time.RFC3339)), 0600)
}

func (m *Migration) users() ([]string, error) {
	entries, err := os.ReadDir(m.boxDir())
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var users []string
	for _, entry := range entries {
		if entry.IsDir() {
			users = append(users, entry.Name())
		}
	}
	return users, nil
}

func (m *Migration) mail(user string) error {
	ledger, err := LoadLedger(path.Join(m.stateDir(), user+".mail"))
	if err != nil {
		return err
	}
	importer, err := NewImporter(m.client, m.account(user), m.logger)
	var httpError *stalwart.HttpError
	if errors.As(err, &httpError) && httpError.Unauthorized() {
		m.logger.Warn("no account for this mailbox, leaving it in place", zap.String("user", user), zap.Error(err))
		return os.WriteFile(path.Join(m.stateDir(), user+".skipped"), []byte(err.Error()), 0600)
	}
	if err != nil {
		return err
	}
	imported, err := importer.Import(NewMaildir(path.Join(m.boxDir(), user)), ledger)
	m.logger.Info("imported mail", zap.String("user", user), zap.Int("messages", imported))
	return err
}

func (m *Migration) contacts() error {
	contacts, err := NewRoundcubeDump(path.Join(m.dataDir, "database.dump.sql")).Contacts()
	if err != nil {
		return err
	}
	for user, cards := range contacts {
		ledger, err := LoadLedger(path.Join(m.stateDir(), user+".contacts"))
		if err != nil {
			return err
		}
		client := m.client.As(m.account(user))
		for _, contact := range cards {
			if ledger.Has(contact.Id) {
				continue
			}
			href := fmt.Sprintf("/dav/card/%s/default/%s.vcf", m.account(user), contact.Uid())
			if err := client.Put(href, "text/vcard; charset=utf-8", []byte(contact.Card())); err != nil {
				return fmt.Errorf("contact %s of %s: %w", contact.Id, user, err)
			}
			if err := ledger.Add(contact.Id); err != nil {
				return err
			}
		}
		m.logger.Info("imported contacts", zap.String("user", user), zap.Int("contacts", len(cards)))
	}
	return nil
}

func (m *Migration) account(user string) string {
	return user + "@" + m.domain
}

func (m *Migration) boxDir() string {
	return path.Join(m.dataDir, "box")
}

func (m *Migration) stateDir() string {
	return path.Join(m.dataDir, "migration")
}
