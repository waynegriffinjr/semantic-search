> The Response Body Tells the Rest of the Story
Status codes give you the category of the result, but the response body often includes more detail. A well-designed API returns helpful error messages:

{
  "status": 422,
  "detail": "Validation error",
  "errors": [
    {
      "field": "email",
      "message": "Not a valid email address"
    }
  ]
}

When you build your own APIs in Module 5, you'll design these error responses. Good error messages make debugging dramatically easier for anyone using your API.