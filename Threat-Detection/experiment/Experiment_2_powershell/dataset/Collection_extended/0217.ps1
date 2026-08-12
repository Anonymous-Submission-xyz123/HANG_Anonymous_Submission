# Natural language intent:
# Uses ADSI to search for computer objects in Active Directory.

([adsisearcher]"objectcategory=computer").FindAll(); ([adsisearcher]"objectcategory=computer").FindOne()
