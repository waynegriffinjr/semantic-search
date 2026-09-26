> What Good Design Looks Like: A Complete Example
Imagine you're designing an API for a study tracking application. Here's how you'd structure the resources:

# Users
GET    /users              ← list all users
POST   /users              ← create a new user
GET    /users/42           ← get user 42
PUT    /users/42           ← update user 42
DELETE /users/42           ← delete user 42

# User's study sessions
GET    /users/42/sessions           ← all sessions for user 42
POST   /users/42/sessions           ← create a session for user 42
GET    /users/42/sessions/7         ← specific session

# Courses (top-level resource)
GET    /courses                     ← all courses
GET    /courses?difficulty=beginner  ← filtered by difficulty
GET    /courses/5                   ← specific course
GET    /courses/5/lessons           ← lessons in course 5

Even without documentation, you can read these URIs and understand what they do. That's the goal of good REST design.