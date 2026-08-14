package installer

import (
	"path"

	"go.uber.org/zap"
)

const SpamScript = "sieve/spam.sieve"

type Runner interface {
	RunDir(dir, app string, args ...string) (string, error)
}

type Sieve struct {
	appDir     string
	configPath string
	executor   Runner
	logger     *zap.Logger
}

func NewSieve(appDir string, configPath string, executor Runner, logger *zap.Logger) *Sieve {
	return &Sieve{appDir: appDir, configPath: configPath, executor: executor, logger: logger}
}

func (s *Sieve) ScriptPath() string {
	return path.Join(s.configPath, SpamScript)
}

func (s *Sieve) Compile() error {
	script := s.ScriptPath()
	s.logger.Info("compiling the spam filing script", zap.String("script", script))
	sievec := path.Join(s.appDir, "dovecot", "bin", "sievec.sh")
	_, err := s.executor.RunDir("", sievec, script)
	return err
}
