package stalwart

type Certificate struct {
	Id          string    `json:"id,omitempty"`
	Certificate FileValue `json:"certificate"`
	PrivateKey  FileValue `json:"privateKey"`
}
