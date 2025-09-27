"""
Utility functions for standardized error handling in database and utility operations.
"""

def check_error(result_or_callable, message_holder=None, fallback=None):
    """
    Evaluates a callable or result and handles standard (msg, 'error') patterns.

    Args:
        result_or_callable: A callable or pre-evaluated result.
        message_holder (dict, optional): A dictionary that holds "message" and "message_type".
        fallback (Any, optional): A fallback value to return if an error is detected.

    Returns:
        The original result if successful, or fallback if error is detected.
    """
    try:
        result = (result_or_callable() if callable(
            result_or_callable) else result_or_callable)

        if isinstance(result, tuple) and len(result) == 2:
            msg, msg_type = result
            if msg_type in ("error", "warning"):
                if message_holder is not None:
                    message_holder["message"] = msg
                    message_holder["message_type"] = msg_type
                return fallback
        return result
    except Exception as e: # pylint: disable=broad-exception-caught
        if message_holder is not None:
            message_holder["message"] = f"Unexpected Error: {e}"
            message_holder["message_type"] = "error"
        return fallback
