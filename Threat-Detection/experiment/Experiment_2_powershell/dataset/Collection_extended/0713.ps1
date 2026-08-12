# Natural language intent:
# Explanation A certificate authority itself has a set of permissions that secure various CA actions. These permissions can be access from `certsrv.msc`, right clicking a CA, selecting properties, and switching to the Security tab:   This can also be enumerated via PSPKI�s module with `Get-CertificationAuthority | Get-CertificationAuthorityAcl`:

Get-CertificationAuthority -ComputerName dc.theshire.local | Get-certificationAuthorityAcl | select -expand Access
