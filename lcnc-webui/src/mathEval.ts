// Safe recursive-descent math expression evaluator.
// Supports: integers/decimals, + − × ÷, unary ±, parentheses.
// No eval(), no Function(). Returns null on any invalid input.

type Token = number | '+' | '-' | '*' | '/' | '(' | ')';

function tokenize(expr: string): Token[] | null {
  const tokens: Token[] = [];
  let i = 0;
  while (i < expr.length) {
    const c = expr[i]!;
    if (c === ' ' || c === '\t') { i++; continue; }
    if (/[0-9]/.test(c) || (c === '.' && i + 1 < expr.length && /[0-9]/.test(expr[i + 1]!))) {
      let num = '';
      while (i < expr.length && /[0-9.]/.test(expr[i]!)) num += expr[i++]!;
      const n = parseFloat(num);
      if (isNaN(n)) return null;
      tokens.push(n);
      continue;
    }
    if (c === '+' || c === '-' || c === '*' || c === '/' || c === '(' || c === ')') {
      tokens.push(c as Token);
      i++;
      continue;
    }
    return null; // unknown character
  }
  return tokens;
}

interface S { t: Token[]; pos: number }

function parseExpr(s: S): number {
  let v = parseTerm(s);
  while (s.pos < s.t.length) {
    const op = s.t[s.pos];
    if (op !== '+' && op !== '-') break;
    s.pos++;
    const r = parseTerm(s);
    v = op === '+' ? v + r : v - r;
  }
  return v;
}

function parseTerm(s: S): number {
  let v = parseFactor(s);
  while (s.pos < s.t.length) {
    const op = s.t[s.pos];
    if (op !== '*' && op !== '/') break;
    s.pos++;
    const r = parseFactor(s);
    if (op === '/') {
      if (r === 0) throw new Error('div0');
      v = v / r;
    } else {
      v = v * r;
    }
  }
  return v;
}

function parseFactor(s: S): number {
  if (s.pos >= s.t.length) throw new Error('eof');
  const tok = s.t[s.pos]!;
  if (tok === '-') { s.pos++; return -parseFactor(s); }
  if (tok === '+') { s.pos++; return parseFactor(s); }
  if (tok === '(') {
    s.pos++;
    const v = parseExpr(s);
    if (s.t[s.pos] !== ')') throw new Error('paren');
    s.pos++;
    return v;
  }
  if (typeof tok === 'number') { s.pos++; return tok; }
  throw new Error(`tok:${String(tok)}`);
}

export function evaluate(expression: string): number | null {
  const trimmed = expression.trim();
  if (!trimmed) return null;
  const tokens = tokenize(trimmed);
  if (!tokens || tokens.length === 0) return null;
  try {
    const s: S = { t: tokens, pos: 0 };
    const result = parseExpr(s);
    if (s.pos !== s.t.length) return null; // trailing junk
    return isFinite(result) ? result : null;
  } catch {
    return null;
  }
}

/** Format a result number: integers stay whole, floats get up to 6 decimal places. */
export function fmtEval(n: number): string {
  if (Number.isInteger(n)) return String(n);
  return String(parseFloat(n.toFixed(6)));
}
