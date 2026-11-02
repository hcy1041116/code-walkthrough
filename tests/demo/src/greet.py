"""A tiny module the engine tests walk through."""
NAMES = ["Ada", "Lin"]


def greet(name: str, excited: bool = False) -> str:
    text = f"Hello, {name}"
    return text + ("!" if excited else ".")


def main():
    for n in NAMES:
        print(greet(n, excited=True))


if __name__ == "__main__":
    main()
