# ClayCode BASE — 14 blocker attack report

## Result

A new executable BASE candidate was built instead of writing another prose-only language proposal. The local Linux proof passes APP-01 through APP-09, 5,000 differential cases, 1,000 authority-denial mutations, G9 cycle parsing, type/effect negative controls, a real Tk/X11 event loop under Xvfb and an independent C/gcc native backend smoke test.

The work also reproduced and repaired the earlier G9 grammar defect: `if` was used by the admitted G9 V3 cycle but absent from `grammar.ebnf`. During implementation two additional concrete parser defects surfaced and were fixed: G9 `cycle(input,node)` was silently missed by the extractor, and current FRANK constructor calls use named fields (`realized=current`). The executable parser now handles those cases and preserves G9's `receipt? or residual` as explicit coalesce IR.

## Application evidence

- APP-01 CLI/file state: evaluator == generated target.
- APP-02 real loopback HTTP server: evaluator == generated target.
- APP-03 SQLite transactional state: evaluator == generated target; explicit transaction bug found and repaired.
- APP-04 asyncio concurrency + cancellation + lock-backed atomic increment: evaluator == target.
- APP-05 Tk event loop under Xvfb: evaluator == target.
- APP-06 safe compiler/tool adapter: evaluator == target.
- APP-07 NumPy numerical backend: evaluator == target.
- APP-08 harmless Linux system effect under explicit capability authority: evaluator == target; missing authority denied.
- APP-09 exact current FRANK `frame` function body: evaluator == generated target with explicit pure dependency bindings.
- APP-10 full FRANK handoff: **not claimed**.

## Gate boundary

The 14 BASE work packages are no longer an undifferentiated list. The executable implementation supplies concrete evidence for every package and locally closes/provisionally closes the evaluator, FFI, concurrency, conformance and corpus portions. Two mandatory acceptance conditions remain outside what this session can truthfully manufacture:

1. compile/execute the **full frozen FRANK handoff** without semantic escape hatches;
2. rerun the accepted suite on **Andreas' exact Ubuntu developer system**.

Therefore `GENERAL_PURPOSE_GATE` remains `NOT_PASS` until those receipts exist. GitHub Ubuntu CI is added as an independent platform check, but it does not pretend to be Andreas' machine.
