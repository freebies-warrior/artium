package email

import (
	"fmt"
	"time"
)

func (s *Service) SendVerificationEmail(
	toEmail string,
	verificationLink string,
	expiryMinutes int,
) error {
	subject := "Verify your email for Artium"

	// Plain-text fallback
	textBody := fmt.Sprintf(
		"Hi,\n\n"+
			"Welcome to Artium! Please verify your email address by opening this link:\n\n"+
			"%s\n\n"+
			"This link expires in %d minutes.\n\n"+
			"If you didn’t create an account, you can ignore this email.\n\n"+
			"— %s\n",
		verificationLink, expiryMinutes, s.cfg.FromName,
	)

	year := time.Now().Year()

	// HTML version
	htmlBody := fmt.Sprintf(`<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f6f7fb;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
    <table role="presentation" width="100%%" cellspacing="0" cellpadding="0" style="background:#f6f7fb;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,0.06);">
            <tr>
              <td style="padding:24px 28px;background:#111827;color:#ffffff;">
                <div style="font-size:18px;font-weight:700;">%s</div>
                <div style="margin-top:6px;font-size:13px;opacity:0.85;">Verify your email address</div>
              </td>
            </tr>

            <tr>
              <td style="padding:28px;color:#111827;">
                <p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:#374151;">
                  Thanks for signing up. Please verify your email address to finish setting up your account.
                </p>

                <table role="presentation" cellspacing="0" cellpadding="0" style="margin:20px 0 18px;">
                  <tr>
                    <td bgcolor="#2563eb" style="border-radius:10px;">
                      <a href="%s"
                         style="display:inline-block;padding:12px 18px;color:#ffffff;text-decoration:none;font-weight:700;font-size:14px;">
                        Verify email
                      </a>
                    </td>
                  </tr>
                </table>

                <p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#6b7280;">
                  This link expires in <strong>%d minutes</strong>.
                </p>

                <p style="margin:0 0 6px;font-size:13px;line-height:1.6;color:#6b7280;">
                  If the button doesn’t work, copy and paste this URL into your browser:
                </p>

                <p style="margin:0;font-size:12px;line-height:1.6;word-break:break-all;">
                  <a href="%s" style="color:#2563eb;text-decoration:none;">%s</a>
                </p>
              </td>
            </tr>

            <tr>
              <td style="padding:18px 28px;background:#f9fafb;color:#6b7280;font-size:12px;line-height:1.5;">
                <p style="margin:0;">
                  If you didn’t create an account, you can ignore this email.
                </p>
              </td>
            </tr>
          </table>

          <div style="max-width:600px;padding:10px 0 0;color:#9ca3af;font-size:11px;">
            © %d %s
          </div>
        </td>
      </tr>
    </table>
  </body>
</html>`,
		s.cfg.FromName,
		verificationLink,
		expiryMinutes,
		verificationLink,
		verificationLink,
		year,
		s.cfg.FromName,
	)

	// NEW: send multipart (text + html)
	return s.sendMailMultipart(toEmail, subject, textBody, htmlBody)
}
