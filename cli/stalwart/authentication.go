package stalwart

type Authentication struct {
	DirectoryId         string          `json:"directoryId"`
	DefaultUserRoleIds  map[string]bool `json:"defaultUserRoleIds"`
	DefaultGroupRoleIds map[string]bool `json:"defaultGroupRoleIds"`
	DefaultAdminRoleIds map[string]bool `json:"defaultAdminRoleIds"`
}
