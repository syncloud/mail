package migration

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Maildir struct {
	root string
}

func NewMaildir(root string) *Maildir {
	return &Maildir{root: root}
}

func (m *Maildir) Folders() ([]Folder, error) {
	folders := []Folder{{Path: m.root}}
	entries, err := os.ReadDir(m.root)
	if err != nil {
		return nil, err
	}
	for _, entry := range entries {
		name := entry.Name()
		if !entry.IsDir() || !strings.HasPrefix(name, ".") || name == "." || name == ".." {
			continue
		}
		path := filepath.Join(m.root, name)
		if !isMaildir(path) {
			continue
		}
		folders = append(folders, Folder{Names: strings.Split(strings.TrimPrefix(name, "."), "."), Path: path})
	}
	sort.Slice(folders, func(i, j int) bool { return len(folders[i].Names) < len(folders[j].Names) })
	return folders, nil
}

func (m *Maildir) Keywords() (Keywords, error) {
	return LoadKeywords(filepath.Join(m.root, "dovecot-keywords"))
}

func isMaildir(path string) bool {
	info, err := os.Stat(filepath.Join(path, "cur"))
	return err == nil && info.IsDir()
}
