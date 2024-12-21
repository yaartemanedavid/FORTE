def parse_duration(input_str: str) -> int:
    return int(input_str.split('#')[1].rstrip('s'))
