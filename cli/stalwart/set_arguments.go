package stalwart

type SetArguments[T any] struct {
	AccountId string       `json:"accountId"`
	Create    map[string]T `json:"create,omitempty"`
	Update    map[string]T `json:"update,omitempty"`
	Destroy   []string     `json:"destroy,omitempty"`
}
