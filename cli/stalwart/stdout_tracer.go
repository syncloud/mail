package stalwart

type StdoutTracer struct {
	Id        string `json:"id,omitempty"`
	Type      string `json:"@type"`
	Enable    bool   `json:"enable"`
	Level     string `json:"level"`
	Ansi      bool   `json:"ansi"`
	Multiline bool   `json:"multiline"`
}
