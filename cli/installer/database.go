package installer

import (
	"fmt"
	"os"
	"path"

	"go.uber.org/zap"
)

type Database struct {
	appDir      string
	databaseDir string
	configDir   string
	name        string
	user        string
	password    string
	port        int
	initFile    string
	executor    *Executor
	logger      *zap.Logger
}

func NewDatabase(appDir, dataDir, configDir, name, user, password string, port int, executor *Executor, logger *zap.Logger) *Database {
	return &Database{
		appDir:      appDir,
		databaseDir: path.Join(dataDir, "database"),
		configDir:   configDir,
		name:        name,
		user:        user,
		password:    password,
		port:        port,
		initFile:    path.Join(appDir, "roundcubemail", "SQL", "postgres.initial.sql"),
		executor:    executor,
		logger:      logger,
	}
}

func (d *Database) Dir() string {
	return d.databaseDir
}

func (d *Database) Port() int {
	return d.port
}

func (d *Database) psql() string {
	return path.Join(d.appDir, "postgresql", "bin", "psql.sh")
}

func (d *Database) Init() error {
	d.logger.Info("initializing database")
	initdb := path.Join(d.appDir, "postgresql", "bin", "initdb.sh")
	if _, err := d.executor.RunDir("", "sudo", "-H", "-u", d.user, initdb, d.databaseDir); err != nil {
		return err
	}
	return d.UpdateConfig()
}

func (d *Database) UpdateConfig() error {
	if _, err := os.Stat(d.databaseDir); os.IsNotExist(err) {
		return nil
	}
	src := path.Join(d.configDir, "postgresql", "postgresql.conf")
	dst := path.Join(d.databaseDir, "postgresql.conf")
	content, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, content, 0644)
}

func (d *Database) Create() error {
	d.logger.Info("creating database")
	if err := d.execute("postgres", fmt.Sprintf("ALTER USER %s WITH PASSWORD '%s';", d.user, d.password)); err != nil {
		return err
	}
	if err := d.execute("postgres", fmt.Sprintf("create database %s;", d.name)); err != nil {
		return err
	}
	return d.executeFile(d.name, d.initFile)
}

func (d *Database) execute(database, sql string) error {
	d.logger.Info("executing", zap.String("sql", sql))
	_, err := d.executor.RunDir("", d.psql(), "-U", d.user, "-h", d.databaseDir, "-d", database, "-c", sql)
	return err
}

func (d *Database) executeFile(database, file string) error {
	d.logger.Info("executing", zap.String("file", file))
	_, err := d.executor.RunDir("", d.psql(), "-U", d.user, "-h", d.databaseDir, "-d", database, "-f", file)
	return err
}
