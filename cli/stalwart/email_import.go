package stalwart

type EmailImport struct {
	BlobId     string          `json:"blobId"`
	MailboxIds map[string]bool `json:"mailboxIds"`
	Keywords   map[string]bool `json:"keywords"`
	ReceivedAt string          `json:"receivedAt"`
}
