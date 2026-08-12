# Natural language intent:
# Search for Active Directory groups using ADSI searcher.

([adsisearcher]"objectcategory=group").FindAll(); ([adsisearcher]"objectcategory=group").FindOne()
