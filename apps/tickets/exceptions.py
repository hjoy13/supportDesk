from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    # Already in {"detail": ...} shape (403/404/401/etc.) — leave as-is.
    if isinstance(response.data, dict) and "detail" in response.data:
        return response

    # Otherwise this is DRF's field-keyed validation error shape:
    # {"field": ["msg", ...], ...} — reshape it into the unified envelope.
    if isinstance(response.data, dict):
        response.data = {
            "detail": "Validation failed.",
            "errors": response.data,
        }

    return response