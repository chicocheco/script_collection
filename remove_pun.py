import unicodedata

czech_text_sample = 'Samostatným státem se Česko stalo 1. ledna 1993, přičemž navazuje na tradice státnosti ' \
                    'Československa, Českého království, Českého knížectví a Velké Moravy, sahající do 9. století. ' \
                    'Podle české ústavy je parlamentní, demokratický právní stát s liberálním státním režimem.'

# split punctuation from characters like č becomes 'c' with '̌' (yes, that weird little thing on the right is háček
normalized_text = unicodedata.normalize('NFD', czech_text_sample)

# ex. with separated 'háček' unicodedata.combining('̌') returns 230, but with 'c' it returns 0
# read this as: return character if combining() is not 0 where 0 is like None so not None => True
text_without_pun = ''.join(char for char in normalized_text if not unicodedata.combining(char))

print(text_without_pun)
