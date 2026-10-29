package stalwart

type Session struct {
	PrimaryAccounts map[string]string `json:"primaryAccounts"`
	Username        string            `json:"username"`
}

func (s *Session) AccountId() string {
	return s.PrimaryAccounts["urn:ietf:params:jmap:mail"]
}
