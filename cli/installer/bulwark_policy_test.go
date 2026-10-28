package installer

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestBulwarkPolicy_Seeds(t *testing.T) {
	file := filepath.Join(t.TempDir(), "policy.json")
	assert.NoError(t, NewBulwarkPolicy(file).Ensure("mail.example.com"))

	var policy struct {
		DefaultSidebarApps []SidebarApp `json:"defaultSidebarApps"`
	}
	content, err := os.ReadFile(file)
	assert.NoError(t, err)
	assert.NoError(t, json.Unmarshal(content, &policy))
	assert.Len(t, policy.DefaultSidebarApps, 1)
	assert.Equal(t, "https://mail.example.com/stalwart/", policy.DefaultSidebarApps[0].Url)
}

func TestBulwarkPolicy_KeepsAdminEdits(t *testing.T) {
	file := filepath.Join(t.TempDir(), "policy.json")
	assert.NoError(t, os.WriteFile(file, []byte(`{"pushRelayUrl":"https://push.example","defaultSidebarApps":[{"id":"admin-app-wiki","name":"Wiki","url":"https://wiki.example","icon":"Globe","openMode":"tab","showOnMobile":false},{"id":"admin-app-syncloud-server","name":"Mail server","url":"https://old.example/stalwart/admin/","icon":"Server","openMode":"tab","showOnMobile":true}]}`), 0600))

	assert.NoError(t, NewBulwarkPolicy(file).Ensure("mail.new.example"))

	content, err := os.ReadFile(file)
	assert.NoError(t, err)
	assert.Contains(t, string(content), `"pushRelayUrl": "https://push.example"`)
	assert.Contains(t, string(content), "https://wiki.example")
	assert.Contains(t, string(content), "https://mail.new.example/stalwart/")
	assert.NotContains(t, string(content), "old.example")
}
