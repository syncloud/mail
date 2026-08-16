package installer

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.uber.org/zap"
)

type fakeRunner struct {
	err  error
	out  string
	app  string
	args []string
}

func (f *fakeRunner) RunDir(_ string, app string, args ...string) (string, error) {
	f.app = app
	f.args = args
	return f.out, f.err
}

func TestSieve_CompilesTheSpamScript(t *testing.T) {
	runner := &fakeRunner{}
	sieve := NewSieve("/snap/mail/current", "/var/snap/mail/current/config", runner, zap.NewNop())

	assert.NoError(t, sieve.Compile())

	assert.Equal(t, "/snap/mail/current/dovecot/bin/sievec.sh", runner.app)
	assert.Equal(t, []string{
		"-c", "/var/snap/mail/current/config/dovecot/dovecot.conf",
		"/var/snap/mail/current/config/sieve/spam.sieve",
	}, runner.args)
}

func TestSieve_ReportsCompilationFailure(t *testing.T) {
	runner := &fakeRunner{err: fmt.Errorf("sievec: line 3: error")}
	sieve := NewSieve("/snap/mail/current", "/var/snap/mail/current/config", runner, zap.NewNop())

	assert.Error(t, sieve.Compile())
}
