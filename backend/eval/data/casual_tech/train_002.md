# Logs you'll actually read

Most logs are noise. You scroll past them looking for the thing that broke. That's not logging — that's archaeology.

A useful log line answers one question: what was the system doing, and what did it decide? Not "entered function X." Not "got value Y." Decisions. State transitions. The points where, six months from now, you'll need to know *why* something happened.

JSON formatting beats free-text every time. You can grep free-text. You can query JSON. The difference compounds.

And add a request ID. Always. Without it, you're stitching timelines together by hand.
