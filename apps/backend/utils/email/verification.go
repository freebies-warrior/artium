package email

import "fmt"

func (s *Service) SendVerificationEmail(
	toEmail string,
	verificationLink string,
	expiryMinutes int,
) error {

	subject := "Verify your email address"

	body := fmt.Sprintf(`Hello,

Verify your email to activate your account.

Click the link below:
%s

This link expires in %d minutes.

If you did not sign up, you can ignore this email.

— %s
`, verificationLink, expiryMinutes, s.cfg.FromName)

	return s.sendMail(toEmail, subject, body)
}
