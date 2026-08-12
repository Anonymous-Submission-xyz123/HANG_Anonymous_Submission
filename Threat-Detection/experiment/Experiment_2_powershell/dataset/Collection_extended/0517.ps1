# Natural language intent:
# Retrieve and display ACL information for registry services.

get-acl REGISTRY::HKLM\SYSTEM\CurrentControlSet\Services* |FL ; get-acl REGISTRY::HKLM\SYSTEM\CurrentControlSet\Services${weak_service_name} |FL
