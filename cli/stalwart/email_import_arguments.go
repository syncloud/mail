package stalwart

type EmailImportArguments struct {
	AccountId string                 `json:"accountId"`
	Emails    map[string]EmailImport `json:"emails"`
}
