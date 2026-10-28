package stalwart

import (
	"fmt"

	"go.uber.org/zap"
)

const (
	DirectoryDescription = "syncloud"
	RelayRouteName       = "relay"
	DkimSelector         = "mail"
	AdminGroup           = "syncloud"
	HttpBind             = "127.0.0.1:443"
	TunnelBind           = "127.0.0.1:25"
)

type Provisioner struct {
	client *Client
	logger *zap.Logger
}

func NewProvisioner(client *Client, logger *zap.Logger) *Provisioner {
	return &Provisioner{client: client, logger: logger}
}

func (p *Provisioner) Apply(settings Settings) error {
	accountId, err := p.accountId()
	if err != nil {
		return err
	}
	if err := p.tracer(accountId); err != nil {
		return err
	}
	if err := p.listeners(accountId); err != nil {
		return err
	}
	directoryId, err := p.directory(accountId, settings)
	if err != nil {
		return err
	}
	certificateId, err := p.certificate(accountId, settings)
	if err != nil {
		return err
	}
	if err := p.authentication(accountId, directoryId); err != nil {
		return err
	}
	domainId, err := p.domain(accountId, settings)
	if err != nil {
		return err
	}
	if err := p.dkim(accountId, settings, domainId); err != nil {
		return err
	}
	if err := Update(p.client, accountId, "x:SystemSettings", "singleton", SystemSettings{
		DefaultHostname:      settings.AppDomain,
		DefaultDomainId:      domainId,
		DefaultCertificateId: certificateId,
	}); err != nil {
		return err
	}
	if err := Update(p.client, accountId, "x:Http", "singleton", HttpSettings{
		ClientIpSource: "xForwardedFor",
		ForwardedHops:  1,
	}); err != nil {
		return err
	}
	if err := p.webUi(accountId, settings); err != nil {
		return err
	}
	if err := Update(p.client, accountId, "x:SpamSettings", "singleton", SpamSettings{
		SpamFilterRulesUrl: "file://" + settings.SpamRules,
	}); err != nil {
		return err
	}
	return p.relay(accountId, settings.Relay)
}

func (p *Provisioner) ApplyRelay(relay Relay) error {
	accountId, err := p.accountId()
	if err != nil {
		return err
	}
	if err := p.relay(accountId, relay); err != nil {
		return err
	}
	return p.action(accountId, "ReloadSettings")
}

func (p *Provisioner) ReloadCertificates() error {
	accountId, err := p.accountId()
	if err != nil {
		return err
	}
	return p.action(accountId, "ReloadTlsCertificates")
}

func (p *Provisioner) action(accountId, action string) error {
	_, err := Create(p.client, accountId, "x:Action", Variant{Type: action})
	return err
}

func (p *Provisioner) accountId() (string, error) {
	session, err := p.client.Session()
	if err != nil {
		return "", err
	}
	accountId := session.AccountId()
	if accountId == "" {
		return "", fmt.Errorf("stalwart session has no account")
	}
	return accountId, nil
}

func (p *Provisioner) tracer(accountId string) error {
	tracers, err := List[StdoutTracer](p.client, accountId, "x:Tracer")
	if err != nil {
		return err
	}
	tracer := StdoutTracer{Type: "Stdout", Enable: true, Level: "info"}
	var stale []string
	var existing string
	for _, current := range tracers {
		if current.Type == "Stdout" && existing == "" {
			existing = current.Id
			continue
		}
		stale = append(stale, current.Id)
	}
	if err := Destroy(p.client, accountId, "x:Tracer", stale...); err != nil {
		return err
	}
	if existing != "" {
		return Update(p.client, accountId, "x:Tracer", existing, tracer)
	}
	_, err = Create(p.client, accountId, "x:Tracer", tracer)
	return err
}

func (p *Provisioner) listeners(accountId string) error {
	wanted := []NetworkListener{
		{Name: "smtp", Bind: bind("[::]:25"), Protocol: "smtp", UseTls: true},
		{Name: "submission", Bind: bind("[::]:587"), Protocol: "smtp", UseTls: true},
		{Name: "submissions", Bind: bind("[::]:465"), Protocol: "smtp", UseTls: true, ImplicitTls: true},
		{Name: "imap", Bind: bind("[::]:143"), Protocol: "imap", UseTls: true},
		{Name: "imaps", Bind: bind("[::]:993"), Protocol: "imap", UseTls: true, ImplicitTls: true},
		{Name: "pop3", Bind: bind("[::]:110"), Protocol: "pop3", UseTls: true},
		{Name: "pop3s", Bind: bind("[::]:995"), Protocol: "pop3", UseTls: true, ImplicitTls: true},
		{Name: "sieve", Bind: bind("[::]:4190"), Protocol: "manageSieve", UseTls: true},
		{Name: "http", Bind: bind(HttpBind), Protocol: "http"},
		{Name: "tunnel", Bind: bind(TunnelBind), Protocol: "smtp"},
	}
	current, err := List[NetworkListener](p.client, accountId, "x:NetworkListener")
	if err != nil {
		return err
	}
	byName := map[string]string{}
	var stale []string
	for _, listener := range current {
		if _, seen := byName[listener.Name]; seen {
			stale = append(stale, listener.Id)
			continue
		}
		byName[listener.Name] = listener.Id
	}
	for _, listener := range wanted {
		id, ok := byName[listener.Name]
		delete(byName, listener.Name)
		if ok {
			listener.Name = ""
			if err := Update(p.client, accountId, "x:NetworkListener", id, listener); err != nil {
				return err
			}
			continue
		}
		if _, err := Create(p.client, accountId, "x:NetworkListener", listener); err != nil {
			return err
		}
	}
	for _, id := range byName {
		stale = append(stale, id)
	}
	return Destroy(p.client, accountId, "x:NetworkListener", stale...)
}

func (p *Provisioner) directory(accountId string, settings Settings) (string, error) {
	filter := "(&(objectClass=inetOrgPerson)(cn={local}))"
	directory := LdapDirectory{
		Type:               "Ldap",
		Description:        DirectoryDescription,
		Url:                settings.LdapUrl,
		BaseDn:             "dc=syncloud,dc=org",
		BindDn:             settings.LdapBindDn,
		BindSecret:         Secret(settings.LdapBindPassword),
		BindAuthentication: true,
		FilterLogin:        filter,
		FilterRecipient:    filter,
		FilterMemberOf:     "(&(objectClass=posixGroup)(cn=" + AdminGroup + ")(memberUid={rdn}))",
		AttrEmail:          map[string]bool{"cn": true},
	}
	current, err := List[NamedObject](p.client, accountId, "x:Directory")
	if err != nil {
		return "", err
	}
	for _, existing := range current {
		if existing.Description == DirectoryDescription {
			return existing.Id, Update(p.client, accountId, "x:Directory", existing.Id, directory)
		}
	}
	return Create(p.client, accountId, "x:Directory", directory)
}

func (p *Provisioner) authentication(accountId, directoryId string) error {
	roles, err := List[NamedObject](p.client, accountId, "x:Role")
	if err != nil {
		return err
	}
	byDescription := map[string]string{}
	for _, role := range roles {
		byDescription[role.Description] = role.Id
	}
	authentication := Authentication{DirectoryId: directoryId}
	roleIds := func(descriptions ...string) (map[string]bool, error) {
		ids := map[string]bool{}
		for _, description := range descriptions {
			id, ok := byDescription[description]
			if !ok {
				return nil, fmt.Errorf("stalwart has no %s role", description)
			}
			ids[id] = true
		}
		return ids, nil
	}
	if authentication.DefaultUserRoleIds, err = roleIds("User"); err != nil {
		return err
	}
	if authentication.DefaultGroupRoleIds, err = roleIds("Group"); err != nil {
		return err
	}
	if authentication.DefaultAdminRoleIds, err = roleIds("System Administrator", "User"); err != nil {
		return err
	}
	return Update(p.client, accountId, "x:Authentication", "singleton", authentication)
}

func (p *Provisioner) certificate(accountId string, settings Settings) (string, error) {
	certificate := Certificate{
		Certificate: File(settings.CertificateFile),
		PrivateKey:  File(settings.KeyFile),
	}
	current, err := List[NamedObject](p.client, accountId, "x:Certificate")
	if err != nil {
		return "", err
	}
	if len(current) > 0 {
		return current[0].Id, Update(p.client, accountId, "x:Certificate", current[0].Id, certificate)
	}
	return Create(p.client, accountId, "x:Certificate", certificate)
}

func (p *Provisioner) domain(accountId string, settings Settings) (string, error) {
	domain := Domain{
		Name:                  settings.DeviceDomain,
		Enable:                true,
		DkimManagement:        Variant{Type: "Manual"},
		CertificateManagement: Variant{Type: "Manual"},
		DnsManagement:         Variant{Type: "Manual"},
	}
	current, err := List[NamedObject](p.client, accountId, "x:Domain")
	if err != nil {
		return "", err
	}
	for _, existing := range current {
		if existing.Name == settings.DeviceDomain {
			domain.Name = ""
			return existing.Id, Update(p.client, accountId, "x:Domain", existing.Id, domain)
		}
	}
	return Create(p.client, accountId, "x:Domain", domain)
}

func (p *Provisioner) dkim(accountId string, settings Settings, domainId string) error {
	signature := DkimSignature{
		Type:       "Dkim1RsaSha256",
		DomainId:   domainId,
		Selector:   DkimSelector,
		PrivateKey: File(settings.DkimKeyFile),
		Stage:      "active",
	}
	current, err := List[DkimSignature](p.client, accountId, "x:DkimSignature")
	if err != nil {
		return err
	}
	var stale []string
	var existing string
	for _, candidate := range current {
		if candidate.DomainId == domainId && candidate.Selector == DkimSelector && existing == "" {
			existing = candidate.Id
			continue
		}
		stale = append(stale, candidate.Id)
	}
	if err := Destroy(p.client, accountId, "x:DkimSignature", stale...); err != nil {
		return err
	}
	if existing != "" {
		return Update(p.client, accountId, "x:DkimSignature", existing, signature)
	}
	_, err = Create(p.client, accountId, "x:DkimSignature", signature)
	return err
}

func (p *Provisioner) webUi(accountId string, settings Settings) error {
	application := Application{
		Enable:             true,
		Description:        "Stalwart Web Interface",
		ResourceUrl:        "file://" + settings.WebUiArchive,
		UrlPrefix:          map[string]bool{"/stalwart": true},
		UnpackDirectory:    settings.WebUiDirectory,
		AutoUpdateInterval: 7776000000,
	}
	current, err := List[NamedObject](p.client, accountId, "x:Application")
	if err != nil {
		return err
	}
	if len(current) > 0 {
		return Update(p.client, accountId, "x:Application", current[0].Id, application)
	}
	_, err = Create(p.client, accountId, "x:Application", application)
	return err
}

func (p *Provisioner) relay(accountId string, relay Relay) error {
	current, err := List[NamedObject](p.client, accountId, "x:MtaRoute")
	if err != nil {
		return err
	}
	existing := ""
	for _, route := range current {
		if route.Name == RelayRouteName {
			existing = route.Id
		}
	}
	remote := "'mx'"
	if relay.Enabled {
		route := RelayRoute{
			Type:              "Relay",
			Name:              RelayRouteName,
			Description:       "Syncloud mail relay",
			Host:              relay.Host,
			Port:              relay.Port,
			Protocol:          "smtp",
			ImplicitTls:       true,
			AllowInvalidCerts: true,
			AuthUsername:      relay.Login,
			AuthSecret:        Secret(relay.Password),
		}
		if existing != "" {
			route.Name = ""
			err = Update(p.client, accountId, "x:MtaRoute", existing, route)
		} else {
			_, err = Create(p.client, accountId, "x:MtaRoute", route)
		}
		if err != nil {
			return err
		}
		remote = "'" + RelayRouteName + "'"
	}
	if err := Update(p.client, accountId, "x:MtaOutboundStrategy", "singleton", OutboundStrategy{
		Route: Expression{
			Match: map[string]ExpressionMatch{"0": {If: "is_local_domain(rcpt_domain)", Then: "'local'"}},
			Else:  remote,
		},
	}); err != nil {
		return err
	}
	if !relay.Enabled && existing != "" {
		return Destroy(p.client, accountId, "x:MtaRoute", existing)
	}
	return nil
}

func bind(address string) map[string]bool {
	return map[string]bool{address: true}
}
