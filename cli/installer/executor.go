package installer

import (
	"os/exec"
	"strings"

	"go.uber.org/zap"
)

type Executor struct {
	logger *zap.Logger
}

func NewExecutor(logger *zap.Logger) *Executor {
	return &Executor{
		logger: logger,
	}
}

func (e *Executor) RunDir(dir, app string, args ...string) (string, error) {
	cmd := exec.Command(app, args...)
	cmd.Dir = dir
	e.logger.Info("executing", zap.String("cmd", cmd.String()), zap.String("dir", dir))
	out, err := cmd.CombinedOutput()
	e.logger.Info("command output")
	for _, line := range strings.Split(string(out), "\n") {
		e.logger.Info(line)
	}
	return string(out), err
}
