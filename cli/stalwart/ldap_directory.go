package stalwart

type LdapDirectory struct {
	Id                 string          `json:"id,omitempty"`
	Type               string          `json:"@type"`
	Description        string          `json:"description"`
	Url                string          `json:"url"`
	UseTls             bool            `json:"useTls"`
	BaseDn             string          `json:"baseDn"`
	BindDn             string          `json:"bindDn"`
	BindSecret         SecretValue     `json:"bindSecret"`
	BindAuthentication bool            `json:"bindAuthentication"`
	FilterLogin        string          `json:"filterLogin"`
	FilterRecipient    string          `json:"filterRecipient"`
	FilterMemberOf     string          `json:"filterMemberOf"`
	AttrEmail          map[string]bool `json:"attrEmail"`
}
