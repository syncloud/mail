package stalwart

type Expression struct {
	Match map[string]ExpressionMatch `json:"match"`
	Else  string                     `json:"else"`
}
