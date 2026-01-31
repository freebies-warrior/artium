package email

import (
	"bytes"
	"fmt"
	"mime/quotedprintable"
	"net/mail"
	"net/smtp"
	"strings"
	"time"
)

func (s *Service) sendMailMultipart(toEmail, subject, textBody, htmlBody string) error {
	// Envelope addresses must be plain (RFC 5321). Header can be pretty.
	fromHeader := mail.Address{Name: s.cfg.FromName, Address: s.cfg.FromAddr}
	toHeader := mail.Address{Address: toEmail}

	// Prevent header injection
	subject = strings.ReplaceAll(subject, "\n", "")
	subject = strings.ReplaceAll(subject, "\r", "")

	boundary := fmt.Sprintf("artium-%d", time.Now().UnixNano())

	var buf bytes.Buffer

	// Headers
	buf.WriteString(fmt.Sprintf("From: %s\r\n", fromHeader.String()))
	buf.WriteString(fmt.Sprintf("To: %s\r\n", toHeader.String()))
	buf.WriteString(fmt.Sprintf("Subject: %s\r\n", subject))
	buf.WriteString("MIME-Version: 1.0\r\n")
	buf.WriteString(fmt.Sprintf("Content-Type: multipart/alternative; boundary=%q\r\n", boundary))
	buf.WriteString("\r\n")

	// text/plain part
	buf.WriteString(fmt.Sprintf("--%s\r\n", boundary))
	buf.WriteString("Content-Type: text/plain; charset=UTF-8\r\n")
	buf.WriteString("Content-Transfer-Encoding: quoted-printable\r\n")
	buf.WriteString("\r\n")
	{
		qp := quotedprintable.NewWriter(&buf)
		_, _ = qp.Write([]byte(textBody))
		_ = qp.Close()
	}
	buf.WriteString("\r\n")

	// text/html part
	buf.WriteString(fmt.Sprintf("--%s\r\n", boundary))
	buf.WriteString("Content-Type: text/html; charset=UTF-8\r\n")
	buf.WriteString("Content-Transfer-Encoding: quoted-printable\r\n")
	buf.WriteString("\r\n")
	{
		qp := quotedprintable.NewWriter(&buf)
		_, _ = qp.Write([]byte(htmlBody))
		_ = qp.Close()
	}
	buf.WriteString("\r\n")

	// end boundary
	buf.WriteString(fmt.Sprintf("--%s--\r\n", boundary))

	// SMTP send
	addr := fmt.Sprintf("%s:%d", s.cfg.Host, s.cfg.Port)

	// Mailpit: do NOT AUTH. Only auth if username is set.
	var auth smtp.Auth
	if s.cfg.Username != "" {
		auth = smtp.PlainAuth("", s.cfg.Username, s.cfg.Password, s.cfg.Host)
	} else {
		auth = nil
	}

	// IMPORTANT: envelope-from must be plain email address
	return smtp.SendMail(addr, auth, s.cfg.FromAddr, []string{toEmail}, buf.Bytes())
}
