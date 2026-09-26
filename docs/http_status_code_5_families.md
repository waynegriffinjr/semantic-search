The Five Families
Status codes are grouped by their first digit. Each group tells a different story:

Range

Category

Meaning

1xx	
Informational

"I received your request and I'm working on it." (Rare — you'll almost never see these.)

2xx	
Success

"Everything worked. Here's what you asked for."

3xx	
Redirection

"What you want has moved. Go look over there instead."

4xx	
Client Error

"You made a mistake in your request."

5xx	
Server Error

"I made a mistake trying to handle your request."

The most important distinction: 4xx means you (the client) did something wrong. 5xx means the server did something wrong. When debugging, this tells you where to look.