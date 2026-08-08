package installer

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path"

	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const TunnelSocket = "spool/public/tunnel"

type MailInbound struct {
	dataDir string
	client  platform.HttpClient
	logger  *zap.Logger
}

func NewMailInbound(dataDir string, client platform.HttpClient, logger *zap.Logger) *MailInbound {
	return &MailInbound{dataDir: dataDir, client: client, logger: logger}
}

func (m *MailInbound) SocketPath() string {
	return path.Join(m.dataDir, TunnelSocket)
}

func (m *MailInbound) Register() error {
	socket := m.SocketPath()
	m.logger.Info("registering the inbound mail socket", zap.String("socket", socket))
	resp, err := m.client.Post("http://unix/mail/inbound/register",
		url.Values{"socket": {socket}})
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("unable to register the inbound mail socket: %s %s",
			resp.Status, string(body))
	}
	return nil
}
