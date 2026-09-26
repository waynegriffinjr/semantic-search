> Nested Resources (Sub-Resources)
Resources can have relationships. An author has books. An order has items. A user has posts. You express these relationships by nesting URIs:

/authors/7/books        ← all books by author 7
/orders/100/items       ← all items in order 100
/users/3/posts          ← all posts by user 3
/users/3/posts/12       ← post 12 by user 3

The hierarchy reads left to right like a sentence: "author 7's books" or "user 3's post 12." This makes APIs self-documenting, the URI tells you the relationship.

Rule of thumb: don't nest deeper than two levels. /users/3/posts/12/comments/5/reactions is technically valid but hard to work with. If you're nesting that deep, the inner resource probably deserves its own top-level endpoint: /comments/5/reactions.