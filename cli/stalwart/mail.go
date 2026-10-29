package stalwart

import (
	"encoding/json"
	"fmt"
	"time"
)

func Mailboxes(client *Client, accountId string) ([]Mailbox, error) {
	return List[Mailbox](client, accountId, "Mailbox")
}

func CreateMailbox(client *Client, accountId, name, parentId string) (string, error) {
	mailbox := NewMailbox{Name: name}
	if parentId != "" {
		mailbox.ParentId = &parentId
	}
	return Create(client, accountId, "Mailbox", mailbox)
}

func ImportEmail(client *Client, accountId string, content []byte, mailboxId string, keywords map[string]bool, received time.Time) error {
	blobId, err := client.Upload(accountId, content)
	if err != nil {
		return err
	}
	arguments := EmailImportArguments{
		AccountId: accountId,
		Emails: map[string]EmailImport{"m": {
			BlobId:     blobId,
			MailboxIds: map[string]bool{mailboxId: true},
			Keywords:   keywords,
			ReceivedAt: received.UTC().Format(time.RFC3339),
		}},
	}
	responses, err := client.Call(MethodCall{Name: "Email/import", Arguments: arguments, Id: "0"})
	if err != nil {
		return err
	}
	var response EmailImportResponse
	if err := json.Unmarshal(responses[0].Arguments, &response); err != nil {
		return err
	}
	if failure, ok := response.NotCreated["m"]; ok {
		return fmt.Errorf("email import: %s", failure)
	}
	return nil
}
