package stalwart

type DkimSignature struct {
	Id         string    `json:"id,omitempty"`
	Type       string    `json:"@type"`
	DomainId   string    `json:"domainId"`
	Selector   string    `json:"selector"`
	PrivateKey FileValue `json:"privateKey"`
	Stage      string    `json:"stage"`
}
