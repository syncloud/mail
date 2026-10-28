package stalwart

type HttpSettings struct {
	ClientIpSource string `json:"clientIpSource"`
	ForwardedHops  int    `json:"forwardedHops"`
}
