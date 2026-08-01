package installer

import (
	"fmt"
	"os"
	"path"

	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

type Relay struct {
	appDir     string
	postfixDir string
	executor   *Executor
	logger     *zap.Logger
}

func NewRelay(appDir, configDir string, executor *Executor, logger *zap.Logger) *Relay {
	return &Relay{
		appDir:     appDir,
		postfixDir: path.Join(configDir, "postfix"),
		executor:   executor,
		logger:     logger,
	}
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
