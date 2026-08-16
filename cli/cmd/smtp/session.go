package main

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"strings"
	"time"
)

const timeout = 20 * time.Second

type Session struct {
	connection net.Conn
	reader     *bufio.Reader
	transcript strings.Builder
}

func Dial(socket string) (*Session, error) {
	connection, err := net.DialTimeout("unix", socket, timeout)
	if err != nil {
		return nil, err
	}
	if err := connection.SetDeadline(time.Now().Add(timeout)); err != nil {
		return nil, err
	}
	session := &Session{connection: connection, reader: bufio.NewReader(connection)}
	if err := session.reply(); err != nil {
		return nil, err
	}
	return session, nil
}

func (s *Session) Close() {
	_ = s.connection.Close()
}

func (s *Session) Transcript() string {
	return s.transcript.String()
}

func (s *Session) Send(line string) error {
	if err := s.write(line); err != nil {
		return err
	}
	return s.reply()
}

func (s *Session) Write(line string) error {
	return s.write(line)
}

func (s *Session) write(line string) error {
	s.transcript.WriteString("> " + line + "\n")
	_, err := io.WriteString(s.connection, line+"\r\n")
	return err
}

func (s *Session) reply() error {
	for {
		line, err := s.reader.ReadString('\n')
		if err != nil {
			return err
		}
		line = strings.TrimRight(line, "\r\n")
		s.transcript.WriteString("< " + line + "\n")
		if len(line) < 4 || line[3] != '-' {
			return nil
		}
	}
}

func (s *Session) Xclient(attributes string) error {
	if err := s.Send("EHLO smtp.test"); err != nil {
		return err
	}
	return s.Send(fmt.Sprintf("XCLIENT %s", attributes))
}

func (s *Session) Deliver(from string, recipient string, subject string, body string, headers []string) error {
	if err := s.Send("EHLO smtp.test"); err != nil {
		return err
	}
	if err := s.Send(fmt.Sprintf("MAIL FROM:<%s>", from)); err != nil {
		return err
	}
	if err := s.Send(fmt.Sprintf("RCPT TO:<%s>", recipient)); err != nil {
		return err
	}
	if subject != "" {
		if err := s.Send("DATA"); err != nil {
			return err
		}
		if err := s.Write(fmt.Sprintf("Subject: %s", subject)); err != nil {
			return err
		}
		if err := s.Write(fmt.Sprintf("From: %s", from)); err != nil {
			return err
		}
		if err := s.Write(fmt.Sprintf("To: %s", recipient)); err != nil {
			return err
		}
		for _, header := range headers {
			if err := s.Write(header); err != nil {
				return err
			}
		}
		if err := s.Write(""); err != nil {
			return err
		}
		for _, line := range strings.Split(body, "\n") {
			if err := s.Write(line); err != nil {
				return err
			}
		}
		if err := s.Send("."); err != nil {
			return err
		}
	}
	return s.Send("QUIT")
}
