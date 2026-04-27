# Why your tests are slow

Slow tests are a tax on every change you make. Death by a thousand cuts.

The fix isn't more parallelism. Parallelism is a workaround. The fix is asking, for each test, what it actually exercises. Half the time, the answer is "boot the whole app to check one helper function." That's the bug.

Pull the helper out. Test it directly. Stop pretending integration tests are a substitute for unit tests — they're a complement, not a replacement.

I keep a rule: if the suite goes over five seconds locally, I stop and look. Five seconds isn't a benchmark, it's a smell. Something's grown legs.
