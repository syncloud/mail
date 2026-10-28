package migration

import (
	"bufio"
	"os"
	"strings"
)

type RoundcubeDump struct {
	path string
}

func NewRoundcubeDump(path string) *RoundcubeDump {
	return &RoundcubeDump{path: path}
}

func (r *RoundcubeDump) Contacts() (map[string][]Contact, error) {
	file, err := os.Open(r.path)
	if os.IsNotExist(err) {
		return map[string][]Contact{}, nil
	}
	if err != nil {
		return nil, err
	}
	defer file.Close()

	users := map[string]string{}
	var rows []map[string]string
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 1024*1024), 64*1024*1024)
	var table string
	var columns []string
	for scanner.Scan() {
		line := scanner.Text()
		if table == "" {
			table, columns = copyHeader(line)
			continue
		}
		if line == `\.` {
			table = ""
			continue
		}
		row := map[string]string{}
		for index, value := range strings.Split(line, "\t") {
			if index < len(columns) {
				row[columns[index]] = unescapeCopy(value)
			}
		}
		switch table {
		case "users":
			users[row["user_id"]] = row["username"]
		case "contacts":
			rows = append(rows, row)
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}

	contacts := map[string][]Contact{}
	for _, row := range rows {
		if row["del"] == "1" || row["del"] == "t" {
			continue
		}
		username, ok := users[row["user_id"]]
		if !ok {
			continue
		}
		contact := Contact{
			Id:    row["contact_id"],
			Name:  row["name"],
			Email: row["email"],
			VCard: row["vcard"],
		}
		contacts[username] = append(contacts[username], contact)
	}
	return contacts, nil
}

func copyHeader(line string) (string, []string) {
	if !strings.HasPrefix(line, "COPY ") || !strings.HasSuffix(line, "FROM stdin;") {
		return "", nil
	}
	rest := strings.TrimPrefix(line, "COPY ")
	name, rest, ok := strings.Cut(rest, " (")
	if !ok {
		return "", nil
	}
	list, _, ok := strings.Cut(rest, ") FROM stdin;")
	if !ok {
		return "", nil
	}
	name = strings.TrimPrefix(name, "public.")
	var columns []string
	for _, column := range strings.Split(list, ",") {
		columns = append(columns, strings.Trim(strings.TrimSpace(column), `"`))
	}
	if name != "users" && name != "contacts" {
		return "skip", columns
	}
	return name, columns
}

func unescapeCopy(value string) string {
	if value == `\N` {
		return ""
	}
	var out strings.Builder
	for index := 0; index < len(value); index++ {
		if value[index] != '\\' || index+1 == len(value) {
			out.WriteByte(value[index])
			continue
		}
		index++
		switch value[index] {
		case 'n':
			out.WriteByte('\n')
		case 'r':
			out.WriteByte('\r')
		case 't':
			out.WriteByte('\t')
		default:
			out.WriteByte(value[index])
		}
	}
	return out.String()
}
