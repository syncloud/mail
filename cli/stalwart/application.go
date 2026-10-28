package stalwart

type Application struct {
	Id                 string          `json:"id,omitempty"`
	Enable             bool            `json:"enable"`
	Description        string          `json:"description"`
	ResourceUrl        string          `json:"resourceUrl"`
	UrlPrefix          map[string]bool `json:"urlPrefix"`
	UnpackDirectory    string          `json:"unpackDirectory"`
	AutoUpdateInterval int64           `json:"autoUpdateInterval"`
}
