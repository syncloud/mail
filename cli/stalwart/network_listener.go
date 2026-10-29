package stalwart

type NetworkListener struct {
	Id          string          `json:"id,omitempty"`
	Name        string          `json:"name,omitempty"`
	Bind        map[string]bool `json:"bind"`
	Protocol    string          `json:"protocol"`
	UseTls      bool            `json:"useTls"`
	ImplicitTls bool            `json:"implicitTls"`
	ProxyTrust  map[string]bool `json:"overrideProxyTrustedNetworks"`
}
