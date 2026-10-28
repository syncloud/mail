package stalwart

type FileValue struct {
	Type     string `json:"@type"`
	FilePath string `json:"filePath"`
}

func File(path string) FileValue {
	return FileValue{Type: "File", FilePath: path}
}
