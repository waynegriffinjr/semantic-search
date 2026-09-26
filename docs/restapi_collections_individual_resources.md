> Collections and Individual Resources
Resources come in two forms:

Collections - a group of resources of the same type:

/books          ← all books
/users          ← all users

Individual resources - one specific item, identified by an ID:

/books/15       ← book with ID 15
/users/42       ← user with ID 42

Convention: collection names are plural. Use /books, not /book. This reads naturally: "give me all books" (GET /books) or "give me book 15" (GET /books/15).

