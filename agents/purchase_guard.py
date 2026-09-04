"""
RazorGuard AI - Purchase Guard

Independent safety and risk layer for purchase authorization.

The Purchase Guard sits between the Checkout Agent
and the payment provider.

Flow:

    Checkout Agent
          ↓
    Purchase Guard
          ↓
    Deterministic Validation
          ↓
    Risk Assessment
          ↓
    ALLOW / BLOCK
          ↓
       Razorpay

IMPORTANT:

    The LLM/AI agent is never the final authority
    for money movement.

The guard independently validates the purchase before
a payment-provider order can be created.

Risk scoring is an additional security signal.

Risk scoring NEVER overrides a deterministic security
failure.
"""

from services.checkout_service import (
    verify_order_total,
)


# ============================================================
# PURCHASE GUARD
# ============================================================

class PurchaseGuard:
    """
    Independent authorization and risk-assessment layer.

    The guard performs deterministic checks and does not
    rely on an LLM decision to authorize payment.

    Risk scoring provides an additional security signal:

        0 - 29   LOW
        30 - 69  MEDIUM
        70 - 100 HIGH
    """

    def __init__(
        self,
        max_order_amount=None,
    ):
        """
        Parameters
        ----------
        max_order_amount:
            Optional maximum allowed order amount in INR.

            If None, no application-level maximum is applied.
        """

        self.max_order_amount = (
            float(max_order_amount)
            if max_order_amount is not None
            else None
        )

    # ========================================================
    # RISK ENGINE
    # ========================================================

    @staticmethod
    def _calculate_risk(
        checks,
        reasons=None,
        warnings=None,
        verification=None,
        amount=None,
    ):
        """
        Calculate a deterministic RazorGuard risk assessment.

        IMPORTANT:

            This function does NOT authorize payment.

            Deterministic validation remains the final
            authorization boundary.
        """

        reasons = (
            reasons
            if isinstance(
                reasons,
                list,
            )
            else []
        )

        warnings = (
            warnings
            if isinstance(
                warnings,
                list,
            )
            else []
        )

        verification = (
            verification
            if isinstance(
                verification,
                dict,
            )
            else {}
        )

        score = 0

        risk_factors = []

        # ----------------------------------------------------
        # 1. ORDER STRUCTURE
        # ----------------------------------------------------

        if checks.get(
            "order_valid"
        ) is False:

            score += 40

            risk_factors.append(
                "order structure is invalid"
            )

        # ----------------------------------------------------
        # 2. ITEMS
        # ----------------------------------------------------

        if checks.get(
            "items_present"
        ) is False:

            score += 30

            risk_factors.append(
                "order contains no valid items"
            )

        # ----------------------------------------------------
        # 3. TOTAL INTEGRITY
        # ----------------------------------------------------

        if checks.get(
            "total_valid"
        ) is False:

            score += 70

            risk_factors.append(
                "order total failed independent verification"
            )

        # ----------------------------------------------------
        # 4. USER CONFIRMATION
        # ----------------------------------------------------

        if checks.get(
            "confirmation_valid"
        ) is False:

            score += 70

            risk_factors.append(
                "explicit user confirmation is missing"
            )

        # ----------------------------------------------------
        # 5. CURRENCY
        # ----------------------------------------------------

        if checks.get(
            "currency_valid"
        ) is False:

            score += 50

            risk_factors.append(
                "checkout currency is not supported"
            )

        # ----------------------------------------------------
        # 6. AMOUNT LIMIT
        # ----------------------------------------------------

        if checks.get(
            "amount_limit_valid"
        ) is False:

            score += 60

            risk_factors.append(
                "order exceeds the configured purchase limit"
            )

        # ----------------------------------------------------
        # 7. PAYMENT PROVIDER
        # ----------------------------------------------------

        if checks.get(
            "payment_provider_valid"
        ) is False:

            score += 60

            risk_factors.append(
                "payment provider is not authorized"
            )

        # ----------------------------------------------------
        # 8. VERIFICATION DIFFERENCE
        # ----------------------------------------------------

        difference = verification.get(
            "difference"
        )

        if difference is not None:

            try:

                difference = abs(
                    float(
                        difference
                    )
                )

                if difference > 0.01:

                    if not any(
                        "total" in factor.lower()
                        for factor in risk_factors
                    ):

                        score += 50

                        risk_factors.append(
                            (
                                "declared order total differs "
                                "from independently calculated total"
                            )
                        )

            except (
                TypeError,
                ValueError,
            ):

                score += 20

                risk_factors.append(
                    "order total difference could not be interpreted safely"
                )

        # ----------------------------------------------------
        # 9. HIGH ORDER VALUE
        # ----------------------------------------------------

        if amount is not None:

            try:

                numeric_amount = float(
                    amount
                )

                # Risk signal only.
                # This does NOT automatically block payment.

                if numeric_amount >= 50000:

                    score += 15

                    risk_factors.append(
                        "high-value transaction"
                    )

                elif numeric_amount >= 25000:

                    score += 5

                    risk_factors.append(
                        "elevated-value transaction"
                    )

            except (
                TypeError,
                ValueError,
            ):

                score += 20

                risk_factors.append(
                    "transaction amount could not be interpreted safely"
                )

        # ----------------------------------------------------
        # 10. WARNINGS
        # ----------------------------------------------------

        if warnings:

            score += min(
                5,
                len(warnings),
            )

            risk_factors.append(
                "validation produced one or more warnings"
            )

        # ----------------------------------------------------
        # SUCCESS BASELINE
        # ----------------------------------------------------

        if (
            not risk_factors
            and all(
                value is True
                for value in checks.values()
            )
        ):

            score = 5

        # ----------------------------------------------------
        # CLAMP
        # ----------------------------------------------------

        score = max(
            0,
            min(
                int(score),
                100,
            ),
        )

        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if score < 30:

            risk_level = "low"

        elif score < 70:

            risk_level = "medium"

        else:

            risk_level = "high"

        return {
            "risk_score": score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }

    # ========================================================
    # RESULT BUILDER
    # ========================================================

    @classmethod
    def _build_result(
        cls,
        allowed,
        decision,
        reasons,
        warnings,
        checks,
        verification=None,
        amount=None,
        currency=None,
    ):
        """
        Build a consistent Purchase Guard response.
        """

        risk = cls._calculate_risk(
            checks=checks,
            reasons=reasons,
            warnings=warnings,
            verification=verification,
            amount=amount,
        )

        result = {
            "allowed": bool(
                allowed
            ),

            "decision": str(
                decision
            ),

            "reasons": list(
                reasons
            ),

            "warnings": list(
                warnings
            ),

            "checks": dict(
                checks
            ),

            "risk_score": risk[
                "risk_score"
            ],

            "risk_level": risk[
                "risk_level"
            ],

            "risk_factors": risk[
                "risk_factors"
            ],
        }

        if verification is not None:

            result[
                "verification"
            ] = verification

        if amount is not None:

            result[
                "amount"
            ] = amount

        if currency is not None:

            result[
                "currency"
            ] = currency

        return result

    # ========================================================
    # PUBLIC VALIDATION
    # ========================================================

    def evaluate(
        self,
        order,
    ):
        """
        Evaluate whether an order is safe to proceed.

        IMPORTANT:

            ALL deterministic checks are evaluated before
            the final ALLOW/BLOCK decision.

        The risk engine never overrides a deterministic
        security failure.
        """

        reasons = []

        warnings = []

        checks = {
            "order_valid": False,
            "items_present": False,
            "total_valid": False,
            "confirmation_valid": False,
            "amount_limit_valid": True,
            "currency_valid": False,
            "payment_provider_valid": False,
        }

        verification = None
        total = None
        currency = None

        # ====================================================
        # 1. ORDER OBJECT
        # ====================================================

        if not isinstance(
            order,
            dict,
        ):

            return self._build_result(
                allowed=False,
                decision="blocked",
                reasons=[
                    "order must be an object"
                ],
                warnings=[],
                checks=checks,
            )

        checks[
            "order_valid"
        ] = True

        reasons.append(
            "order structure is valid"
        )

        # ====================================================
        # 2. ITEMS
        # ====================================================

        items = order.get(
            "items",
            [],
        )

        if not isinstance(
            items,
            list,
        ):

            checks[
                "items_present"
            ] = False

            reasons.append(
                "order items must be a list"
            )

            return self._build_result(
                allowed=False,
                decision="blocked",
                reasons=reasons,
                warnings=warnings,
                checks=checks,
            )

        if not items:

            reasons.append(
                "order contains no items"
            )

            return self._build_result(
                allowed=False,
                decision="blocked",
                reasons=reasons,
                warnings=warnings,
                checks=checks,
            )

        checks[
            "items_present"
        ] = True

        reasons.append(
            "order contains products"
        )

        # ====================================================
        # 3. VALIDATE INDIVIDUAL ITEMS
        # ====================================================

        item_validation_failed = False

        for index, item in enumerate(
            items
        ):

            if not isinstance(
                item,
                dict,
            ):

                item_validation_failed = True

                reasons.append(
                    f"item {index + 1} is invalid"
                )

                continue

            product_id = item.get(
                "product_id"
            )

            if not product_id:

                item_validation_failed = True

                reasons.append(
                    (
                        f"item {index + 1} "
                        "has no product ID"
                    )
                )

                continue

            quantity = item.get(
                "quantity",
                1,
            )

            try:

                quantity = int(
                    quantity
                )

            except (
                TypeError,
                ValueError,
            ):

                item_validation_failed = True

                reasons.append(
                    (
                        f"invalid quantity "
                        f"for item {index + 1}"
                    )
                )

                continue

            if quantity <= 0:

                item_validation_failed = True

                reasons.append(
                    (
                        "quantity must be greater "
                        f"than zero for item {index + 1}"
                    )
                )

        if item_validation_failed:

            checks[
                "items_present"
            ] = False

            return self._build_result(
                allowed=False,
                decision="blocked",
                reasons=reasons,
                warnings=warnings,
                checks=checks,
            )

        # ====================================================
        # 4. VERIFY TOTAL
        # ====================================================

        try:

            verification = verify_order_total(
                order
            )

        except Exception as exc:

            reasons.append(
                "order total could not be verified"
            )

            warnings.append(
                str(exc)
            )

            return self._build_result(
                allowed=False,
                decision="blocked",
                reasons=reasons,
                warnings=warnings,
                checks=checks,
            )

        if not verification.get(
            "valid",
            False,
        ):

            checks[
                "total_valid"
            ] = False

            reasons.append(
                "order total verification failed"
            )

        else:

            checks[
                "total_valid"
            ] = True

            reasons.append(
                "order total is mathematically verified"
            )

        # ====================================================
        # 5. EXPLICIT USER CONFIRMATION
        # ====================================================

        user_confirmed = order.get(
            "user_confirmed",
            False,
        )

        if user_confirmed is True:

            checks[
                "confirmation_valid"
            ] = True

            reasons.append(
                "explicit user confirmation received"
            )

        else:

            checks[
                "confirmation_valid"
            ] = False

            reasons.append(
                "explicit user confirmation is required"
            )

        # ====================================================
        # 6. CURRENCY
        # ====================================================

        currency = str(
            order.get(
                "currency",
                "",
            )
            or ""
        ).upper().strip()

        if currency == "INR":

            checks[
                "currency_valid"
            ] = True

            reasons.append(
                "checkout currency is INR"
            )

        else:

            checks[
                "currency_valid"
            ] = False

            warnings.append(
                (
                    "received currency: "
                    f"{currency or 'missing'}"
                )
            )

            reasons.append(
                "unsupported checkout currency"
            )

        # ====================================================
        # 7. ORDER AMOUNT
        # ====================================================

        try:

            total = float(
                order.get(
                    "total",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            checks[
                "amount_limit_valid"
            ] = False

            reasons.append(
                "order total is not a valid number"
            )

            warnings.append(
                "transaction amount could not be interpreted safely"
            )

        else:

            if total < 0:

                checks[
                    "amount_limit_valid"
                ] = False

                reasons.append(
                    "order total cannot be negative"
                )

            elif (
                self.max_order_amount is not None
                and total > self.max_order_amount
            ):

                checks[
                    "amount_limit_valid"
                ] = False

                reasons.append(
                    "order exceeds configured purchase limit"
                )

                warnings.append(
                    (
                        f"order total ₹{total:.2f} "
                        f"exceeds limit "
                        f"₹{self.max_order_amount:.2f}"
                    )
                )

            else:

                checks[
                    "amount_limit_valid"
                ] = True

                reasons.append(
                    "order is within configured amount limit"
                    if self.max_order_amount is not None
                    else "no application amount limit configured"
                )

        # ====================================================
        # 8. PAYMENT PROVIDER
        # ====================================================

        provider = str(
            order.get(
                "payment_provider",
                "",
            )
            or ""
        ).lower().strip()

        if provider == "razorpay":

            checks[
                "payment_provider_valid"
            ] = True

            reasons.append(
                "payment provider is Razorpay"
            )

        else:

            checks[
                "payment_provider_valid"
            ] = False

            warnings.append(
                (
                    "expected razorpay, "
                    f"received {provider or 'missing'}"
                )
            )

            reasons.append(
                "unsupported payment provider"
            )

        # ====================================================
        # 9. FINAL DETERMINISTIC DECISION
        # ====================================================

        all_checks_valid = all(
            value is True
            for value in checks.values()
        )

        if not all_checks_valid:

            result = self._build_result(
                allowed=False,
                decision="blocked",
                reasons=reasons,
                warnings=warnings,
                checks=checks,
                verification=verification,
                amount=total,
                currency=currency,
            )

            return result

        # ====================================================
        # 10. FINAL ALLOW
        # ====================================================

        result = self._build_result(
            allowed=True,
            decision="allowed",
            reasons=reasons,
            warnings=warnings,
            checks=checks,
            verification=verification,
            amount=total,
            currency=currency,
        )

        return result

    # ========================================================
    # ASSERT / BLOCKING API
    # ========================================================

    def authorize(
        self,
        order,
    ):
        """
        Authorize a purchase.

        Returns the evaluation when allowed.

        Raises ValueError when blocked.

        Risk information is preserved in the evaluation result.
        """

        result = self.evaluate(
            order
        )

        if not result.get(
            "allowed",
            False,
        ):

            reason_text = "; ".join(
                result.get(
                    "reasons",
                    [],
                )
            )

            raise ValueError(
                f"Purchase blocked: {reason_text}"
            )

        return result


# ============================================================
# DEFAULT GUARD
# ============================================================

purchase_guard = PurchaseGuard()


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def evaluate_purchase(
    order,
):
    """
    Evaluate a purchase using the default guard.
    """

    return purchase_guard.evaluate(
        order
    )


def authorize_purchase(
    order,
):
    """
    Authorize a purchase using the default guard.
    """

    return purchase_guard.authorize(
        order
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PurchaseGuard",
    "purchase_guard",
    "evaluate_purchase",
    "authorize_purchase",
]