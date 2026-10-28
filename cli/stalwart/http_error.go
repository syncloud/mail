package stalwart

import "fmt"

type HttpError struct {
	Method string
	Path   string
	Status int
	Body   string
}

func (e *HttpError) Error() string {
	return fmt.Sprintf("%s %s: %d %s", e.Method, e.Path, e.Status, e.Body)
}

func (e *HttpError) Unauthorized() bool {
	return e.Status == 401 || e.Status == 403
}
