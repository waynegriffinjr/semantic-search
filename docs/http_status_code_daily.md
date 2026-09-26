> The Status Codes You'll Use Every Day
You don't need to memorize all 60+ status codes. Here are the ones that matter most:

2xx - Success
200 OK - The request succeeded. This is the most common status code. GET returned data, PUT/PATCH updated something, DELETE removed something.

201 Created - The request succeeded and a new resource was created. You'll see this after a successful POST. The response usually includes the created resource with its new ID.

204 No Content - The request succeeded, but there's nothing to send back. Common after a DELETE, "yes, I deleted it, and there's nothing more to say."

3xx - Redirection
301 Moved Permanently - The resource has a new permanent URL. The client should use the new URL from now on.

304 Not Modified - The resource hasn't changed since the client last requested it. Used with caching to avoid re-downloading unchanged data.

4xx - Client Errors
400 Bad Request - The server can't understand your request. Usually means you sent malformed data — missing required fields, wrong data types, invalid JSON.

401 Unauthorized - You need to authenticate (prove who you are). This usually means you forgot to include an authentication token, or the token is invalid.

403 Forbidden - You've authenticated, but you don't have permission to access this resource. "I know who you are, but you're not allowed to do that."

The difference between 401 and 403 is subtle but important: 401 means "who are you?" and 403 means "I know who you are, and the answer is no."

404 Not Found - The resource doesn't exist. Either the URI is wrong or the resource has been deleted. This is probably the most famous status code, you've seen it in your browser.

405 Method Not Allowed - The resource exists, but it doesn't support the method you used. For example, trying to DELETE a resource that only allows GET.

422 Unprocessable Entity - The request format is correct, but the data doesn't pass validation. For example, sending an email field with "not-an-email." You'll see this a lot when working with FastAPI and Pydantic validation in Module 5.

429 Too Many Requests - You've hit a rate limit. The server is saying "slow down." Common with APIs that restrict how many calls you can make per minute/hour.

5xx - Server Errors
500 Internal Server Error - Something went wrong on the server. This is the generic "something broke" error. As a client, you can't fix this — the server needs to be fixed.

502 Bad Gateway - The server was acting as a proxy and received a bad response from the upstream server.

503 Service Unavailable - The server is temporarily down, usually for maintenance or because it's overloaded.

