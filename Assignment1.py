from abc import ABC, abstractmethod
from typing import Dict, Type


class PaymentMethod(ABC):
    @abstractmethod
    def get_details(self) -> str:
        pass

    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass


class RazorpayCardPayment(PaymentMethod):
    def __init__(self, card_number: str, **kwargs):
        self.card_number = card_number

    def get_details(self) -> str:
        masked = f"**** **** **** {self.card_number[-4:]}" if len(self.card_number) >= 4 else self.card_number
        return f"Razorpay Card [{masked}]"

    def pay(self, amount: float) -> bool:
        print(f"[Razorpay Gateway] Authorizing Card payment of ${amount:.2f} ({self.get_details()})... SUCCESS")
        return True


class RazorpayUPIPayment(PaymentMethod):
    def __init__(self, upi_id: str, **kwargs):
        self.upi_id = upi_id

    def get_details(self) -> str:
        return f"Razorpay UPI [{self.upi_id}]"

    def pay(self, amount: float) -> bool:
        print(f"[Razorpay Gateway] Requesting UPI payment of ${amount:.2f} ({self.get_details()})... SUCCESS")
        return True


class StripeCardPayment(PaymentMethod):
    def __init__(self, card_number: str, **kwargs):
        self.card_number = card_number

    def get_details(self) -> str:
        masked = f"**** **** **** {self.card_number[-4:]}" if len(self.card_number) >= 4 else self.card_number
        return f"Stripe Card [{masked}]"

    def pay(self, amount: float) -> bool:
        print(f"[Stripe Gateway] Charging Card payment of ${amount:.2f} ({self.get_details()})... SUCCEEDED")
        return True


class StripeUPIPayment(PaymentMethod):
    def __init__(self, upi_id: str, **kwargs):
        self.upi_id = upi_id

    def get_details(self) -> str:
        return f"Stripe UPI [{self.upi_id}]"

    def pay(self, amount: float) -> bool:
        print(f"[Stripe Gateway] Processing UPI transfer of ${amount:.2f} ({self.get_details()})... SUCCEEDED")
        return True


class FactoryPaymentMethod(ABC):
    factory: Dict[str, Type[PaymentMethod]] = {}

    @classmethod
    def get_payment_object(cls, method_type: str, **kwargs) -> PaymentMethod:
        method_key = method_type.strip().lower()
        if method_key not in cls.factory:
            raise ValueError(f"Unsupported payment method '{method_type}' for {cls.__name__}.")
        return cls.factory[method_key](**kwargs)

    @classmethod
    def register_payment_method(cls, method_type: str, payment_class: Type[PaymentMethod]) -> None:
        cls.factory[method_type.strip().lower()] = payment_class


class RazorpayFactory(FactoryPaymentMethod):
    factory = {"card": RazorpayCardPayment, "upi": RazorpayUPIPayment}


class StripeFactory(FactoryPaymentMethod):
    factory = {"card": StripeCardPayment, "upi": StripeUPIPayment}


class Aggregator(ABC):
    def __init__(self, name: str, processing_fee: float, payment_factory: Type[FactoryPaymentMethod]):
        self.name = name
        self.processing_fee = processing_fee
        self.payment_factory = payment_factory

    def call_get_payment_object(self, method_type: str, amount: float, **kwargs) -> bool:
        payment_obj = self.payment_factory.get_payment_object(method_type, **kwargs)
        fee_amount = amount * (self.processing_fee / 100.0)
        total_amount = amount + fee_amount

        print(f"\n[{self.name.upper()}] Base: ${amount:.2f} | Fee ({self.processing_fee}%): ${fee_amount:.2f} | Total: ${total_amount:.2f}")
        return payment_obj.pay(total_amount)


class RazorpayAggregator(Aggregator):
    def __init__(self, processing_fee: float = 2.0):
        super().__init__("Razorpay", processing_fee, RazorpayFactory)


class StripeAggregator(Aggregator):
    def __init__(self, processing_fee: float = 2.9):
        super().__init__("Stripe", processing_fee, StripeFactory)


class AggregatorFactory:
    factory: Dict[str, Type[Aggregator]] = {
        "stripe": StripeAggregator,
        "razorpay": RazorpayAggregator,
    }

    @classmethod
    def get_aggregator_object(cls, aggregator_name: str) -> Aggregator:
        key = aggregator_name.strip().lower()
        if key not in cls.factory:
            raise KeyError(f"Invalid aggregator choice '{aggregator_name}'. Available: {list(cls.factory.keys())}")
        return cls.factory[key]()

    @classmethod
    def register_aggregator(cls, name: str, aggregator_cls: Type[Aggregator]) -> None:
        cls.factory[name.strip().lower()] = aggregator_cls


def run_cli():
    try:
        agg_choice = input("Select Aggregator (stripe / razorpay): ").strip()
        aggregator = AggregatorFactory.get_aggregator_object(agg_choice)

        method_choice = input("Select Payment Method (card / upi): ").strip().lower()
        kwargs = {}

        if method_choice == "card":
            card_no = input("Enter Card Number: ").strip()
            if not card_no.isdigit() or len(card_no) < 12:
                raise ValueError("Invalid Card Number.")
            kwargs["card_number"] = card_no
        elif method_choice == "upi":
            upi_id = input("Enter UPI ID: ").strip()
            if "@" not in upi_id:
                raise ValueError("Invalid UPI ID.")
            kwargs["upi_id"] = upi_id
        else:
            raise ValueError("Invalid payment method selection.")

        amount = float(input("Enter Amount ($): ").strip())
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        success = aggregator.call_get_payment_object(method_choice, amount, **kwargs)
        print("\n[SUCCESS] Transaction completed." if success else "\n[FAILED] Transaction failed.")

    except Exception as e:
        print(f"\n[ERROR] {e}")


def extension_demo():
    class PayPalCardPayment(PaymentMethod):
        def __init__(self, card_number: str, **kwargs):
            self.card_number = card_number

        def get_details(self) -> str:
            return f"PayPal Card [****{self.card_number[-4:]}]"

        def pay(self, amount: float) -> bool:
            print(f"[PayPal Gateway] Payment of ${amount:.2f} APPROVED.")
            return True

    class PayPalFactory(FactoryPaymentMethod):
        factory = {"card": PayPalCardPayment}

    class PayPalAggregator(Aggregator):
        def __init__(self, processing_fee: float = 3.5):
            super().__init__("PayPal", processing_fee, PayPalFactory)

    AggregatorFactory.register_aggregator("paypal", PayPalAggregator)
    pp_agg = AggregatorFactory.get_aggregator_object("paypal")
    pp_agg.call_get_payment_object("card", 250.00, card_number="5500000012349999")


if __name__ == "__main__":
    stripe = AggregatorFactory.get_aggregator_object("stripe")
    stripe.call_get_payment_object("upi", 100.0, upi_id="user@stripe")
    extension_demo()
