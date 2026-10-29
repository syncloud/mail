package stalwart

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"time"

	"go.uber.org/zap"
)

var capabilities = []string{
	"urn:ietf:params:jmap:core",
	"urn:ietf:params:jmap:mail",
	"urn:ietf:params:jmap:contacts",
	"urn:stalwart:jmap",
}

type Client struct {
	http    *http.Client
	account string
	logger  *zap.Logger
}

func NewClient(socket string, logger *zap.Logger) *Client {
	transport := &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			return (&net.Dialer{}).DialContext(ctx, "unix", socket)
		},
	}
	return &Client{
		http:   &http.Client{Transport: transport, Timeout: 10 * time.Minute},
		logger: logger,
	}
}

func (c *Client) As(account string) *Client {
	return &Client{
		http:    c.http,
		account: account,
		logger:  c.logger,
	}
}

func (c *Client) Wait(timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for {
		_, err := c.Session()
		if err == nil {
			return nil
		}
		if time.Now().After(deadline) {
			return fmt.Errorf("stalwart is not answering: %w", err)
		}
		time.Sleep(time.Second)
	}
}

func (c *Client) Session() (*Session, error) {
	var session Session
	if err := c.do(http.MethodGet, "/jmap/session", "", nil, &session); err != nil {
		return nil, err
	}
	return &session, nil
}

func (c *Client) Call(calls ...MethodCall) ([]MethodResponse, error) {
	body, err := json.Marshal(Request{Using: capabilities, MethodCalls: calls})
	if err != nil {
		return nil, err
	}
	var response Response
	if err := c.do(http.MethodPost, "/jmap/", "application/json", bytes.NewReader(body), &response); err != nil {
		return nil, err
	}
	for _, methodResponse := range response.MethodResponses {
		if methodResponse.Name == "error" {
			return nil, fmt.Errorf("%s failed: %s", methodResponse.Id, string(methodResponse.Arguments))
		}
	}
	return response.MethodResponses, nil
}

func (c *Client) Upload(accountId string, content []byte) (string, error) {
	var upload UploadResponse
	path := fmt.Sprintf("/jmap/upload/%s/", accountId)
	if err := c.do(http.MethodPost, path, "message/rfc822", bytes.NewReader(content), &upload); err != nil {
		return "", err
	}
	return upload.BlobId, nil
}

func (c *Client) Put(path, contentType string, content []byte) error {
	return c.do(http.MethodPut, path, contentType, bytes.NewReader(content), nil)
}

func (c *Client) do(method, path, contentType string, body io.Reader, result any) error {
	request, err := http.NewRequest(method, "http://localhost"+path, body)
	if err != nil {
		return err
	}
	if c.account != "" {
		request.SetBasicAuth(c.account, "")
	}
	if contentType != "" {
		request.Header.Set("Content-Type", contentType)
	}
	response, err := c.http.Do(request)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	content, err := io.ReadAll(response.Body)
	if err != nil {
		return err
	}
	if response.StatusCode >= 300 {
		return &HttpError{Method: method, Path: path, Status: response.StatusCode, Body: string(content)}
	}
	if result == nil {
		return nil
	}
	return json.Unmarshal(content, result)
}
