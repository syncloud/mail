package installer

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"fmt"
	"os"
	"path"
)

type Dkim struct {
	dataDir string
}

func NewDkim(dataDir string) *Dkim {
	return &Dkim{dataDir: dataDir}
}

func (d *Dkim) LegacyKey(domain string) string {
	return path.Join(d.dataDir, "opendkim", "keys", domain, "mail.private")
}

func (d *Dkim) Key(domain string) string {
	return path.Join(d.dataDir, "dkim", domain+".private")
}

func (d *Dkim) Ensure(domain string) (string, string, error) {
	for _, candidate := range []string{d.Key(domain), d.LegacyKey(domain)} {
		if _, err := os.Stat(candidate); err == nil {
			publicKey, err := publicKey(candidate)
			return candidate, publicKey, err
		}
	}
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return "", "", err
	}
	file := d.Key(domain)
	if err := os.MkdirAll(path.Dir(file), 0700); err != nil {
		return "", "", err
	}
	encoded := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(key)})
	if err := os.WriteFile(file, encoded, 0600); err != nil {
		return "", "", err
	}
	publicKey, err := publicKey(file)
	return file, publicKey, err
}

func publicKey(file string) (string, error) {
	content, err := os.ReadFile(file)
	if err != nil {
		return "", err
	}
	block, _ := pem.Decode(content)
	if block == nil {
		return "", fmt.Errorf("no pem key in %s", file)
	}
	var key *rsa.PrivateKey
	switch block.Type {
	case "RSA PRIVATE KEY":
		key, err = x509.ParsePKCS1PrivateKey(block.Bytes)
	default:
		parsed, parseErr := x509.ParsePKCS8PrivateKey(block.Bytes)
		err = parseErr
		if rsaKey, ok := parsed.(*rsa.PrivateKey); ok {
			key = rsaKey
		} else if err == nil {
			err = fmt.Errorf("%s is not an rsa key", file)
		}
	}
	if err != nil {
		return "", err
	}
	der, err := x509.MarshalPKIXPublicKey(&key.PublicKey)
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(der), nil
}
