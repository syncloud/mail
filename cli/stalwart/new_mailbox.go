package stalwart

type NewMailbox struct {
	Name     string  `json:"name"`
	ParentId *string `json:"parentId"`
}
