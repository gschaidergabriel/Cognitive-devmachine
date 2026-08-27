# A real failure: the edit that deleted most of a file

On 2026-08-28, the first live Frankenstein direct-dispatch tried to make a small change to `tools/grid10_fabric.py`.

Instead of editing the existing file, the helper was asked to return the **complete file** without having been given the complete current file. It produced a plausible replacement that was only **87 lines long for a file that had been 672 lines**.

The bad commits stayed local on the VPS and were reset before they reached the shared repository. That containment is useful evidence. It is not a success claim for the editor.

## What this changed

The immediate source fix now shows the helper the real current contents and rejects very large shrinkage. But a simple “must stay above 50% of the old size” rule is only a guardrail, not a proof of safe editing.

A safer general rule is:

```text
existing file
→ identify exact pre-edit bytes
→ propose a bounded patch/diff
→ prove the patch applies to those bytes
→ inspect the resulting diff for unrelated deletion
→ run the real acceptance test
→ commit only after all gates pass
```

Why patch/diff first? Because the task is usually “change this part,” not “recreate everything else correctly from memory.”

## What is still unproven

A patch can also be dangerous. A malicious or mistaken patch can deliberately delete unrelated code, and a narrow test can still pass. So patch syntax alone is not safety.

The remaining engineering requirement is to combine patch-based editing with exact source identity and scope checks: changed paths, deletion budget, unchanged-region or semantic preservation checks where appropriate, and tests whose coverage matches the claim.

This is a good example of the project's evidence rule:

> **A successful-looking output is not the same thing as a preserved system.**

The current supervisor keeps retained runtime credit for this Frankenstein direct-dispatch path **unpromoted** until an independent, clean, non-provider review and re-execution succeeds. Whole EntityOS/HCU, full HCU, Physical GRID10, canonical-semantics, and training credit remain zero at this frontier.

For the fused technical evidence and falsifiers, see [`../DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_DIRECT_DISPATCH_NEGATIVE_RESULT_2026-08-28.md`](../DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_DIRECT_DISPATCH_NEGATIVE_RESULT_2026-08-28.md).