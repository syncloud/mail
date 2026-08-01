package main

import (
	"bufio"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"log"
	"math/big"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

type Message struct {
	Login      string   `json:"login"`
	Password   string   `json:"password"`
	From       string   `json:"from"`
	Recipients []string `json:"recipients"`
	Body       string   `json:"body"`
}

type Store struct {
	mutex    sync.Mutex
	messages []Message
}

func NewStore() *Store {
	return &Store{messages: []Message{}}
}

func (s *Store) Add(message Message) {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	s.messages = append(s.messages, message)
	log.Printf("stored message from %s login %s to %v", message.From, message.Login, message.Recipients)
}

func (s *Store) Messages() []Message {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	messages := make([]Message, len(s.messages))
	copy(messages, s.messages)
	return messages
}

func (s *Store) Reset() {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	s.messages = []Message{}
	log.Print("store reset")
}

const UpdateToken = "faker-update-token"

type AcquireRequest struct {
	Domain string `json:"domain"`
}

type Api struct {
	store *Store
}

func (a *Api) write(writer http.ResponseWriter, body interface{}) {
	writer.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(writer).Encode(body); err != nil {
		log.Printf("encode error: %v", err)
	}
}

func (a *Api) acquire(writer http.ResponseWriter, request *http.Request) {
	acquire := AcquireRequest{}
	if err := json.NewDecoder(request.Body).Decode(&acquire); err != nil {
		writer.WriteHeader(http.StatusBadRequest)
		return
	}
	log.Printf("acquire domain %s", acquire.Domain)
	a.write(writer, map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"name":         acquire.Domain,
			"update_token": UpdateToken,
		},
	})
}

func (a *Api) ServeHTTP(writer http.ResponseWriter, request *http.Request) {
	switch {
	case request.URL.Path == "/faker/messages" && request.Method == http.MethodGet:
		a.write(writer, a.store.Messages())
	case request.URL.Path == "/faker/reset":
		a.store.Reset()
		writer.WriteHeader(http.StatusOK)
	case request.URL.Path == "/user":
		a.write(writer, map[string]interface{}{
			"data": map[string]interface{}{"update_token": UpdateToken},
		})
	case request.URL.Path == "/domain/acquire_v2":
		a.acquire(writer, request)
	case request.URL.Path == "/domain/update":
		a.write(writer, map[string]interface{}{"success": true, "data": map[string]interface{}{}})
	default:
		log.Printf("not found: %s %s", request.Method, request.URL.Path)
		writer.WriteHeader(http.StatusNotFound)
	}
}

type Session struct {
	store    *Store
	reader   *bufio.Reader
	writer   *bufio.Writer
	login    string
	password string
	from     string
	to       []string
}

func NewSession(connection net.Conn, store *Store) *Session {
	return &Session{
		store:  store,
		reader: bufio.NewReader(connection),
		writer: bufio.NewWriter(connection),
	}
}

func (s *Session) send(format string, args ...interface{}) error {
	if _, err := fmt.Fprintf(s.writer, format+"\r\n", args...); err != nil {
		return err
	}
	return s.writer.Flush()
}

func (s *Session) auth(argument string) error {
	fields := strings.Fields(argument)
	if len(fields) < 2 || !strings.EqualFold(fields[0], "PLAIN") {
		return s.send("504 unsupported mechanism")
	}
	decoded, err := base64.StdEncoding.DecodeString(fields[1])
	if err != nil {
		return s.send("535 5.7.8 bad credentials encoding")
	}
	parts := strings.Split(string(decoded), "\x00")
	if len(parts) != 3 {
		return s.send("535 5.7.8 bad credentials")
	}
	s.login = parts[1]
	s.password = parts[2]
	log.Printf("auth login %s", s.login)
	return s.send("235 2.7.0 authenticated")
}

func (s *Session) data() error {
	if err := s.send("354 end with ."); err != nil {
		return err
	}
	body := strings.Builder{}
	for {
		line, err := s.reader.ReadString('\n')
		if err != nil {
			return err
		}
		if strings.TrimRight(line, "\r\n") == "." {
			break
		}
		body.WriteString(line)
	}
	s.store.Add(Message{
		Login:      s.login,
		Password:   s.password,
		From:       s.from,
		Recipients: s.to,
		Body:       body.String(),
	})
	s.from = ""
	s.to = nil
	return s.send("250 2.0.0 queued")
}

func address(argument string) string {
	start := strings.Index(argument, "<")
	end := strings.LastIndex(argument, ">")
	if start >= 0 && end > start {
		return argument[start+1 : end]
	}
	fields := strings.SplitN(argument, ":", 2)
	if len(fields) == 2 {
		return strings.TrimSpace(fields[1])
	}
	return strings.TrimSpace(argument)
}

func (s *Session) Run() error {
	if err := s.send("220 mail-relay-faker ESMTP"); err != nil {
		return err
	}
	for {
		line, err := s.reader.ReadString('\n')
		if err != nil {
			return err
		}
		line = strings.TrimRight(line, "\r\n")
		command := strings.ToUpper(strings.SplitN(line, " ", 2)[0])
		argument := ""
		if fields := strings.SplitN(line, " ", 2); len(fields) == 2 {
			argument = fields[1]
		}
		switch command {
		case "EHLO", "HELO":
			err = s.send("250-mail-relay-faker\r\n250-AUTH PLAIN\r\n250 OK")
		case "AUTH":
			err = s.auth(argument)
		case "MAIL":
			s.from = address(argument)
			err = s.send("250 2.1.0 ok")
		case "RCPT":
			s.to = append(s.to, address(argument))
			err = s.send("250 2.1.5 ok")
		case "DATA":
			err = s.data()
		case "RSET":
			s.from = ""
			s.to = nil
			err = s.send("250 2.0.0 ok")
		case "NOOP":
			err = s.send("250 2.0.0 ok")
		case "QUIT":
			_ = s.send("221 2.0.0 bye")
			return nil
		default:
			err = s.send("502 5.5.2 not implemented")
		}
		if err != nil {
			return err
		}
	}
}

func certificate() (tls.Certificate, error) {
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, err
	}
	template := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: "mail-relay-faker"},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().AddDate(1, 0, 0),
		KeyUsage:     x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, &template, &template, &key.PublicKey, key)
	if err != nil {
		return tls.Certificate{}, err
	}
	certPem := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	keyPem := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(key)})
	return tls.X509KeyPair(certPem, keyPem)
}

func env(name string, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

func main() {
	store := NewStore()

	apiAddress := env("FAKER_API_ADDR", ":8025")
	go func() {
		log.Printf("relay faker api listening on %s", apiAddress)
		if err := http.ListenAndServe(apiAddress, &Api{store: store}); err != nil {
			log.Fatalf("api: %v", err)
		}
	}()

	cert, err := certificate()
	if err != nil {
		log.Fatalf("certificate: %v", err)
	}
	smtpAddress := env("FAKER_SMTP_ADDR", ":465")
	listener, err := tls.Listen("tcp", smtpAddress, &tls.Config{Certificates: []tls.Certificate{cert}})
	if err != nil {
		log.Fatalf("listen: %v", err)
	}
	log.Printf("relay faker smtp listening on %s", smtpAddress)
	for {
		connection, err := listener.Accept()
		if err != nil {
			log.Printf("accept: %v", err)
			continue
		}
		go func() {
			defer connection.Close()
			if err := NewSession(connection, store).Run(); err != nil {
				log.Printf("session: %v", err)
			}
		}()
	}
}
