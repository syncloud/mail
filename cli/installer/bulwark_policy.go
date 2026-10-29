package installer

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

const sidebarAppPrefix = "admin-app-syncloud-"

type BulwarkPolicy struct {
	file string
}

func NewBulwarkPolicy(file string) *BulwarkPolicy {
	return &BulwarkPolicy{file: file}
}

func (p *BulwarkPolicy) Apps(appDomain string) []SidebarApp {
	return []SidebarApp{
		{Id: sidebarAppPrefix + "settings", Name: "Mail settings", Url: fmt.Sprintf("https://%s/stalwart/", appDomain), Icon: "Settings", OpenMode: "tab", ShowOnMobile: true},
	}
}

func (p *BulwarkPolicy) Ensure(appDomain string) error {
	policy := map[string]json.RawMessage{}
	content, err := os.ReadFile(p.file)
	if err == nil {
		if err := json.Unmarshal(content, &policy); err != nil {
			return fmt.Errorf("%s: %w", p.file, err)
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	var current []SidebarApp
	if raw, ok := policy["defaultSidebarApps"]; ok {
		if err := json.Unmarshal(raw, &current); err != nil {
			return fmt.Errorf("%s defaultSidebarApps: %w", p.file, err)
		}
	}
	apps := p.Apps(appDomain)
	for _, app := range current {
		if !strings.HasPrefix(app.Id, sidebarAppPrefix) {
			apps = append(apps, app)
		}
	}
	encoded, err := json.Marshal(apps)
	if err != nil {
		return err
	}
	policy["defaultSidebarApps"] = encoded
	content, err = json.MarshalIndent(policy, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(p.file, content, 0600)
}
