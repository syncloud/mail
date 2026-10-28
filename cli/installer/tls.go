package installer

import (
	"os"
	"path"

	"github.com/syncloud/golib/linux"
)

const SystemCaFile = "/etc/ssl/certs/ca-certificates.crt"

type Tls struct {
	platformDir string
	dir         string
}

func NewTls(platformDir, dataDir string) *Tls {
	return &Tls{platformDir: platformDir, dir: path.Join(dataDir, "stalwart", "tls")}
}

func (t *Tls) CertificateFile() string {
	return path.Join(t.dir, "syncloud.crt")
}

func (t *Tls) KeyFile() string {
	return path.Join(t.dir, "syncloud.key")
}

func (t *Tls) CaFile() string {
	return path.Join(t.dir, "ca.pem")
}

func (t *Tls) Sync() error {
	if err := os.MkdirAll(t.dir, 0700); err != nil {
		return err
	}
	if err := copyFile(path.Join(t.platformDir, "syncloud.crt"), t.CertificateFile()); err != nil {
		return err
	}
	if err := copyFile(path.Join(t.platformDir, "syncloud.key"), t.KeyFile()); err != nil {
		return err
	}
	if err := t.caBundle(); err != nil {
		return err
	}
	return linux.Chown(t.dir, UserName)
}

func (t *Tls) caBundle() error {
	system, err := os.ReadFile(SystemCaFile)
	if err != nil {
		return err
	}
	platform, err := os.ReadFile(path.Join(t.platformDir, "syncloud.ca.crt"))
	if err != nil {
		return err
	}
	bundle := append(append(system, '\n'), platform...)
	tmp := t.CaFile() + ".tmp"
	if err := os.WriteFile(tmp, bundle, 0644); err != nil {
		return err
	}
	return os.Rename(tmp, t.CaFile())
}

func copyFile(from, to string) error {
	content, err := os.ReadFile(from)
	if err != nil {
		return err
	}
	tmp := to + ".tmp"
	if err := os.WriteFile(tmp, content, 0600); err != nil {
		return err
	}
	return os.Rename(tmp, to)
}
