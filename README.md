matildas
========

This Python program aims to document gender of characters in currently popular children's books.

1. The New York Times bestselling picture books list is pulled (available dating back to June 2008).
2. More elaborate descriptions of each book are accessed through Google Books.
3. Sentences containing author names are removed from the book descriptions, to keep the focus on character genders.
4. The descriptions are scored for gender-relevant words, such as gendered pronouns and proper names (sent to a gendered database of names).
5. Author names are categorized using the genderized database of names.
6. Data is analyzed, including normalization for number of gendered terms (words + names) for length of description.
