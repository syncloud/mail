package migration

import (
	"fmt"
	"strings"
)

type Contact struct {
	Id    string
	Name  string
	Email string
	VCard string
}

func (c Contact) Uid() string {
	return "roundcube-" + c.Id
}

func (c Contact) Card() string {
	card := strings.ReplaceAll(strings.TrimSpace(c.VCard), "\r\n", "\n")
	if card == "" {
		card = fmt.Sprintf("BEGIN:VCARD\nVERSION:3.0\nFN:%s\nEMAIL;TYPE=INTERNET:%s\nEND:VCARD", c.Name, c.Email)
	}
	if !strings.Contains(strings.ToUpper(card), "\nUID:") {
		card = strings.Replace(card, "\nEND:VCARD", "\nUID:"+c.Uid()+"\nEND:VCARD", 1)
	}
	return strings.ReplaceAll(card, "\n", "\r\n") + "\r\n"
}
