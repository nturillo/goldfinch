from libgen_api import LibgenSearch

s = LibgenSearch()
title_filters = {"Extension" : "epub"}
results = s.search_title_filtered("Lonesome Dove", title_filters, exact_match=True)
print(results)