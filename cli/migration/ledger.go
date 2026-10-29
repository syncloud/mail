package migration

import (
	"bufio"
	"os"
)

type Ledger struct {
	path     string
	imported map[string]bool
}

func LoadLedger(path string) (*Ledger, error) {
	ledger := &Ledger{path: path, imported: map[string]bool{}}
	file, err := os.Open(path)
	if os.IsNotExist(err) {
		return ledger, nil
	}
	if err != nil {
		return nil, err
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		ledger.imported[scanner.Text()] = true
	}
	return ledger, scanner.Err()
}

func (l *Ledger) Has(key string) bool {
	return l.imported[key]
}

func (l *Ledger) Add(key string) error {
	file, err := os.OpenFile(l.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	if _, err := file.WriteString(key + "\n"); err != nil {
		file.Close()
		return err
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return err
	}
	l.imported[key] = true
	return file.Close()
}
