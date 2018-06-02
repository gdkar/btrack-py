# btrack-py

an attempt at working through ideas for a BTrack replacement in a flexible scripting language before hashing them out in c++ or whatever.

## thoughts

### basic core notions

1.  we should recompute tempo estimates at regular non-current-tempo-dependant intervals
2.  tempo calculations actually apply as of somewhere in the middle of the correlation buffer, everything after that is speculation
3.  once you've told clients that sample N is beat number B that's kinda committed. invalidations shouldn't change *that*. however, if additional information appears which tells us that we *should* have done something different, internally pretend we *did* and compute future beats accordingly. this approach is, um, a little odd to get used to but i'm fairly confident it's the, like, correct thing to be doing in this kinda real-time or actually-latency-corrected-into-the-future sort of thing. yes, this means the beat number vs. time curve will, in effect, be operating at a ~fixed offset of whatever our prediction / prediction error ends up being from the internal best-estimate-of-ground-truth, but it won't *diverge over time*
4.  we should be trying to provide an answer of what is the *beat number, including fraction, at the queried time* and, secondarily, *at what time did / will beat number B occur.* the quarried time should be allowed to be "in the future" relative to the last *committed* beat number, at plausibly in the future absolute ( to allow for latency compensation and things. ) how *far* in the future we're okay with is kinda up for debate, and interacts directly with the point above about "not rewriting what we've told clients." obviously if we allow quarries arbitrarily far into the future, then the distance between the two beat-number curves could become arbitrarily great, and prooobably we don't want that. at the moment i'm gonna pick "half a beat" basically out of a hat. we can re-evaluate that call once we have some experience with this system.
5.  it should be ~easy for the user to influence this whole process. our whole game is somewhere on the spectrum between "user assisted / computer generated" and "computer assisted / human generated" art, but either way, it's 100% the VJ's call what should have happened. on *that* note:
    *   we should support "tap for tempo and alignment." at the moment i'm gonna say this should just add a bunch of virtual odf into the odf buffer at the specified tap time, and possibly invalidate things accordingly
    *   we should support "tap for downbeat," which shouldn't do *anything* except adjust the integral beat numbers assigned to the beat locations we're computing.
    *   we should support "tap for No Really This Right Here Is Beat Zero," which should basically.... nuke the entire queued beat buffer. that time *is* beat zero. if it's in the future, we might not really have to invalidate stuff, but regardless that's the internal *and* external beat zero now, so flush all following beat locations and redo 'em. yes, this violates the *fuck* out of our core principles, but this operation is also *fucking necessary* for the system to provide a not shit experience for actual human users. :\

### buffers to keep track of, and their time bases:

1.  sample time base:
    *   input audio. that's.... really it. honestly we should never *ever* have to rewind this, so... shrug.
2.  tempo recompute time base:
    *   tempo estimates. invalidated by odf value invalidation, and by new tempo estimate comp, because the *actual* time that a tempo estimate applies is always going to be somewhere in the average time of the correlation buffer and we're extrapolating out from there.
    *   tempo observation arrays. yyyyeah, we've gotta fuckin' hold onto these fuckers, because... we can invalidate and need to roll back. oh well life is hard sometimes. only need the actual observations, tho, not the correlation results and what have you.
3.  beat time base:
    *   um. beats. obviously. these have to track the progress of both what we actually told clients and what to the best of our knowledge we *should* have told clients. probably each beat also should include some number of fractional committals, to account for clients asking about their future and what they shall be, que sera sera, etc.
        *   the internal part is invalidated by anything that invalidates tempo estimates *or* cumulative score estimates.
        *   the external part is invalidated only by the harshest type of user input tap.
4.  odf time base:
    *   raw odf values. computed when enough input audio accumulates / only invalidated by ( possibly ) tapping input.
    *   cumulative odf values. these are the tricky bastards. we have...
        +   every new raw odf sample invalidates all fully-after-data predicted future cumulative values. always. regardless of everything. because "truly the future" samples are computed *without* decay, whereas "truly observed" samples are computed *with* decay, so even if we add a zero sample we still have to invalidate. eugh.
        +   every time we add a new tempo estimate that differs from what we'd projected the tempo value to be, invalidate back to that point. if the tempo projection was actually right ( i.e., the testimated tempo is constant for a bit ) we don't have to invalidate *anything* on that account.
        +   every time we retroactively invalidate tempo estimates, invalidate back to the last valid tempo estimate, obvs.


### operation

on audio -> compute odf sample

on odf sample ->
*   invalidate the cumulative obs data
*   possibly compute tempo
*   possibly compute beat

on tempo sample ->
*   invalidate the cumulative obs data

on cumulative obs invalidation ->
*   invalidate beats

that's.... i think the entire workflow, actually. cool.
