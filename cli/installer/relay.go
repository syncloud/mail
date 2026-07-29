package installer

import (
	"fmt"
	"os"
	"path"
	"strings"

	"github.com/syncloud/golib/platform"
)

func (i *Installer) ApplyRelay() error {
	relay, err := i.platformClient.GetMailRelay()
	if err != nil {
		return err
	}
	domain, err := i.mydomain()
	if err != nil {
		return err
	}
	return i.writeRelayMaps(relay, domain)
}

func (i *Installer) mydomain() (string, error) {
	postconf := path.Join(i.appDir, "postfix", "usr", "sbin", "postconf")
	postfixDir := path.Join(i.configPath, "postfix")
	out, err := i.executor.RunDir(postfixDir, postconf, "-h", "-c", postfixDir, "mydomain")
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(out), nil
}

func (i *Installer) writeRelayMaps(relay *platform.MailRelay, domain string) error {
	postfixDir := path.Join(i.configPath, "postfix")
	saslFile := path.Join(postfixDir, "sasl_passwd")
	relayFile := path.Join(postfixDir, "relayhost")

	saslContent := ""
	relayContent := ""
	if relay.Enabled {
		host := fmt.Sprintf("[%s]:%d", relay.Host, relay.Port)
		saslContent = fmt.Sprintf("%s %s:%s\n", host, relay.Login, relay.Password)
		relayContent = fmt.Sprintf("@%s %s\n", domain, host)
	}

	if err := os.WriteFile(saslFile, []byte(saslContent), 0600); err != nil {
		return err
	}
	if err := os.WriteFile(relayFile, []byte(relayContent), 0644); err != nil {
		return err
	}

	postmap := path.Join(i.appDir, "postfix", "usr", "sbin", "postmap")
	if _, err := i.executor.RunDir(postfixDir, postmap, "-c", postfixDir, "hash:"+saslFile); err != nil {
		return err
	}
	if _, err := i.executor.RunDir(postfixDir, postmap, "-c", postfixDir, "hash:"+relayFile); err != nil {
		return err
	}
	return nil
}
