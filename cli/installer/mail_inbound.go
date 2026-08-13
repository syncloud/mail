package installer

import (
	"errors"
	"path"

	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const TunnelSocket = "spool/public/tunnel"

type PlatformRegistry interface {
	RegisterMailInbound(socket string) error
}

type MailInbound struct {
	dataDir  string
	registry PlatformRegistry
	logger   *zap.Logger
}

func NewMailInbound(dataDir string, registry PlatformRegistry, logger *zap.Logger) *MailInbound {
	return &MailInbound{dataDir: dataDir, registry: registry, logger: logger}
}

func (m *MailInbound) SocketPath() string {
	return path.Join(m.dataDir, TunnelSocket)
}

func (m *MailInbound) Register() error {
	socket := m.SocketPath()
	m.logger.Info("registering the inbound mail socket", zap.String("socket", socket))
	err := m.registry.RegisterMailInbound(socket)
	if errors.Is(err, platform.ErrNotSupported) {
		m.logger.Info("this platform does not take inbound mail registrations")
		return nil
	}
	return err
}
