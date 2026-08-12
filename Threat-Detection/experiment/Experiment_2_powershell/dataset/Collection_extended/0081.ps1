# Natural language intent:
# Send a malicious email with an attachment for test purposes.

Send-MailMessage -From ${sender} -To ${receiver} -Subject 'T1027_Atomic_Test' -Attachments ${input_file} -SmtpServer ${smtp_server}
