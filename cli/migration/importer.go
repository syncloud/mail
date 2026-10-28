package migration

import (
	"os"
	"strings"

	"go.uber.org/zap"
	"hooks/stalwart"
)

var roles = map[string]string{
	"sent":    "sent",
	"drafts":  "drafts",
	"trash":   "trash",
	"junk":    "junk",
	"spam":    "junk",
	"archive": "archive",
}

type Importer struct {
	client    *stalwart.Client
	accountId string
	mailboxes []stalwart.Mailbox
	logger    *zap.Logger
}

func NewImporter(client *stalwart.Client, account string, logger *zap.Logger) (*Importer, error) {
	session, err := client.As(account).Session()
	if err != nil {
		return nil, err
	}
	accountId := session.AccountId()
	mailboxes, err := stalwart.Mailboxes(client, accountId)
	if err != nil {
		return nil, err
	}
	return &Importer{client: client, accountId: accountId, mailboxes: mailboxes, logger: logger}, nil
}

func (i *Importer) Import(maildir *Maildir, ledger *Ledger) (int, error) {
	keywords, err := maildir.Keywords()
	if err != nil {
		return 0, err
	}
	folders, err := maildir.Folders()
	if err != nil {
		return 0, err
	}
	imported := 0
	for _, folder := range folders {
		mailboxId, err := i.mailbox(folder)
		if err != nil {
			return imported, err
		}
		messages, err := folder.Messages()
		if err != nil {
			return imported, err
		}
		for _, message := range messages {
			key := folder.Name() + "/" + message.Key
			if message.Deleted() || ledger.Has(key) {
				continue
			}
			content, err := os.ReadFile(message.Path)
			if err != nil {
				return imported, err
			}
			if err := stalwart.ImportEmail(i.client, i.accountId, content, mailboxId, message.Keywords(keywords), message.Received); err != nil {
				return imported, err
			}
			if err := ledger.Add(key); err != nil {
				return imported, err
			}
			imported++
		}
		i.logger.Info("imported folder", zap.String("folder", folder.Name()), zap.Int("messages", len(messages)))
	}
	return imported, nil
}

func (i *Importer) mailbox(folder Folder) (string, error) {
	if folder.IsInbox() {
		return i.byRole("inbox"), nil
	}
	parentId := ""
	for depth, name := range folder.Names {
		if depth == 0 {
			if role, ok := roles[strings.ToLower(name)]; ok {
				if id := i.byRole(role); id != "" {
					parentId = id
					continue
				}
			}
		}
		id := i.byName(name, parentId)
		if id == "" {
			created, err := stalwart.CreateMailbox(i.client, i.accountId, name, parentId)
			if err != nil {
				return "", err
			}
			i.mailboxes = append(i.mailboxes, stalwart.Mailbox{Id: created, Name: name, ParentId: parentId})
			id = created
		}
		parentId = id
	}
	return parentId, nil
}

func (i *Importer) byRole(role string) string {
	for _, mailbox := range i.mailboxes {
		if mailbox.Role == role {
			return mailbox.Id
		}
	}
	return ""
}

func (i *Importer) byName(name, parentId string) string {
	for _, mailbox := range i.mailboxes {
		if strings.EqualFold(mailbox.Name, name) && mailbox.ParentId == parentId {
			return mailbox.Id
		}
	}
	return ""
}
