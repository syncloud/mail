package installer

import (
	"io"
	"net/http"
	"net/url"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.uber.org/zap"
)

type fakePlatform struct {
	status int
	posted url.Values
	path   string
}

func (f *fakePlatform) Post(path string, values url.Values) (*http.Response, error) {
	f.path = path
	f.posted = values
	return &http.Response{
		StatusCode: f.status,
		Status:     http.StatusText(f.status),
		Body:       io.NopCloser(strings.NewReader("")),
	}, nil
}

func (f *fakePlatform) Get(_ string) (*http.Response, error) {
	return nil, nil
}

func TestMailInbound_RegistersTheSocket(t *testing.T) {
	platform := &fakePlatform{status: http.StatusOK}
	inbound := NewMailInbound("/var/snap/mail/current", platform, zap.NewNop())

	assert.NoError(t, inbound.Register())

	assert.Equal(t, "http://unix/mail/inbound/register", platform.path)
	assert.Equal(t, "/var/snap/mail/current/spool/public/tunnel",
		platform.posted.Get("socket"))
}

func TestMailInbound_OlderPlatformWithoutTheEndpointIsNotAFailure(t *testing.T) {
	platform := &fakePlatform{status: http.StatusNotFound}
	inbound := NewMailInbound("/var/snap/mail/current", platform, zap.NewNop())

	assert.NoError(t, inbound.Register())
}

func TestMailInbound_ReportsOtherFailures(t *testing.T) {
	platform := &fakePlatform{status: http.StatusInternalServerError}
	inbound := NewMailInbound("/var/snap/mail/current", platform, zap.NewNop())

	assert.Error(t, inbound.Register())
}
