package stalwart

import (
	"encoding/json"
	"fmt"
)

type MethodResponse struct {
	Name      string
	Arguments json.RawMessage
	Id        string
}

func (m *MethodResponse) UnmarshalJSON(data []byte) error {
	var parts []json.RawMessage
	if err := json.Unmarshal(data, &parts); err != nil {
		return err
	}
	if len(parts) != 3 {
		return fmt.Errorf("method response has %d parts", len(parts))
	}
	if err := json.Unmarshal(parts[0], &m.Name); err != nil {
		return err
	}
	m.Arguments = parts[1]
	return json.Unmarshal(parts[2], &m.Id)
}
