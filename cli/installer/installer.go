package installer

import (
	"fmt"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/syncloud/golib/config"
	"github.com/syncloud/golib/linux"
	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

const (
	App            = "mail"
	UserName       = "mail"
	PsqlPort       = 5432
	DbName         = "mail"
	DbUser         = "mail"
	DbPass         = "mail"
	SystemdDovecot = "mail.dovecot"
)

var dkimKeyPattern = regexp.MustCompile(`(?s).*p=(.*?)".*`)

type Variables struct {
	AppDir           string
	AppDataDir       string
	DbPsqlPath       string
	DbPsqlPort       int
	DbName           string
	DbUser           string
	DbPassword       string
	PlatformDataDir  string
	DeviceDomainName string
	AppDomainName    string
	Timezone         string
}

type Installer struct {
	appDir             string
	dataDir            string
	configPath         string
	databasePath       string
	logDir             string
	opendkimDir        string
	opendkimKeysDir    string
	platformClient     *platform.Client
	mailPlatformClient *PlatformClient
	executor           *Executor
	logger             *zap.Logger
}

func New(logger *zap.Logger) *Installer {
	appDir := fmt.Sprintf("/snap/%s/current", App)
	dataDir := fmt.Sprintf("/var/snap/%s/current", App)
	return &Installer{
		appDir:             appDir,
		dataDir:            dataDir,
		configPath:         path.Join(dataDir, "config"),
		databasePath:       path.Join(dataDir, "database"),
		logDir:             path.Join(dataDir, "log"),
		opendkimDir:        path.Join(dataDir, "opendkim"),
		opendkimKeysDir:    path.Join(dataDir, "opendkim", "keys"),
		platformClient:     platform.New(),
		mailPlatformClient: NewPlatformClient(logger),
		executor:           NewExecutor(logger),
		logger:             logger,
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
	deviceDomainName, err := i.mailPlatformClient.GetDeviceDomainName()
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

	variables := Variables{
		AppDir:           i.appDir,
		AppDataDir:       i.dataDir,
		DbPsqlPath:       i.databasePath,
		DbPsqlPort:       PsqlPort,
		DbName:           DbName,
		DbUser:           DbUser,
		DbPassword:       DbPass,
		PlatformDataDir:  i.platformDataDir(),
		DeviceDomainName: deviceDomainName,
		AppDomainName:    appDomainName,
		Timezone:         tz,
	}

	templatesPath := path.Join(i.appDir, "config")
	if err := config.Generate(templatesPath, i.configPath, variables); err != nil {
		return err
	}

	return linux.Chown(i.configPath, UserName)
}

func (i *Installer) InitConfig() error {
	if err := linux.CreateUser("maildrop"); err != nil {
		return err
	}
	if err := linux.CreateUser("dovecot"); err != nil {
		return err
	}
	if err := linux.CreateUser(UserName); err != nil {
		return err
	}

	if err := os.MkdirAll(path.Join(i.dataDir, "nginx"), 0755); err != nil {
		return err
	}

	if err := i.RegenerateConfigs(); err != nil {
		return err
	}

	deviceDomainName, err := i.mailPlatformClient.GetDeviceDomainName()
	if err != nil {
		return err
	}
	opendkimKeysDomainDir := path.Join(i.opendkimKeysDir, deviceDomainName)

	dataDirs := []string{
		path.Join(i.dataDir, "config"),
		i.logDir,
		path.Join(i.dataDir, "spool"),
		path.Join(i.dataDir, "dovecot"),
		path.Join(i.dataDir, "dovecot", "private"),
		path.Join(i.dataDir, "data"),
		i.opendkimDir,
		i.opendkimKeysDir,
		opendkimKeysDomainDir,
	}
	for _, dataDir := range dataDirs {
		if err := os.MkdirAll(dataDir, 0755); err != nil {
			return err
		}
	}

	dkimKey, err := i.GenerateDkimKey(deviceDomainName, opendkimKeysDomainDir)
	if err != nil {
		return err
	}
	if err := i.mailPlatformClient.SetDkimKey(dkimKey); err != nil {
		return err
	}

	if err := linux.Chown(i.dataDir, UserName); err != nil {
		return err
	}

	boxDataDir := path.Join(i.dataDir, "box")
	if err := os.MkdirAll(boxDataDir, 0755); err != nil {
		return err
	}
	if _, err := i.executor.Run("chown", "-R", "dovecot:dovecot", boxDataDir); err != nil {
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
	return i.DatabaseInit()
}

func (i *Installer) PostRefresh() error {
	if err := i.InitConfig(); err != nil {
		return err
	}
	logs, err := filepath.Glob(path.Join(i.logDir, "*.log"))
	if err != nil {
		return err
	}
	for _, logFile := range logs {
		if err := os.Remove(logFile); err != nil {
			return err
		}
	}
	return nil
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

func (i *Installer) DatabaseInit() error {
	i.logger.Info("initializing database")
	psqlInitdb := path.Join(i.appDir, "postgresql", "bin", "initdb.sh")
	if _, err := i.executor.Run("sudo", "-H", "-u", UserName, psqlInitdb, i.databasePath); err != nil {
		return err
	}
	postgresqlConfFrom := path.Join(i.dataDir, "config", "postgresql", "postgresql.conf")
	postgresqlConfTo := path.Join(i.databasePath, "postgresql.conf")
	content, err := os.ReadFile(postgresqlConfFrom)
	if err != nil {
		return err
	}
	return os.WriteFile(postgresqlConfTo, content, 0644)
}

func (i *Installer) Initialize() error {
	i.logger.Info("initialization")
	if err := i.executeSql(
		fmt.Sprintf("ALTER USER %s WITH PASSWORD '%s';", DbUser, DbUser),
		"postgres",
	); err != nil {
		return err
	}
	if err := i.executeSql(fmt.Sprintf("create database %s;", DbName), "postgres"); err != nil {
		return err
	}
	dbInitFile := path.Join(i.appDir, "roundcubemail", "SQL", "postgres.initial.sql")
	if err := i.executeFile(dbInitFile, DbName); err != nil {
		return err
	}
	return i.setActivated(true)
}

func (i *Installer) psql() string {
	return path.Join(i.appDir, "postgresql", "bin", "psql.sh")
}

func (i *Installer) executeSql(sql, database string) error {
	i.logger.Info("executing", zap.String("sql", sql))
	_, err := i.executor.Run(i.psql(),
		"-U", DbUser, "-h", i.databasePath, "-d", database, "-c", sql)
	return err
}

func (i *Installer) executeFile(file, database string) error {
	i.logger.Info("executing", zap.String("file", file))
	_, err := i.executor.Run(i.psql(),
		"-U", DbUser, "-h", i.databasePath, "-d", database, "-f", file)
	return err
}

func (i *Installer) PrepareStorage() error {
	appStorageDir, err := i.platformClient.InitStorage(App, UserName)
	if err != nil {
		return err
	}
	tmpStoragePath := path.Join(appStorageDir, "tmp")
	if err := os.MkdirAll(tmpStoragePath, 0755); err != nil {
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
