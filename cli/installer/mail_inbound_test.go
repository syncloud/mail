package installer

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

type fakeRegistry struct {
	err    error
	socket string
}

func (f *fakeRegistry) RegisterMailInbound(socket string) error {
	f.socket = socket
	return f.err
}

func TestMailInbound_RegistersTheSocket(t *testing.T) {
	registry := &fakeRegistry{}
	inbound := NewMailInbound("/var/snap/mail/current", registry, zap.NewNop())

	assert.NoError(t, inbound.Register())

	assert.Equal(t, "/var/snap/mail/current/spool/public/tunnel", registry.socket)
}

func TestMailInbound_OlderPlatformWithoutTheEndpointIsNotAFailure(t *testing.T) {
	registry := &fakeRegistry{err: platform.ErrNotSupported}
	inbound := NewMailInbound("/var/snap/mail/current", registry, zap.NewNop())

	assert.NoError(t, inbound.Register())
}

func TestMailInbound_ReportsOtherFailures(t *testing.T) {
	registry := &fakeRegistry{err: fmt.Errorf("register mail inbound, 500 Internal Server Error")}
	inbound := NewMailInbound("/var/snap/mail/current", registry, zap.NewNop())

	assert.Error(t, inbound.Register())
}
