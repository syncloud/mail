package installer

import (
	"fmt"
	"os"
	"path"
	"strconv"
	"strings"

	"gopkg.in/ini.v1"
)

const DefaultRelayPort = 587

type RelayConfig struct {
	Enabled  bool   `json:"enabled"`
	Host     string `json:"host"`
	Port     int    `json:"port"`
	User     string `json:"user"`
	Password string `json:"password"`
}

func (i *Installer) GetRelay() (RelayConfig, error) {
	cfg, err := ini.LooseLoad(i.userConfigFile)
	if err != nil {
		return RelayConfig{}, err
	}
	section := cfg.Section("relay")
	return RelayConfig{
		Enabled:  section.Key("enabled").MustBool(false),
		Host:     section.Key("host").String(),
		Port:     section.Key("port").MustInt(DefaultRelayPort),
		User:     section.Key("user").String(),
		Password: section.Key("password").String(),
	}, nil
}

func (i *Installer) SetRelay(relay RelayConfig) error {
	cfg, err := ini.LooseLoad(i.userConfigFile)
	if err != nil {
		return err
	}
	section := cfg.Section("relay")
	section.Key("enabled").SetValue(strconv.FormatBool(relay.Enabled))
	section.Key("host").SetValue(relay.Host)
	section.Key("port").SetValue(strconv.Itoa(relay.Port))
	section.Key("user").SetValue(relay.User)
	section.Key("password").SetValue(relay.Password)
	return cfg.SaveTo(i.userConfigFile)
}

func (i *Installer) ApplyRelay() error {
	relay, err := i.GetRelay()
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

func (i *Installer) writeRelayMaps(relay RelayConfig, domain string) error {
	postfixDir := path.Join(i.configPath, "postfix")
	saslFile := path.Join(postfixDir, "sasl_passwd")
	relayFile := path.Join(postfixDir, "relayhost")

	saslContent := ""
	relayContent := ""
	if relay.Enabled {
		host := fmt.Sprintf("[%s]:%d", relay.Host, relay.Port)
		saslContent = fmt.Sprintf("%s %s:%s\n", host, relay.User, relay.Password)
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
