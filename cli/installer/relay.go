package installer

import (
	"fmt"
	"os"
	"path"
	"strings"

	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

type Relay struct {
	appDir         string
	postfixDir     string
	platformClient *platform.Client
	executor       *Executor
	logger         *zap.Logger
}

func NewRelay(appDir, configDir string, platformClient *platform.Client, executor *Executor, logger *zap.Logger) *Relay {
	return &Relay{
		appDir:         appDir,
		postfixDir:     path.Join(configDir, "postfix"),
		platformClient: platformClient,
		executor:       executor,
		logger:         logger,
	}
}

func (r *Relay) Apply() error {
	config, err := r.platformClient.GetMailRelay()
	if err != nil {
		return err
	}
	domain, err := r.mydomain()
	if err != nil {
		return err
	}
	return r.writeMaps(config, domain)
}

func (r *Relay) mydomain() (string, error) {
	postconf := path.Join(r.appDir, "postfix", "usr", "sbin", "postconf")
	out, err := r.executor.RunDir(r.postfixDir, postconf, "-h", "-c", r.postfixDir, "mydomain")
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(out), nil
}

func (r *Relay) writeMaps(config *platform.MailRelay, domain string) error {
	saslFile := path.Join(r.postfixDir, "sasl_passwd")
	relayFile := path.Join(r.postfixDir, "relayhost")

	saslContent := ""
	relayContent := ""
	if config.Enabled {
		host := fmt.Sprintf("[%s]:%d", config.Host, config.Port)
		saslContent = fmt.Sprintf("%s %s:%s\n", host, config.Login, config.Password)
		relayContent = fmt.Sprintf("@%s smtps:%s\n", domain, host)
	}

	if err := os.WriteFile(saslFile, []byte(saslContent), 0600); err != nil {
		return err
	}
	if err := os.WriteFile(relayFile, []byte(relayContent), 0644); err != nil {
		return err
	}

	postmap := path.Join(r.appDir, "postfix", "usr", "sbin", "postmap")
	if _, err := r.executor.RunDir(r.postfixDir, postmap, "-c", r.postfixDir, "hash:"+saslFile); err != nil {
		return err
	}
	if _, err := r.executor.RunDir(r.postfixDir, postmap, "-c", r.postfixDir, "hash:"+relayFile); err != nil {
		return err
	}
	return nil
}
