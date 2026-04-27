# The "it works on my machine" tax

Every team pays this tax. The senior engineer's laptop has six undocumented tools installed, and the new hire spends two weeks finding out which ones.

Reproducibility isn't glamorous. It doesn't ship features. It does, however, decide whether the next person to touch this code can.

Two practical fixes, in order. One: pin everything. Lockfiles, container images, system packages. If you're not pinning, you're rolling dice on every build. Two: write the setup steps down — in the repo, not a wiki. Wikis go stale. READMEs get updated when someone hits the same bug for the third time.

This is boring work. Do it anyway.
