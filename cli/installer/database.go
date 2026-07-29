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
	backupFile  string
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
		backupFile:  path.Join(dataDir, "database.dump.sql"),
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

func (d *Database) pgDumpAll() string {
	return path.Join(d.appDir, "postgresql", "bin", "pg_dumpall.sh")
}

// Backup, Remove and Restore are always run around a refresh rather than only
// when the postgres version changes, so that a major version bump needs no
// detection and no in place upgrade: the cluster is simply rebuilt from a dump
// the previous version produced.
func (d *Database) Backup() error {
	if _, err := os.Stat(d.databaseDir); os.IsNotExist(err) {
		return nil
	}
	d.logger.Info("dumping database")
	_, err := d.executor.RunDir("", d.pgDumpAll(), "-U", d.user, "-h", d.databaseDir, "-f", d.backupFile)
	return err
}

// Rebuild throws away the cluster the previous revision left behind and starts
// an empty one of the current version, ready for the dump to be loaded once
// postgres is running. It is a no op without a dump to restore from.
func (d *Database) Rebuild() error {
	if _, err := os.Stat(d.backupFile); os.IsNotExist(err) {
		return d.UpdateConfig()
	}
	d.logger.Info("removing old cluster")
	if err := os.RemoveAll(d.databaseDir); err != nil {
		return err
	}
	return d.Init()
}

func (d *Database) Restore() error {
	if _, err := os.Stat(d.backupFile); os.IsNotExist(err) {
		return nil
	}
	d.logger.Info("restoring database")
	if _, err := d.executor.RunDir("", d.psql(), "-U", d.user, "-h", d.databaseDir,
		"-d", "postgres", "-f", d.backupFile); err != nil {
		return err
	}
	return os.Remove(d.backupFile)
}

func (d *Database) psql() string {
	return path.Join(d.appDir, "postgresql", "bin", "psql.sh")
}

func (d *Database) Init() error {
	d.logger.Info("initializing database")
	initdb := path.Join(d.appDir, "postgresql", "bin", "initdb.sh")
	// postgres 15 and later can default to the icu locale provider, whose data
	// files are not reachable from these relocated binaries, so ask for libc
	if _, err := d.executor.RunDir("", "sudo", "-H", "-u", d.user, initdb,
		"--locale-provider=libc", "--encoding=UTF8", d.databaseDir); err != nil {
		return err
	}
	return d.UpdateConfig()
}

func (d *Database) UpdateConfig() error {
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
