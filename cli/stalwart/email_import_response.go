package stalwart

type EmailImportResponse struct {
	Created    map[string]Created  `json:"created"`
	NotCreated map[string]SetError `json:"notCreated"`
}
