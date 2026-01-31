package email

import (
	"fmt"
	"net/smtp"
)

type Config struct {
	Host     string
	Port     int
	Username string
	Password string
	FromName string
	FromAddr string
}

type Service struct {
	cfg Config
}

func New(cfg Config) *Service {
	return &Service{cfg: cfg}
}

func (s *Service) sendMail(to string, subject string, body string) error {
	msg := []byte(
		fmt.Sprintf("From: %s <%s>\r\n", s.cfg.FromName, s.cfg.FromAddr) +
			fmt.Sprintf("To: %s\r\n", to) +
			fmt.Sprintf("Subject: %s\r\n", subject) +
			"\r\n" +
			body,
	)

	addr := fmt.Sprintf("%s:%d", s.cfg.Host, s.cfg.Port)

	var auth smtp.Auth = nil
	if s.cfg.Username != "" && s.cfg.Password != "" {
		auth = smtp.PlainAuth(
			"",
			s.cfg.Username,
			s.cfg.Password,
			s.cfg.Host,
		)
	}

	return smtp.SendMail(
		addr,
		auth,
		s.cfg.FromAddr,
		[]string{to},
		msg,
	)
}
