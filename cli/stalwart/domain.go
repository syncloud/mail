package stalwart

type Domain struct {
	Id                    string  `json:"id,omitempty"`
	Name                  string  `json:"name,omitempty"`
	Enable                bool    `json:"enable"`
	DkimManagement        Variant `json:"dkimManagement"`
	CertificateManagement Variant `json:"certificateManagement"`
	DnsManagement         Variant `json:"dnsManagement"`
}
