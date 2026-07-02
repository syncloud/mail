package installer

import (
	"bufio"
	"fmt"
	"os"
	"path"
	"strings"
)

func (i *Installer) userConfigFile() string {
	return path.Join(i.dataDir, "user_mail.cfg")
}

func (i *Installer) isActivated() (bool, error) {
	value, found, err := readIniValue(i.userConfigFile(), "mail", "activated")
	if err != nil {
		return false, err
	}
	if !found {
		return false, nil
	}
	return strings.EqualFold(value, "true"), nil
}

func (i *Installer) setActivated(activated bool) error {
	value := "false"
	if activated {
		value = "true"
	}
	return writeIniValue(i.userConfigFile(), "mail", "activated", value)
}

func readIniValue(filename, section, key string) (string, bool, error) {
	file, err := os.Open(filename)
	if os.IsNotExist(err) {
		return "", false, nil
	}
	if err != nil {
		return "", false, err
	}
	defer file.Close()

	currentSection := ""
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, ";") {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			currentSection = strings.TrimSpace(line[1 : len(line)-1])
			continue
		}
		if currentSection != section {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		if strings.TrimSpace(parts[0]) == key {
			return strings.TrimSpace(parts[1]), true, nil
		}
	}
	if err := scanner.Err(); err != nil {
		return "", false, err
	}
	return "", false, nil
}

func writeIniValue(filename, section, key, value string) error {
	f, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := fmt.Fprintf(f, "[%s]\n%s = %s\n", section, key, value); err != nil {
		return err
	}
	return nil
}
