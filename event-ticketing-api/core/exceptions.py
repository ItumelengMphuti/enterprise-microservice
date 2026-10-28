from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = response.data
    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
        details = {}
    elif response.status_code == 400:
        message = "Request validation failed."
    else:
        message = "Request failed."

    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "error"),
            "message": message,
            "details": details,
        }
    }
    return response
