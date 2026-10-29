package stalwart

import (
	"fmt"
	"strings"
)

type SetError struct {
	Type        string   `json:"type"`
	Description string   `json:"description"`
	Properties  []string `json:"properties"`
}

func (s SetError) String() string {
	return fmt.Sprintf("%s %s [%s]", s.Type, s.Description, strings.Join(s.Properties, ", "))
}
