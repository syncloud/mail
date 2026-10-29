package installer

type SidebarApp struct {
	Id           string `json:"id"`
	Name         string `json:"name"`
	Url          string `json:"url"`
	Icon         string `json:"icon"`
	OpenMode     string `json:"openMode"`
	ShowOnMobile bool   `json:"showOnMobile"`
}
