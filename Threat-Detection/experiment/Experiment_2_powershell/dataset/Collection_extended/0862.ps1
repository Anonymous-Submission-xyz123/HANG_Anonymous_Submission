# Natural language intent:
# Locate web server configuration files, With this command, we can easily find configuration files belonging to Microsoft IIS, XAMPP, Apache, PHP or MySQL installation:

gci c:\ -Include web.config,applicationHost.config,php.ini,httpd.conf,httpd-xampp.conf,my.ini,my.cnf -File -Recurse -EA SilentlyContinue
