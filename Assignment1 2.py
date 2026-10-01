from abc import ABC, abstractmethod


class PaymentMethod(ABC):
    @abstractmethod
    def get_details(self):
        pass

    @abstractmethod
    def pay(self, amount):
        pass


class RazorpayCardPayment(PaymentMethod):
    def __init__(self, card_number, **kwargs):
        self.card_number = str(card_number)

    def get_details(self):
        if len(self.card_number) >= 4:
            masked = "**** **** **** " + self.card_number[-4:]
        else:
            masked = self.card_number
        return f"Razorpay Card [{masked}]"

    def pay(self, amount):
        print(f"[Razorpay] Card ${amount:.2f} ({self.get_details()})... OK")
        return True


class RazorpayUPIPayment(PaymentMethod):
    def __init__(self, upi_id, **kwargs):
        self.upi_id = upi_id

    def get_details(self):
        return "Razorpay UPI [" + self.upi_id + "]"

    def pay(self, amount):
        print(f"[Razorpay] UPI ${amount:.2f} ({self.get_details()})... OK")
        return True


class StripeCardPayment(PaymentMethod):
    def __init__(self, card_number, **kwargs):
        self.card_number = str(card_number)

    def get_details(self):
        if len(self.card_number) >= 4:
            masked = "**** **** **** " + self.card_number[-4:]
        else:
            masked = self.card_number
        return f"Stripe Card [{masked}]"

    def pay(self, amount):
        print(f"[Stripe] Card ${amount:.2f} ({self.get_details()})... OK")
        return True


class StripeUPIPayment(PaymentMethod):
    def __init__(self, upi_id, **kwargs):
        self.upi_id = upi_id

    def get_details(self):
        return f"Stripe UPI [{self.upi_id}]"

    def pay(self, amount):
        print(f"[Stripe] UPI ${amount:.2f} ({self.get_details()})... OK")
        return True


class FactoryPaymentMethod(ABC):
    factory = {}

    @classmethod
    def get_payment_object(cls, method_type, **kwargs):
        k = method_type.strip().lower()
        if k not in cls.factory:
            raise ValueError(f"Unsupported method '{method_type}' for {cls.__name__}.")
        return cls.factory[k](**kwargs)

    @classmethod
    def register_payment_method(cls, method_type, payment_class):
        cls.factory[method_type.strip().lower()] = payment_class


class RazorpayFactory(FactoryPaymentMethod):
    factory = {"card": RazorpayCardPayment, "upi": RazorpayUPIPayment}


class StripeFactory(FactoryPaymentMethod):
    factory = {"card": StripeCardPayment, "upi": StripeUPIPayment}


class Aggregator(ABC):
    def __init__(self, name, processing_fee, payment_factory):
        self.name = name
        self.processing_fee = processing_fee
        self.payment_factory = payment_factory

    def call_get_payment_object(self, method_type, amount, **kwargs):
        payment_obj = self.payment_factory.get_payment_object(method_type, **kwargs)
        fee = amount * (self.processing_fee / 100.0)
        total = amount + fee

        print(f"[{self.name}] Base: ${amount:.2f} | Fee: ${fee:.2f} | Total: ${total:.2f}")
        return payment_obj.pay(total)


class RazorpayAggregator(Aggregator):
    def __init__(self, processing_fee=2.0):
        super().__init__("Razorpay", processing_fee, RazorpayFactory)


class StripeAggregator(Aggregator):
    def __init__(self, processing_fee=2.9):
        super().__init__("Stripe", processing_fee, StripeFactory)


class AggregatorFactory:
    factory = {
        "stripe": StripeAggregator,
        "razorpay": RazorpayAggregator,
    }

    @classmethod
    def get_aggregator_object(cls, aggregator_name):
        key = aggregator_name.strip().lower()
        if key not in cls.factory:
            raise KeyError(f"Invalid aggregator '{aggregator_name}'. Available: {list(cls.factory.keys())}")
        return cls.factory[key]()

    @classmethod
    def register_aggregator(cls, name, aggregator_cls):
        cls.factory[name.strip().lower()] = aggregator_cls


def run_cli():
    try:
        agg_choice = input("Aggregator (stripe/razorpay): ").strip()
        agg = AggregatorFactory.get_aggregator_object(agg_choice)

        method_choice = input("Method (card/upi): ").strip().lower()
        params = {}

        if method_choice == "card":
            card_no = input("Card No: ").strip()
            if not card_no.isdigit() or len(card_no) < 12:
                raise ValueError("Invalid Card No.")
            params["card_number"] = card_no
        elif method_choice == "upi":
            upi_id = input("UPI ID: ").strip()
            if "@" not in upi_id:
                raise ValueError("Invalid UPI ID.")
            params["upi_id"] = upi_id
        else:
            raise ValueError("Invalid selection.")

        amt = float(input("Amount ($): ").strip())
        if amt <= 0:
            raise ValueError("Amount must be > 0.")

        res = agg.call_get_payment_object(method_choice, amt, **params)
        print("Success." if res else "Failed.")

    except Exception as e:
        print(f"Error: {e}")


def extension_demo():
    class PayPalCardPayment(PaymentMethod):
        def __init__(self, card_number, **kwargs):
            self.card_number = str(card_number)

        def get_details(self):
            return f"PayPal Card [****{self.card_number[-4:]}]"

        def pay(self, amount):
            print(f"[PayPal] Pay ${amount:.2f}... OK")
            return True

    class PayPalFactory(FactoryPaymentMethod):
        factory = {"card": PayPalCardPayment}

    class PayPalAggregator(Aggregator):
        def __init__(self, processing_fee=3.5):
            super().__init__("PayPal", processing_fee, PayPalFactory)

    AggregatorFactory.register_aggregator("paypal", PayPalAggregator)
    pp_agg = AggregatorFactory.get_aggregator_object("paypal")
    pp_agg.call_get_payment_object("card", 250.00, card_number="5500000012349999")


if __name__ == "__main__":
    stripe = AggregatorFactory.get_aggregator_object("stripe")
    stripe.call_get_payment_object("upi", 100.0, upi_id="user@stripe")
    extension_demo()
