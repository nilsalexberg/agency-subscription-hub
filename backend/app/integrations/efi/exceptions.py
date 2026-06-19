from __future__ import annotations


class EfiAPIError(Exception):
    """Raised when the Efí API returns a non-2xx response.

    `property` is the JSON-path Efí reports for validation failures (e.g.
    "/payment/credit_card/billing_address/zipcode") — use it to map the
    error back to a specific form field.
    """

    def __init__(
        self,
        status_code: int,
        error_description: str,
        property: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_description = error_description
        self.property = property
        super().__init__(f"Efí API error {status_code}: {error_description}")
