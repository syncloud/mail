package migration

import (
	"bufio"
	"os"
	"strconv"
	"strings"
)

type Keywords map[int]string

func LoadKeywords(path string) (Keywords, error) {
	keywords := Keywords{}
	file, err := os.Open(path)
	if os.IsNotExist(err) {
		return keywords, nil
	}
	if err != nil {
		return nil, err
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		index, keyword, ok := strings.Cut(strings.TrimSpace(scanner.Text()), " ")
		if !ok {
			continue
		}
		position, err := strconv.Atoi(index)
		if err != nil {
			continue
		}
		keywords[position] = keyword
	}
	return keywords, scanner.Err()
}
