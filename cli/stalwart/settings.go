package stalwart

type Settings struct {
	DeviceDomain     string
	AppDomain        string
	HttpSocket       string
	TunnelSocket     string
	LdapUrl          string
	LdapBindDn       string
	LdapBindPassword string
	DkimKeyFile      string
	CertificateFile  string
	KeyFile          string
	WebUiArchive     string
	WebUiDirectory   string
	SpamRules        string
	Relay            Relay
}
