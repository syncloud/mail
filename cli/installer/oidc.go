package installer

import (
	"fmt"
	"os"
	"path"

	"github.com/syncloud/golib/platform"
)

const OidcAuthMethod = "client_secret_post"

type Oidc struct {
	platformClient *platform.Client
	localesDir     string
	secretFile     string
}

func NewOidc(platformClient *platform.Client, appDir, dataDir string) *Oidc {
	return &Oidc{
		platformClient: platformClient,
		localesDir:     path.Join(appDir, "bulwark", "locales"),
		secretFile:     path.Join(dataDir, "bulwark", "oauth.secret"),
	}
}

func (o *Oidc) SecretFile() string {
	return o.secretFile
}

func (o *Oidc) Register() error {
	redirectUris, err := o.redirectUris()
	if err != nil {
		return err
	}
	secret, err := o.platformClient.RegisterOIDCClient(App, redirectUris, false, OidcAuthMethod)
	if err != nil {
		return err
	}
	return os.WriteFile(o.secretFile, []byte(secret), 0600)
}

func (o *Oidc) redirectUris() ([]string, error) {
	entries, err := os.ReadDir(o.localesDir)
	if err != nil {
		return nil, err
	}
	var redirectUris []string
	for _, entry := range entries {
		if entry.IsDir() {
			redirectUris = append(redirectUris, fmt.Sprintf("/%s/auth/callback", entry.Name()))
		}
	}
	if len(redirectUris) == 0 {
		return nil, fmt.Errorf("no bulwark locales in %s", o.localesDir)
	}
	return redirectUris, nil
}
