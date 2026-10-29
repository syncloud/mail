package migration

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestParseMessage_Flags(t *testing.T) {
	message := ParseMessage("/box/user/cur/1700000000.M1P2.host,S=10:2,FSa", time.Unix(0, 0))
	assert.Equal(t, "1700000000.M1P2.host,S=10", message.Key)
	assert.Equal(t, map[string]bool{"$flagged": true, "$seen": true, "$Forwarded": true},
		message.Keywords(Keywords{0: "$Forwarded"}))
	assert.False(t, message.Deleted())
}

func TestParseMessage_New(t *testing.T) {
	message := ParseMessage("/box/user/new/1700000000.M1P2.host", time.Unix(0, 0))
	assert.Equal(t, "1700000000.M1P2.host", message.Key)
	assert.Empty(t, message.Keywords(Keywords{}))
}

func TestParseMessage_Deleted(t *testing.T) {
	assert.True(t, ParseMessage("/box/user/cur/1.host:2,ST", time.Unix(0, 0)).Deleted())
}
