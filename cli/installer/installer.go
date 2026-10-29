package installer

import (
	"fmt"
	"os"
	"path"
	"strings"
	"time"

	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
	"hooks/migration"
	"hooks/stalwart"
)

const (
	App             = "mail"
	UserName        = "mail"
	SystemdStalwart = "mail.stalwart"
	SystemdBulwark  = "mail.bulwark"
	LdapUrl         = "ldap://localhost"
	LdapBindDn      = "dc=syncloud,dc=org"
	LdapPassword    = "syncloud"
	PlatformDataDir = "/var/snap/platform/current"
)

type Installer struct {
	appDir         string
	dataDir        string
	commonDir      string
	configPath     string
	platformClient *platform.Client
	mailInbound    *MailInbound
	dkim           *Dkim
	tls            *Tls
	oidc           *Oidc
	hookInstance   *HookInstance
	logger         *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	platformClient := platform.New()
	return &Installer{
		appDir:         appDir,
		dataDir:        dataDir,
		commonDir:      commonDir,
		configPath:     path.Join(dataDir, "config"),
		platformClient: platformClient,
		mailInbound:    NewMailInbound(dataDir, platformClient, logger),
		dkim:           NewDkim(dataDir),
		tls:            NewTls(PlatformDataDir, dataDir),
		oidc:           NewOidc(platformClient, appDir, dataDir),
		hookInstance:   NewHookInstance(appDir, dataDir, logger),
		logger:         logger,
	}
}

func (i *Installer) Install() error {
	if err := i.setup(); err != nil {
		return err
	}
	return i.mailInbound.Register()
}

func (i *Installer) PostRefresh() error {
	return i.Install()
}

func (i *Installer) Configure() error {
	appStorageDir, err := i.platformClient.InitStorage(App, UserName)
	if err != nil {
		return err
	}
	tmpStoragePath := path.Join(appStorageDir, "tmp")
	if err := linux.CreateMissingDirs(tmpStoragePath); err != nil {
		return err
	}
	return linux.Chown(tmpStoragePath, UserName)
}

func (i *Installer) PreRefresh() error {
	return nil
}

func (i *Installer) StorageChange() error {
	return nil
}

func (i *Installer) CertificateChange() error {
	if err := i.tls.Sync(); err != nil {
		return err
	}
	client, err := i.client()
	if err != nil {
		return err
	}
	return stalwart.NewProvisioner(client, i.logger).ReloadCertificates()
}

func (i *Installer) AccessChange() error {
	variables, err := i.regenerateConfigs()
	if err != nil {
		return err
	}
	if err := i.bulwarkPolicy().Ensure(variables.AppDomainName); err != nil {
		return err
	}
	if err := i.oidc.Register(); err != nil {
		return err
	}
	if err := linux.Chown(path.Join(i.dataDir, "bulwark"), UserName); err != nil {
		return err
	}
	client, err := i.client()
	if err != nil {
		return err
	}
	settings, err := i.settings()
	if err != nil {
		return err
	}
	if err := stalwart.NewProvisioner(client, i.logger).Apply(settings); err != nil {
		return err
	}
	if err := i.platformClient.RestartService(SystemdStalwart); err != nil {
		return err
	}
	return i.platformClient.RestartService(SystemdBulwark)
}

func (i *Installer) MailRelayChange() error {
	client, err := i.client()
	if err != nil {
		return err
	}
	relay, err := i.relay()
	if err != nil {
		return err
	}
	return stalwart.NewProvisioner(client, i.logger).ApplyRelay(relay)
}

func (i *Installer) BackupPreStop() error {
	return nil
}

func (i *Installer) RestorePreStart() error {
	return i.PostRefresh()
}

func (i *Installer) RestorePostStart() error {
	return i.Configure()
}

func (i *Installer) Migrate() error {
	domain, err := i.stalwartEnv("STALWART_DIRECTORY_EMAIL_DOMAIN")
	if err != nil {
		return err
	}
	client, err := i.client()
	if err != nil {
		return err
	}
	return migration.New(i.dataDir, domain, client, i.logger).Run()
}

func (i *Installer) setup() error {
	if err := linux.CreateUser(UserName); err != nil {
		return err
	}
	if err := linux.CreateMissingDirs(
		i.commonDir,
		i.configPath,
		path.Join(i.dataDir, "nginx"),
		path.Join(i.dataDir, "stalwart", "data"),
		path.Join(i.dataDir, "stalwart", "webui"),
		path.Join(i.dataDir, "spool", "public"),
		path.Join(i.dataDir, "dkim"),
		path.Join(i.dataDir, "migration"),
		path.Join(i.dataDir, "bulwark", "settings"),
		path.Join(i.dataDir, "bulwark", "admin"),
		path.Join(i.dataDir, "bulwark", "admin-state"),
		path.Join(i.dataDir, "bulwark", "telemetry"),
		path.Join(i.dataDir, "bulwark", "version-check"),
		path.Join(i.dataDir, "bulwark", "cache"),
	); err != nil {
		return err
	}
	variables, err := i.regenerateConfigs()
	if err != nil {
		return err
	}
	if err := i.oidc.Register(); err != nil {
		return err
	}
	if err := os.RemoveAll(path.Join(i.dataDir, "stalwart", "admin.password")); err != nil {
		return err
	}
	if _, err := EnsureSecret(path.Join(i.dataDir, "bulwark", "session.secret")); err != nil {
		return err
	}
	if err := i.bulwarkPolicy().Ensure(variables.AppDomainName); err != nil {
		return err
	}
	_, publicKey, err := i.dkim.Ensure(variables.DeviceDomainName)
	if err != nil {
		return err
	}
	if err := i.platformClient.SetDkimKey(publicKey); err != nil {
		return err
	}
	if err := linux.Chown(i.dataDir, UserName); err != nil {
		return err
	}
	if err := linux.Chown(i.commonDir, UserName); err != nil {
		return err
	}
	if err := i.tls.Sync(); err != nil {
		return err
	}
	return i.provision()
}

func (i *Installer) provision() error {
	settings, err := i.settings()
	if err != nil {
		return err
	}
	client, err := i.hookInstance.Start()
	if err != nil {
		return err
	}
	defer i.hookInstance.Stop()
	return stalwart.NewProvisioner(client, i.logger).Apply(settings)
}

func (i *Installer) regenerateConfigs() (Variables, error) {
	deviceDomainName, err := i.platformClient.GetDeviceDomainName()
	if err != nil {
		return Variables{}, err
	}
	appDomainName, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return Variables{}, err
	}
	authUrl, err := i.platformClient.GetAppUrl("auth")
	if err != nil {
		return Variables{}, err
	}
	variables := Variables{
		AppDir:           i.appDir,
		DataDir:          i.dataDir,
		CommonDir:        i.commonDir,
		DeviceDomainName: deviceDomainName,
		AppDomainName:    appDomainName,
		AuthUrl:          authUrl,
		OauthSecretFile:  i.oidc.SecretFile(),
		PlatformCa:       path.Join(PlatformDataDir, "syncloud.ca.crt"),
	}
	if err := config.Generate(path.Join(i.appDir, "config"), i.configPath, variables); err != nil {
		return Variables{}, err
	}
	return variables, linux.Chown(i.configPath, UserName)
}

func (i *Installer) settings() (stalwart.Settings, error) {
	deviceDomainName, err := i.platformClient.GetDeviceDomainName()
	if err != nil {
		return stalwart.Settings{}, err
	}
	appDomainName, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return stalwart.Settings{}, err
	}
	keyFile, _, err := i.dkim.Ensure(deviceDomainName)
	if err != nil {
		return stalwart.Settings{}, err
	}
	relay, err := i.relay()
	if err != nil {
		return stalwart.Settings{}, err
	}
	return stalwart.Settings{
		DeviceDomain:     deviceDomainName,
		AppDomain:        appDomainName,
		LdapUrl:          LdapUrl,
		LdapBindDn:       LdapBindDn,
		LdapBindPassword: LdapPassword,
		DkimKeyFile:      keyFile,
		CertificateFile:  i.tls.CertificateFile(),
		KeyFile:          i.tls.KeyFile(),
		WebUiArchive:     path.Join(i.appDir, "stalwart", "webui.zip"),
		WebUiDirectory:   path.Join(i.dataDir, "stalwart", "webui"),
		SpamRules:        path.Join(i.appDir, "stalwart", "spam-filter-rules.json.gz"),
		Relay:            relay,
	}, nil
}

func (i *Installer) relay() (stalwart.Relay, error) {
	relay, err := i.platformClient.GetMailRelay()
	if err != nil {
		return stalwart.Relay{}, err
	}
	return stalwart.Relay{
		Enabled:  relay.Enabled,
		Host:     relay.Host,
		Port:     relay.Port,
		Login:    relay.Login,
		Password: relay.Password,
	}, nil
}

func (i *Installer) client() (*stalwart.Client, error) {
	client := stalwart.NewClient(path.Join(i.dataDir, "stalwart", "admin.sock"), i.logger)
	return client, client.Wait(2 * time.Minute)
}

func (i *Installer) stalwartEnv(name string) (string, error) {
	content, err := os.ReadFile(path.Join(i.configPath, "stalwart", "stalwart.env"))
	if err != nil {
		return "", err
	}
	for _, line := range strings.Split(string(content), "\n") {
		if value, ok := strings.CutPrefix(line, name+"="); ok {
			return value, nil
		}
	}
	return "", fmt.Errorf("%s is not in stalwart.env", name)
}

func (i *Installer) bulwarkPolicy() *BulwarkPolicy {
	return NewBulwarkPolicy(path.Join(i.dataDir, "bulwark", "admin", "policy.json"))
}
