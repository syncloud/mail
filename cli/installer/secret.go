package installer

import (
	"crypto/rand"
	"encoding/hex"
	"os"
	"strings"
)

func EnsureSecret(path string) (string, error) {
	content, err := os.ReadFile(path)
	if err == nil && len(strings.TrimSpace(string(content))) > 0 {
		return strings.TrimSpace(string(content)), nil
	}
	if err != nil && !os.IsNotExist(err) {
		return "", err
	}
	random := make([]byte, 32)
	if _, err := rand.Read(random); err != nil {
		return "", err
	}
	secret := hex.EncodeToString(random)
	if err := os.WriteFile(path, []byte(secret), 0600); err != nil {
		return "", err
	}
	return secret, nil
}
