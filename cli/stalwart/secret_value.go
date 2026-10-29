package stalwart

type SecretValue struct {
	Type   string `json:"@type"`
	Secret string `json:"secret"`
}

func Secret(value string) SecretValue {
	return SecretValue{Type: "Value", Secret: value}
}
