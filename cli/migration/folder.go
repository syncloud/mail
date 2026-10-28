package migration

import (
	"os"
	"path/filepath"
	"strings"
)

type Folder struct {
	Names []string
	Path  string
}

func (f Folder) IsInbox() bool {
	return len(f.Names) == 0
}

func (f Folder) Name() string {
	return strings.Join(f.Names, "/")
}

func (f Folder) Messages() ([]Message, error) {
	var messages []Message
	for _, sub := range []string{"cur", "new"} {
		entries, err := os.ReadDir(filepath.Join(f.Path, sub))
		if os.IsNotExist(err) {
			continue
		}
		if err != nil {
			return nil, err
		}
		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			info, err := entry.Info()
			if err != nil {
				return nil, err
			}
			messages = append(messages, ParseMessage(filepath.Join(f.Path, sub, entry.Name()), info.ModTime()))
		}
	}
	return messages, nil
}
