package rest

import (
	"encoding/json"
	"net"
	"net/http"
	"os"

	"hooks/installer"

	"go.uber.org/zap"
)

type Server struct {
	installer *installer.Installer
	socket    string
	logger    *zap.Logger
}

type response struct {
	Success bool        `json:"success"`
	Message string      `json:"message,omitempty"`
	Data    interface{} `json:"data,omitempty"`
}

func NewServer(inst *installer.Installer, socket string, logger *zap.Logger) *Server {
	return &Server{installer: inst, socket: socket, logger: logger}
}

func (s *Server) Start() error {
	_ = os.Remove(s.socket)
	listener, err := net.Listen("unix", s.socket)
	if err != nil {
		return err
	}
	if err := os.Chmod(s.socket, 0666); err != nil {
		return err
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/api/relay", s.relay)
	s.logger.Info("webui started", zap.String("socket", s.socket))
	return http.Serve(listener, mux)
}

func (s *Server) relay(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		relay, err := s.installer.GetRelay()
		if err != nil {
			s.fail(w, err)
			return
		}
		relay.Password = ""
		s.ok(w, relay)
	case http.MethodPost:
		var relay installer.RelayConfig
		if err := json.NewDecoder(r.Body).Decode(&relay); err != nil {
			s.fail(w, err)
			return
		}
		if relay.Password == "" {
			current, err := s.installer.GetRelay()
			if err != nil {
				s.fail(w, err)
				return
			}
			relay.Password = current.Password
		}
		if err := s.installer.SetRelay(relay); err != nil {
			s.fail(w, err)
			return
		}
		if err := s.installer.ApplyRelay(); err != nil {
			s.fail(w, err)
			return
		}
		s.ok(w, "ok")
	default:
		w.WriteHeader(http.StatusMethodNotAllowed)
	}
}

func (s *Server) ok(w http.ResponseWriter, data interface{}) {
	s.write(w, http.StatusOK, response{Success: true, Data: data})
}

func (s *Server) fail(w http.ResponseWriter, err error) {
	s.logger.Error("request failed", zap.Error(err))
	s.write(w, http.StatusInternalServerError, response{Success: false, Message: err.Error()})
}

func (s *Server) write(w http.ResponseWriter, status int, body response) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
