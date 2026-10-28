package stalwart

type Mailbox struct {
	Id       string `json:"id"`
	Name     string `json:"name"`
	ParentId string `json:"parentId"`
	Role     string `json:"role"`
}
