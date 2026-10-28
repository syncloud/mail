package stalwart

import "encoding/json"

type MethodCall struct {
	Name      string
	Arguments any
	Id        string
}

func (m MethodCall) MarshalJSON() ([]byte, error) {
	return json.Marshal([]any{m.Name, m.Arguments, m.Id})
}
