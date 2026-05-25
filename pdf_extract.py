import sys, zlib, re

def extract_streams(data):
    """Yield decompressed stream bytes for FlateDecode streams."""
    out = []
    idx = 0
    while True:
        s = data.find(b'stream', idx)
        if s == -1:
            break
        # find the dict before 'stream'
        dict_start = data.rfind(b'<<', 0, s)
        header = data[dict_start:s] if dict_start != -1 else b''
        # stream data starts after 'stream' + EOL
        p = s + len(b'stream')
        if data[p:p+2] == b'\r\n':
            p += 2
        elif data[p:p+1] in (b'\n', b'\r'):
            p += 1
        e = data.find(b'endstream', p)
        if e == -1:
            break
        raw = data[p:e]
        idx = e + len(b'endstream')
        if b'FlateDecode' in header:
            try:
                dec = zlib.decompress(raw)
            except Exception:
                # try trimming trailing bytes
                try:
                    dec = zlib.decompressobj().decompress(raw)
                except Exception:
                    continue
            out.append((header, dec))
    return out

def text_from_content(dec):
    """Extract text strings from a content stream (Tj/TJ operators)."""
    texts = []
    # Match (...) strings, handling escaped parens
    # Tokenize TJ arrays and Tj strings
    i = 0
    n = len(dec)
    # Find all parenthesized strings in order, also track BT/ET and TD/Td/T* for spacing
    # Simpler: extract all (...) literal strings
    result = []
    buf = bytearray()
    depth = 0
    escaped = False
    in_str = False
    out_chars = []
    j = 0
    s = dec
    while j < len(s):
        c = s[j:j+1]
        if in_str:
            if escaped:
                # handle octal? keep simple
                mapping = {b'n':b'\n', b'r':b'\r', b't':b'\t', b'b':b'\b', b'f':b'\f', b'(':b'(', b')':b')', b'\\':b'\\'}
                if c in mapping:
                    buf += mapping[c]
                elif c.isdigit():
                    # octal up to 3 digits
                    oct_digits = c
                    k = j+1
                    while k < len(s) and len(oct_digits) < 3 and s[k:k+1].isdigit():
                        oct_digits += s[k:k+1]
                        k += 1
                    try:
                        buf += bytes([int(oct_digits,8) & 0xFF])
                    except Exception:
                        pass
                    j = k
                    escaped = False
                    continue
                else:
                    buf += c
                escaped = False
            else:
                if c == b'\\':
                    escaped = True
                elif c == b'(':
                    depth += 1
                    buf += c
                elif c == b')':
                    if depth == 0:
                        in_str = False
                        out_chars.append(bytes(buf))
                        buf = bytearray()
                    else:
                        depth -= 1
                        buf += c
                else:
                    buf += c
        else:
            if c == b'(':
                in_str = True
                depth = 0
        j += 1
    return out_chars

def main():
    path = sys.argv[1]
    page_filter = None
    with open(path,'rb') as f:
        data = f.read()
    streams = extract_streams(data)
    all_text = []
    for header, dec in streams:
        # only content streams (heuristic: contains BT or Tj or TJ)
        if b'BT' in dec or b'Tj' in dec or b'TJ' in dec:
            chars = text_from_content(dec)
            if chars:
                # join with spaces; decode latin-1 as fallback
                txt = b' '.join(chars).decode('latin-1', errors='replace')
                all_text.append(txt)
    print('\n'.join(all_text))

if __name__ == '__main__':
    main()
