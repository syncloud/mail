package installer

import (
	"fmt"
	"os"
	"path"
	"strconv"

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
	if err := i.RegenerateConfigs(); err != nil {
		return err
	}
	return i.platformClient.RestartService(SystemdPostfix)
}

func (i *Installer) applySasl(relay RelayConfig) error {
	saslFile := path.Join(i.configPath, "postfix", "sasl_passwd")
	if !relay.Enabled {
		_ = os.Remove(saslFile)
		_ = os.Remove(saslFile + ".db")
		return nil
	}
	line := fmt.Sprintf("[%s]:%d %s:%s\n", relay.Host, relay.Port, relay.User, relay.Password)
	if err := os.WriteFile(saslFile, []byte(line), 0600); err != nil {
		return err
	}
	postmap := path.Join(i.appDir, "postfix", "usr", "sbin", "postmap")
	postfixConfigDir := path.Join(i.configPath, "postfix")
	_, err := i.executor.RunDir(postfixConfigDir, postmap, "-c", postfixConfigDir, "hash:"+saslFile)
	return err
}
