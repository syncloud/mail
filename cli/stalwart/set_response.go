package stalwart

import (
	"errors"
	"fmt"
)

type SetResponse struct {
	Created      map[string]Created  `json:"created"`
	NotCreated   map[string]SetError `json:"notCreated"`
	NotUpdated   map[string]SetError `json:"notUpdated"`
	NotDestroyed map[string]SetError `json:"notDestroyed"`
}

func (s *SetResponse) Err() error {
	var errs []error
	for id, failure := range s.NotCreated {
		errs = append(errs, fmt.Errorf("create %s: %s", id, failure))
	}
	for id, failure := range s.NotUpdated {
		errs = append(errs, fmt.Errorf("update %s: %s", id, failure))
	}
	for id, failure := range s.NotDestroyed {
		errs = append(errs, fmt.Errorf("destroy %s: %s", id, failure))
	}
	return errors.Join(errs...)
}
