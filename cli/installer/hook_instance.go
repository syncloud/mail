package installer

import (
	"os"
	"os/exec"
	"path"
	"strings"
	"syscall"
	"time"

	"github.com/syncloud/golib/linux"
	"go.uber.org/zap"
	"hooks/stalwart"
)

type HookInstance struct {
	appDir  string
	dataDir string
	logger  *zap.Logger
	command *exec.Cmd
}

func NewHookInstance(appDir, dataDir string, logger *zap.Logger) *HookInstance {
	return &HookInstance{appDir: appDir, dataDir: dataDir, logger: logger}
}

func (r *HookInstance) socketDir() string {
	return path.Join(r.dataDir, "stalwart", "hook")
}

func (r *HookInstance) adminSocket() string {
	return path.Join(r.socketDir(), "admin.sock")
}

func (r *HookInstance) Start() (*stalwart.Client, error) {
	if err := os.MkdirAll(r.socketDir(), 0700); err != nil {
		return nil, err
	}
	if err := linux.Chown(r.socketDir(), UserName); err != nil {
		return nil, err
	}
	env, err := os.ReadFile(path.Join(r.dataDir, "config", "stalwart", "stalwart.env"))
	if err != nil {
		return nil, err
	}
	command := exec.Command(path.Join(r.appDir, "stalwart", "stalwart"), "-c", path.Join(r.dataDir, "config", "stalwart", "config.json"))
	command.Env = append(os.Environ(), strings.Split(strings.TrimSpace(string(env)), "\n")...)
	command.Env = append(command.Env, "STALWART_ADMIN_SOCKET="+r.adminSocket())
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	if err := command.Start(); err != nil {
		return nil, err
	}
	r.command = command
	client := stalwart.NewClient(r.adminSocket(), r.logger)
	if err := client.Wait(time.Minute); err != nil {
		r.Stop()
		return nil, err
	}
	return client, nil
}

func (r *HookInstance) Stop() {
	if r.command == nil || r.command.Process == nil {
		return
	}
	if err := r.command.Process.Signal(syscall.SIGTERM); err != nil {
		r.logger.Warn("stalwart hook instance is already gone", zap.Error(err))
	}
	done := make(chan error, 1)
	go func() { done <- r.command.Wait() }()
	select {
	case err := <-done:
		r.logger.Info("stalwart hook instance stopped", zap.Error(err))
	case <-time.After(30 * time.Second):
		r.logger.Error("stalwart hook instance did not stop, killing it")
		if err := r.command.Process.Kill(); err != nil {
			r.logger.Error("cannot kill stalwart hook instance", zap.Error(err))
		}
		<-done
	}
	r.command = nil
}
