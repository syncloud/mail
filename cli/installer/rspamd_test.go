package installer

import (
	"os"
	"path"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.uber.org/zap"
)

func rspamdIn(t *testing.T) (*Rspamd, *fakeRunner, string) {
	dataDir := t.TempDir()
	assert.NoError(t, os.Mkdir(path.Join(dataDir, "rspamd"), 0755))
	runner := &fakeRunner{out: "$2$hashed"}
	return NewRspamd("/snap/mail/current", dataDir, runner, zap.NewNop()), runner, dataDir
}

func TestRspamd_GeneratesAPasswordAndKeepsIt(t *testing.T) {
	rspamd, _, dataDir := rspamdIn(t)

	first, err := rspamd.Password()
	assert.NoError(t, err)
	assert.Len(t, first, PasswordLength*2)

	stored, err := os.ReadFile(path.Join(dataDir, PasswordFile))
	assert.NoError(t, err)
	assert.Equal(t, first, string(stored))

	again, err := rspamd.Password()
	assert.NoError(t, err)
	assert.Equal(t, first, again)
}

func TestRspamd_HashesTheGeneratedPassword(t *testing.T) {
	rspamd, runner, _ := rspamdIn(t)

	hashed, err := rspamd.HashedPassword()
	assert.NoError(t, err)

	assert.Equal(t, "$2$hashed", hashed)
	assert.Equal(t, "/snap/mail/current/rspamd/bin/rspamadm.sh", runner.app)
	assert.Equal(t, "pw", runner.args[0])
	assert.Equal(t, "-p", runner.args[1])
}

func TestRspamd_TakesTheHashFromTheLastLine(t *testing.T) {
	rspamd, runner, _ := rspamdIn(t)
	runner.out = "some notice\n$2$hashed\n"

	hashed, err := rspamd.HashedPassword()
	assert.NoError(t, err)

	assert.Equal(t, "$2$hashed", hashed)
}
