package stalwart

type GetResponse[T any] struct {
	List     []T      `json:"list"`
	NotFound []string `json:"notFound"`
}
