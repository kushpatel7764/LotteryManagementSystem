"""
Utility functions for standardized error handling in database and utility operations.
"""

from flask import flash


def check_error(
    result_or_callable, message_holder=None, fallback=None, flash_prefix=None
):
    """
    Evaluate a callable or result and handle standard message/status tuple patterns.

    If ``message_holder`` is provided, the message and status are stored in it.
    If ``flash_prefix`` is provided, the message is displayed via Flask's flash.

    Args:
        result_or_callable: A callable or pre-evaluated result. When callable,
            it is invoked before inspection.
        message_holder (dict, optional): A dict with ``"message"`` and
            ``"message_type"`` keys. Populated when a status tuple is detected.
        fallback (Any, optional): Value returned when an error is detected.
        flash_prefix (str, optional): Prefix used to namespace the flash category,
            e.g. ``"tickets"`` produces ``"tickets_error"``.

    Returns:
        The original result on success, or ``fallback`` when an error is detected.
    """
    try:
        result = (
            result_or_callable() if callable(result_or_callable) else result_or_callable
        )

        if isinstance(result, tuple) and len(result) == 2:
            msg, msg_type = result
            if msg_type in ("error", "warning", "success"):
                if message_holder is not None:
                    existing = message_holder["message_type"]
                    # Priority rules: error > warning > success; never downgrade
                    should_skip = (
                        (msg_type == "success" and existing in ("error", "warning"))
                        or (msg_type == "warning" and existing == "error")
                        or (msg_type == "error" and existing == "error")
                    )
                    if not should_skip:
                        message_holder["message"] = msg
                        message_holder["message_type"] = msg_type

                if flash_prefix:
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
