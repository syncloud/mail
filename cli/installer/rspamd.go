package installer

import (
	"crypto/rand"
	"encoding/hex"
	"os"
	"path"
	"strings"

	"go.uber.org/zap"
)

const (
	PasswordFile   = "rspamd/password"
	PasswordLength = 24
)

type Rspamd struct {
	appDir   string
	dataDir  string
	executor Runner
	logger   *zap.Logger
}

func NewRspamd(appDir string, dataDir string, executor Runner, logger *zap.Logger) *Rspamd {
	return &Rspamd{appDir: appDir, dataDir: dataDir, executor: executor, logger: logger}
}

func (r *Rspamd) PasswordPath() string {
	return path.Join(r.dataDir, PasswordFile)
}

func (r *Rspamd) Password() (string, error) {
	file := r.PasswordPath()
	existing, err := os.ReadFile(file)
	if err == nil {
		return strings.TrimSpace(string(existing)), nil
	}
	if !os.IsNotExist(err) {
		return "", err
	}
	r.logger.Info("generating the rspamd controller password")
	secret := make([]byte, PasswordLength)
	if _, err := rand.Read(secret); err != nil {
		return "", err
	}
	password := hex.EncodeToString(secret)
	if err := os.WriteFile(file, []byte(password), 0600); err != nil {
		return "", err
	}
	return password, nil
}

func (r *Rspamd) HashedPassword() (string, error) {
	password, err := r.Password()
	if err != nil {
		return "", err
	}
	rspamadm := path.Join(r.appDir, "rspamd", "bin", "rspamadm.sh")
	out, err := r.executor.RunDir("", rspamadm, "pw", "-p", password)
	if err != nil {
		return "", err
	}
	return lastLine(out), nil
}

func lastLine(out string) string {
	lines := strings.Split(strings.TrimSpace(out), "\n")
	return strings.TrimSpace(lines[len(lines)-1])
}
