package migration

import (
	"path/filepath"
	"strings"
	"time"
)

type Message struct {
	Path     string
	Key      string
	Flags    string
	Received time.Time
}

func ParseMessage(path string, received time.Time) Message {
	name := filepath.Base(path)
	key, flags, _ := strings.Cut(name, ":2,")
	return Message{Path: path, Key: key, Flags: flags, Received: received}
}

func (m Message) Deleted() bool {
	return strings.ContainsRune(m.Flags, 'T')
}

func (m Message) Keywords(custom Keywords) map[string]bool {
	keywords := map[string]bool{}
	for _, flag := range m.Flags {
		switch {
		case flag == 'S':
			keywords["$seen"] = true
		case flag == 'R':
			keywords["$answered"] = true
		case flag == 'F':
			keywords["$flagged"] = true
		case flag == 'D':
			keywords["$draft"] = true
		case flag >= 'a' && flag <= 'z':
			if keyword, ok := custom[int(flag-'a')]; ok {
				keywords[keyword] = true
			}
		}
	}
	return keywords
}
