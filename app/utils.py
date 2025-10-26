from rest_framework.response import Response


def get_response_schema(schema, message, status_code):
    """Utility: Standard response structure"""

    return Response(
        {
            "message": message,
            "status": status_code,
            "results": schema,
        },
        status=status_code,
    )


def get_global_success_messages():
    """Utility: Get global success messages"""

    data = {
        "NO_CONTENT": "No content",

        "CREDENTIALS_MATCHED": "Login successful.",
        "LOGOUT_SUCCESSFUL": "Logout successful.",

        "RECORD_CREATED": "Record created successfully.",
        "RECORD_RETRIEVED": "Record retrieved successfully.",
        "RECORD_UPDATED": "Record updated successfully.",
        "RECORD_DELETED": "Record deleted successfully.",

        "OPERATION_SUCCESSFUL": "Operation successful.",
    }

    return data


def get_global_error_messages():
    """Utility: Get global error messages"""

    data = {
        "SOMETHING_WENT_WRONG": "Something went wrong, please try again.",

        "BAD_REQUEST": "Bad request, please try again.",

        "RECORD_NOT_FOUND": "Record not found.",

        "FORBIDDEN": "You do not have permission to perform this action.",

        "USER_ALREADY_EXISTS": "User already exists.",
        "USER_NOT_FOUND": "User not found.",

        "NOT_AUTHORIZED": "You are not authorized to perform this action.",

        "CREDENTIALS_MISMATCHED": "Invalid credentials provided.",
        "CREDENTIALS_NOT_PROVIDED": "Credentials not provided.",

    }

    return data
