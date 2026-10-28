package stalwart

type RelayRoute struct {
	Id                string      `json:"id,omitempty"`
	Type              string      `json:"@type"`
	Name              string      `json:"name,omitempty"`
	Description       string      `json:"description"`
	Host              string      `json:"host"`
	Port              int         `json:"port"`
	Protocol          string      `json:"protocol"`
	ImplicitTls       bool        `json:"implicitTls"`
	AllowInvalidCerts bool        `json:"allowInvalidCerts"`
	AuthUsername      string      `json:"authUsername"`
	AuthSecret        SecretValue `json:"authSecret"`
}
