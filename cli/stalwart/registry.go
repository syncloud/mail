package stalwart

import (
	"encoding/json"
	"fmt"
)

func List[T any](client *Client, accountId, object string) ([]T, error) {
	return get[T](client, object, GetArguments{AccountId: accountId})
}

func Singleton[T any](client *Client, accountId, object string) (T, error) {
	var empty T
	list, err := get[T](client, object, GetArguments{AccountId: accountId, Ids: []string{"singleton"}})
	if err != nil {
		return empty, err
	}
	if len(list) != 1 {
		return empty, fmt.Errorf("%s singleton not found", object)
	}
	return list[0], nil
}

func Create[T any](client *Client, accountId, object string, value T) (string, error) {
	result, err := set(client, object, SetArguments[T]{AccountId: accountId, Create: map[string]T{"new": value}})
	if err != nil {
		return "", err
	}
	created, ok := result.Created["new"]
	if !ok {
		return "", fmt.Errorf("%s was not created", object)
	}
	return created.Id, nil
}

func Update[T any](client *Client, accountId, object, id string, value T) error {
	_, err := set(client, object, SetArguments[T]{AccountId: accountId, Update: map[string]T{id: value}})
	return err
}

func Destroy(client *Client, accountId, object string, ids ...string) error {
	if len(ids) == 0 {
		return nil
	}
	_, err := set(client, object, SetArguments[Variant]{AccountId: accountId, Destroy: ids})
	return err
}

func get[T any](client *Client, object string, arguments GetArguments) ([]T, error) {
	responses, err := client.Call(MethodCall{Name: object + "/get", Arguments: arguments, Id: "0"})
	if err != nil {
		return nil, err
	}
	var response GetResponse[T]
	if err := json.Unmarshal(responses[0].Arguments, &response); err != nil {
		return nil, err
	}
	return response.List, nil
}

func set[T any](client *Client, object string, arguments SetArguments[T]) (*SetResponse, error) {
	responses, err := client.Call(MethodCall{Name: object + "/set", Arguments: arguments, Id: "0"})
	if err != nil {
		return nil, err
	}
	var response SetResponse
	if err := json.Unmarshal(responses[0].Arguments, &response); err != nil {
		return nil, err
	}
	if err := response.Err(); err != nil {
		return nil, fmt.Errorf("%s/set: %w", object, err)
	}
	return &response, nil
}
