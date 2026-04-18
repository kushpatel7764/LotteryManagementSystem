"""
Utility functions for standardized error handling in database and utility operations.
"""

from flask import flash


def check_error(
    result_or_callable, message_holder=None, fallback=None, flash_prefix=None
):
    """
    Evaluates a callable or result and handles standard
    (msg, 'error', 'success', 'warning') patterns.
    The message_holder is passed in then the message and message_type will be stored
    in it. Else if a flash_prefix is passed the message is displayed via flash().

    Args:
        result_or_callable: A callable or pre-evaluated result.
        message_holder (dict, optional): A dictionary that holds "message" and "message_type".
        fallback (Any, optional): A fallback value to return if an error is detected.

    Returns:
        The original result if successful, or fallback if error is detected.
    """
    try:
        result = (
            result_or_callable() if callable(result_or_callable) else result_or_callable
        )

        if isinstance(result, tuple) and len(result) == 2:
            msg, msg_type = result
            if msg_type in ("error", "warning", "success"):
                if message_holder is not None:
                    if not (
                        # Don't let success overwrite warning/error
                        (
                            msg_type == "success"
                            and message_holder["message_type"] in ["error", "warning"]
                        )
                        or
                        # Don't let warning overwrite error
                        (
                            msg_type == "warning"
                            and message_holder["message_type"] == "error"
                        )
                        or
                        # Don't let error overwrite existing error
                        (
                            msg_type == "error"
                            and message_holder["message_type"] == "error"
                        )
                    ):
                        message_holder["message"] = msg
                        message_holder["message_type"] = msg_type

                if flash_prefix:  # only flash if explicitly asked
                    flash(msg, f"{flash_prefix}_{msg_type}")
                return fallback
        return result
    except Exception as e:  # pylint: disable=broad-exception-caught
        if message_holder is not None:
            message_holder["message"] = f"Unexpected Error: {e}"
            message_holder["message_type"] = "error"

        if flash_prefix:
            flash(f"Unexpected Error: {e}", f"{flash_prefix}_error")
        return fallback
