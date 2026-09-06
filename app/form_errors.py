from pydantic import ValidationError


def field_errors(exc: ValidationError) -> dict[str, str]:
    """Map a Pydantic ValidationError to a flat {field_name: message} dict for form re-rendering."""
    return {str(err["loc"][0]): err["msg"] for err in exc.errors()}
