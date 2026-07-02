package installer

import (
	"encoding/json"
	"fmt"
	"io"
	"net/url"

	"github.com/syncloud/golib/platform"
	"go.uber.org/zap"
)

type PlatformClient struct {
	client *platform.RealHttpClient
	logger *zap.Logger
}

func NewPlatformClient(logger *zap.Logger) *PlatformClient {
	return &PlatformClient{
		client: platform.NewHttpClient(),
		logger: logger,
	}
}

func (c *PlatformClient) GetDeviceDomainName() (string, error) {
	c.logger.Info("get device domain name")
	resp, err := c.client.Get("http://unix/app/device_domain_name")
	if err != nil {
		return "", err
	}
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("get device domain name, %s", resp.Status)
	}
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	var responseJson platform.Response
	if err := json.Unmarshal(bodyBytes, &responseJson); err != nil {
		return "", err
	}
	return responseJson.Data, nil
}

func (c *PlatformClient) SetDkimKey(key string) error {
	c.logger.Info("set dkim key")
	resp, err := c.client.Post("http://unix/config/set_dkim_key", url.Values{"dkim_key": {key}})
	if err != nil {
		return err
	}
	if resp.StatusCode != 200 {
		return fmt.Errorf("set dkim key, %s", resp.Status)
	}
	return nil
}
