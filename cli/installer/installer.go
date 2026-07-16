package installer

import (
	"fmt"
	"os"
	"path"
	"regexp"
	"strconv"
	"strings"

	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
	"gopkg.in/ini.v1"
)

const (
	App            = "mail"
	UserName       = "mail"
	PsqlPort       = 5432
	DbName         = "mail"
	DbUser         = "mail"
	DbPass         = "mail"
	SystemdDovecot = "mail.dovecot"
	SystemdPostfix = "mail.postfix"
)

var dkimKeyPattern = regexp.MustCompile(`(?s).*p=(.*?)".*`)

type Variables struct {
	AppDir           string
	AppDataDir       string
	AppCommonDir     string
	DbPsqlPath       string
	DbPsqlPort       int
	DbName           string
	DbUser           string
	DbPassword       string
	PlatformDataDir  string
	DeviceDomainName string
	AppDomainName    string
	Timezone         string
	Relay            bool
	RelayHost        string
	RelayPort        int
}

type Installer struct {
	appDir          string
	dataDir         string
	commonDir       string
	configPath      string
	logDir          string
	opendkimDir     string
	opendkimKeysDir string
	userConfigFile  string
	platformClient  *platform.Client
	database        *Database
	executor        *Executor
	logger          *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	commonDir := fmt.Sprintf("/var/snap/%s/common", App)
	configPath := path.Join(dataDir, "config")
	executor := NewExecutor(logger)
	return &Installer{
		appDir:          appDir,
		dataDir:         dataDir,
		commonDir:       commonDir,
		configPath:      configPath,
		logDir:          path.Join(dataDir, "log"),
		opendkimDir:     path.Join(dataDir, "opendkim"),
		opendkimKeysDir: path.Join(dataDir, "opendkim", "keys"),
		userConfigFile:  path.Join(dataDir, "user_mail.cfg"),
		platformClient:  platform.New(),
		database:        NewDatabase(appDir, dataDir, configPath, DbName, DbUser, DbPass, PsqlPort, executor, logger),
		executor:        executor,
		logger:          logger,
	}
}

func (i *Installer) platformDataDir() string {
	return "/var/snap/platform/current"
}

func timezone() (string, error) {
	content, err := os.ReadFile("/etc/timezone")
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(content)), nil
}

func (i *Installer) RegenerateConfigs() error {
	deviceDomainName, err := i.platformClient.GetDeviceDomainName()
	if err != nil {
		return err
	}
	appDomainName, err := i.platformClient.GetAppDomainName(App)
	if err != nil {
		return err
	}
	tz, err := timezone()
	if err != nil {
		return err
	}
	relay, err := i.GetRelay()
	if err != nil {
		return err
	}

	variables := Variables{
		AppDir:           i.appDir,
		AppDataDir:       i.dataDir,
		AppCommonDir:     i.commonDir,
		DbPsqlPath:       i.database.Dir(),
		DbPsqlPort:       i.database.Port(),
		DbName:           DbName,
		DbUser:           DbUser,
		DbPassword:       DbPass,
		PlatformDataDir:  i.platformDataDir(),
		DeviceDomainName: deviceDomainName,
		AppDomainName:    appDomainName,
		Timezone:         tz,
		Relay:            relay.Enabled,
		RelayHost:        relay.Host,
		RelayPort:        relay.Port,
	}

	templatesPath := path.Join(i.appDir, "config")
	if err := config.Generate(templatesPath, i.configPath, variables); err != nil {
		return err
	}

	if err := i.applySasl(relay); err != nil {
		return err
	}

	return linux.Chown(i.configPath, UserName)
}

func (i *Installer) MigrateCommonToData() error {
	marker := path.Join(i.dataDir, ".migrated_from_common")
	if _, err := os.Stat(marker); err == nil {
		return nil
	}
	if err := linux.CreateMissingDirs(i.dataDir); err != nil {
		return err
	}
	entries, err := os.ReadDir(i.commonDir)
	if err != nil {
		if os.IsNotExist(err) {
			return os.WriteFile(marker, []byte{}, 0644)
		}
		return err
	}
	for _, entry := range entries {
		name := entry.Name()
		if name == "web.socket" || strings.HasSuffix(name, ".socket") {
			continue
		}
		dst := path.Join(i.dataDir, name)
		if _, err := os.Stat(dst); err == nil {
			continue
		}
		i.logger.Info("migrating to data", zap.String("name", name))
		if err := os.Rename(path.Join(i.commonDir, name), dst); err != nil {
			return err
		}
	}
	return os.WriteFile(marker, []byte{}, 0644)
}

func (i *Installer) InitConfig() error {
	if err := i.MigrateCommonToData(); err != nil {
		return err
	}
	if err := linux.CreateUser("maildrop"); err != nil {
		return err
	}
	if err := linux.CreateUser("dovecot"); err != nil {
		return err
	}
	if err := linux.CreateUser(UserName); err != nil {
		return err
	}

	deviceDomainName, err := i.platformClient.GetDeviceDomainName()
	if err != nil {
		return err
	}
	opendkimKeysDomainDir := path.Join(i.opendkimKeysDir, deviceDomainName)
	boxDataDir := path.Join(i.dataDir, "box")

	if err := linux.CreateMissingDirs(
		i.commonDir,
		path.Join(i.dataDir, "nginx"),
		path.Join(i.dataDir, "config"),
		i.logDir,
		path.Join(i.dataDir, "spool"),
		path.Join(i.dataDir, "dovecot"),
		path.Join(i.dataDir, "dovecot", "private"),
		path.Join(i.dataDir, "data"),
		boxDataDir,
		i.opendkimDir,
		i.opendkimKeysDir,
		opendkimKeysDomainDir,
	); err != nil {
		return err
	}

	if err := i.RegenerateConfigs(); err != nil {
		return err
	}

	dkimKey, err := i.GenerateDkimKey(deviceDomainName, opendkimKeysDomainDir)
	if err != nil {
		return err
	}
	if err := i.platformClient.SetDkimKey(dkimKey); err != nil {
		return err
	}

	if err := linux.Chown(i.dataDir, UserName); err != nil {
		return err
	}
	if err := linux.Chown(i.commonDir, UserName); err != nil {
		return err
	}
	if _, err := i.executor.RunDir("", "chown", "-R", "dovecot:dovecot", boxDataDir); err != nil {
		return err
	}

	i.logger.Info("setup configs")
	return nil
}

func (i *Installer) GenerateDkimKey(deviceDomainName, opendkimKeysDomainDir string) (string, error) {
	genkey := path.Join(i.appDir, "opendkim", "bin", "opendkim-genkey")
	if _, err := i.executor.RunDir(opendkimKeysDomainDir, genkey, "-s", "mail", "-d", deviceDomainName); err != nil {
		return "", err
	}
	mailTxtFile := path.Join(opendkimKeysDomainDir, "mail.txt")
	content, err := os.ReadFile(mailTxtFile)
	if err != nil {
		return "", err
	}
	mailTxt := strings.TrimSpace(string(content))
	match := dkimKeyPattern.FindStringSubmatch(mailTxt)
	if match == nil {
		return "", fmt.Errorf("unable to parse dkim key from %s", mailTxtFile)
	}
	return match[1], nil
}

func (i *Installer) Install() error {
	if err := i.InitConfig(); err != nil {
		return err
	}
	return i.database.Init()
}

func (i *Installer) PostRefresh() error {
	return i.InitConfig()
}

func (i *Installer) Configure() error {
	activated, err := i.isActivated()
	if err != nil {
		return err
	}
	if !activated {
		if err := i.Initialize(); err != nil {
			return err
		}
	}
	return i.PrepareStorage()
}

func (i *Installer) Initialize() error {
	i.logger.Info("initialization")
	if err := i.database.Create(); err != nil {
		return err
	}
	return i.setActivated(true)
}

func (i *Installer) isActivated() (bool, error) {
	cfg, err := ini.LooseLoad(i.userConfigFile)
	if err != nil {
		return false, err
	}
	return cfg.Section("mail").Key("activated").MustBool(false), nil
}

func (i *Installer) setActivated(activated bool) error {
	cfg, err := ini.LooseLoad(i.userConfigFile)
	if err != nil {
		return err
	}
	cfg.Section("mail").Key("activated").SetValue(strconv.FormatBool(activated))
	return cfg.SaveTo(i.userConfigFile)
}

func (i *Installer) PrepareStorage() error {
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

func (i *Installer) UpdateDomain() error {
	if err := i.RegenerateConfigs(); err != nil {
		return err
	}
	return i.platformClient.RestartService(SystemdDovecot)
}

func (i *Installer) CertificateChange() error {
	return i.platformClient.RestartService(SystemdDovecot)
}

func (i *Installer) StorageChange() error {
	return nil
}

func (i *Installer) AccessChange() error {
	return i.UpdateDomain()
}

func (i *Installer) PreRefresh() error {
	return nil
}

func (i *Installer) BackupPreStop() error {
	return i.PreRefresh()
}

func (i *Installer) RestorePreStart() error {
	return i.PostRefresh()
}

func (i *Installer) RestorePostStart() error {
	return i.Configure()
}
