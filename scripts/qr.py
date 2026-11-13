"""Minimal QR Code encoder (byte mode, error correction M). Based on the public QR spec / Nayuki's reference design."""
ECC_M = 0  # format bits index for M is 0b00
# (ec codewords per block, num blocks) for level M, versions 1..20
EC_M = {1:(10,1),2:(16,1),3:(26,1),4:(18,2),5:(24,2),6:(16,4),7:(18,4),8:(22,4),9:(22,5),10:(26,5),
        11:(30,5),12:(22,8),13:(22,9),14:(24,9),15:(24,10),16:(28,10),17:(28,11),18:(26,13),19:(26,14),20:(26,16)}

def num_raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        n = ver // 7 + 2
        r -= (25 * n - 10) * n - 55
        if ver >= 7: r -= 36
    return r

def num_data_codewords(ver):
    ec, blocks = EC_M[ver]
    return num_raw_modules(ver) // 8 - ec * blocks

def rs_divisor(degree):
    res = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            res[j] = rs_mul(res[j], root)
            if j + 1 < degree: res[j] ^= res[j + 1]
        root = rs_mul(root, 0x02)
    return res

def rs_remainder(data, div):
    res = [0] * len(div)
    for b in data:
        factor = b ^ res.pop(0)
        res.append(0)
        for i, coef in enumerate(div):
            res[i] ^= rs_mul(coef, factor)
    return res

def rs_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z & 0xFF

def encode(text):
    data = text.encode('utf-8')
    for ver in range(1, 21):
        cc_bits = 8 if ver <= 9 else 16
        if 4 + cc_bits + 8 * len(data) <= num_data_codewords(ver) * 8: break
    else: raise ValueError('too long')
    bits = []
    def app(val, n): bits.extend((val >> i) & 1 for i in reversed(range(n)))
    app(0b0100, 4); app(len(data), cc_bits)
    for b in data: app(b, 8)
    cap = num_data_codewords(ver) * 8
    app(0, min(4, cap - len(bits)))
    app(0, (8 - len(bits) % 8) % 8)
    pad = 0xEC
    while len(bits) < cap: app(pad, 8); pad ^= 0xEC ^ 0x11
    cws = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    # interleave with ECC
    ec_len, nblocks = EC_M[ver]
    raw = num_raw_modules(ver) // 8
    n_short = nblocks - raw % nblocks
    short_len = raw // nblocks
    div = rs_divisor(ec_len)
    blocks, k = [], 0
    for i in range(nblocks):
        dlen = short_len - ec_len + (0 if i < n_short else 1)
        dat = cws[k:k + dlen]; k += dlen
        ecc = rs_remainder(dat, div)
        if i < n_short: dat = dat + [0]
        blocks.append(dat + ecc)
    result = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != short_len - ec_len or j >= n_short:
                result.append(blk[i])
    return ver, result

def build(text):
    ver, cws = encode(text)
    size = ver * 4 + 17
    m = [[False] * size for _ in range(size)]
    fn = [[False] * size for _ in range(size)]
    def setf(x, y, dark): m[y][x] = dark; fn[y][x] = True
    for i in range(size):
        setf(6, i, i % 2 == 0); setf(i, 6, i % 2 == 0)
    def finder(x, y):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                xx, yy = x + dx, y + dy
                if 0 <= xx < size and 0 <= yy < size:
                    d = max(abs(dx), abs(dy)); setf(xx, yy, d not in (2, 4))
    finder(3, 3); finder(size - 4, 3); finder(3, size - 4)
    if ver > 1:
        n = ver // 7 + 2
        step = 26 if ver == 32 else (ver * 4 + n * 2 + 1) // (n * 2 - 2) * 2
        pos = [6] + [size - 7 - i * step for i in range(n - 1)][::-1]
        for i in range(n):
            for j in range(n):
                if (i == 0 and j == 0) or (i == 0 and j == n - 1) or (i == n - 1 and j == 0): continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setf(pos[i] + dx, pos[j] + dy, max(abs(dx), abs(dy)) != 1)
    def draw_format(mask):
        data = (ECC_M << 3) | mask
        rem = data
        for _ in range(10): rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = ((data << 10) | rem) ^ 0x5412
        g = lambda i: ((bits >> i) & 1) != 0
        for i in range(6): setf(8, i, g(i))
        setf(8, 7, g(6)); setf(8, 8, g(7)); setf(7, 8, g(8))
        for i in range(9, 15): setf(14 - i, 8, g(i))
        for i in range(8): setf(size - 1 - i, 8, g(i))
        for i in range(8, 15): setf(8, size - 15 + i, g(i))
        setf(8, size - 8, True)
    draw_format(0)
    if ver >= 7:
        rem = ver
        for _ in range(12): rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = (ver << 12) | rem
        for i in range(18):
            b = ((bits >> i) & 1) != 0
            a, c = size - 11 + i % 3, i // 3
            setf(a, c, b); setf(c, a, b)
    # data
    i = 0
    right = size - 1
    while right >= 1:
        if right == 6: right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                upward = ((right + 1) & 2) == 0
                y = size - 1 - vert if upward else vert
                if not fn[y][x] and i < len(cws) * 8:
                    m[y][x] = ((cws[i >> 3] >> (7 - (i & 7))) & 1) != 0
                    i += 1
        right -= 2
    masks = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]
    def apply(k):
        for y in range(size):
            for x in range(size):
                if not fn[y][x] and masks[k](x, y): m[y][x] = not m[y][x]
    def penalty():
        p = 0
        for grid in (m, [list(r) for r in zip(*m)]):
            for row in grid:
                run, prev = 0, None
                for c in row:
                    if c == prev: run += 1
                    else:
                        if run >= 5: p += run - 2
                        run, prev = 1, c
                if run >= 5: p += run - 2
                s = ''.join('1' if c else '0' for c in row)
                for pat in ('10111010000', '00001011101'): p += 40 * s.count(pat)
        for y in range(size - 1):
            for x in range(size - 1):
                if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]: p += 3
        dark = sum(sum(r) for r in m); total = size * size
        p += (abs(dark * 20 - total * 10) + total - 1) // total * 10 - 10 if False else (abs(dark * 20 - total * 10) // total) * 10
        return p
    best, best_p = 0, None
    for k in range(8):
        apply(k); draw_format(k)
        pp = penalty()
        if best_p is None or pp < best_p: best, best_p = k, pp
        apply(k)
    apply(best); draw_format(best)
    return m

def svg(text, dark='#0d1a2d', margin=2):
    m = build(text); n = len(m)
    d = ''.join(f'M{x + margin},{y + margin}h1v1h-1z' for y in range(n) for x in range(n) if m[y][x])
    s = n + margin * 2
    return f'<svg viewBox="0 0 {s} {s}" shape-rendering="crispEdges" aria-hidden="true"><rect width="100%" height="100%" fill="#fff"/><path d="{d}" fill="{dark}"/></svg>'
