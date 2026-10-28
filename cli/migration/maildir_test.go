package migration

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestMaildir_Folders(t *testing.T) {
	root := t.TempDir()
	for _, dir := range []string{"cur", "new", ".Sent/cur", ".Projects/cur", ".Projects.2026/cur", ".notmaildir"} {
		assert.NoError(t, os.MkdirAll(filepath.Join(root, dir), 0755))
	}
	assert.NoError(t, os.WriteFile(filepath.Join(root, ".Projects.2026", "cur", "1.host:2,S"), []byte("Subject: x\r\n\r\nx"), 0644))
	assert.NoError(t, os.WriteFile(filepath.Join(root, "dovecot-keywords"), []byte("0 $Forwarded\n1 work\n"), 0644))

	folders, err := NewMaildir(root).Folders()
	assert.NoError(t, err)
	var names []string
	for _, folder := range folders {
		names = append(names, folder.Name())
	}
	assert.Equal(t, "", names[0])
	assert.ElementsMatch(t, []string{"", "Sent", "Projects", "Projects/2026"}, names)
	assert.Equal(t, "Projects/2026", names[len(names)-1])

	messages, err := folders[len(folders)-1].Messages()
	assert.NoError(t, err)
	assert.Len(t, messages, 1)

	keywords, err := NewMaildir(root).Keywords()
	assert.NoError(t, err)
	assert.Equal(t, Keywords{0: "$Forwarded", 1: "work"}, keywords)
}
