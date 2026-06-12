# fix_protocol/fix_parser.py

import sys

SOH = "\x01"

TAG_NAMES = {
    8: "BeginString",
    9: "BodyLength",
    10: "CheckSum",
    11: "ClOrdID",
    34: "MsgSeqNum",
    35: "MsgType",
    38: "OrderQty",
    40: "OrdType",
    44: "Price",
    49: "SenderCompID",
    52: "SendingTime",
    54: "Side",
    55: "Symbol",
    56: "TargetCompID",
    59: "TimeInForce",
    60: "TransactTime",
    98: "EncryptMethod",
    108: "HeartBtInt",
    141: "ResetSeqNumFlag",
    150: "ExecType",
    151: "LeavesQty",
    39: "OrdStatus",
    14: "CumQty",
    17: "ExecID",
    37: "OrderID",
}

MSG_TYPES = {
    "0": "Heartbeat",
    "1": "TestRequest",
    "2": "ResendRequest",
    "3": "Reject",
    "4": "SequenceReset",
    "5": "Logout",
    "A": "Logon",
    "D": "NewOrderSingle",
    "8": "ExecutionReport",
    "F": "OrderCancelRequest",
    "G": "OrderCancelReplaceRequest",
}

SIDE_VALUES = {
    "1": "Buy",
    "2": "Sell",
    "5": "Sell Short",
}

ORDTYPE_VALUES = {
    "1": "Market",
    "2": "Limit",
    "3": "Stop",
    "4": "Stop Limit",
}

TIF_VALUES = {
    "0": "Day",
    "1": "GTC",
    "3": "IOC",
    "4": "FOK",
}


def decode_value(tag, value):
    if tag == 35:
        return f"{value} ({MSG_TYPES.get(value, 'Unknown')})"

    if tag == 54:
        return f"{value} ({SIDE_VALUES.get(value, 'Unknown')})"

    if tag == 40:
        return f"{value} ({ORDTYPE_VALUES.get(value, 'Unknown')})"

    if tag == 59:
        return f"{value} ({TIF_VALUES.get(value, 'Unknown')})"

    return value


def parse_fix(raw_message):
    raw_message = raw_message.strip()

    # Support both pipe-delimited and actual SOH-delimited FIX
    raw_message = raw_message.replace("|", SOH)

    fields = []

    for pair in raw_message.split(SOH):
        if not pair:
            continue

        if "=" not in pair:
            fields.append(("?", "MalformedField", pair))
            continue

        tag_str, value = pair.split("=", 1)

        try:
            tag = int(tag_str)
        except ValueError:
            tag = tag_str

        tag_name = TAG_NAMES.get(tag, "UnknownTag")

        fields.append(
            (
                tag,
                tag_name,
                decode_value(tag, value),
            )
        )

    return fields


def print_message(raw_message):
    print("\n================ FIX MESSAGE ================\n")

    fields = parse_fix(raw_message)

    for tag, tag_name, value in fields:
        print(f"{str(tag):>4}  {tag_name:<20} {value}")

    print("\n=============================================\n")


def main():
    if len(sys.argv) > 1:
        raw_message = " ".join(sys.argv[1:])
    else:
        print("Paste FIX message:")
        raw_message = input().strip()

    print_message(raw_message)


if __name__ == "__main__":
    main()
