package stalwart

type GetArguments struct {
	AccountId string   `json:"accountId"`
	Ids       []string `json:"ids,omitempty"`
}
