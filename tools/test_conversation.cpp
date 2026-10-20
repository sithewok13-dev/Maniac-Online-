// Portable conversation contract: ordering, backpressure, departures and
// fallback, without a model, UI or game data. Build with sanitizers:
// c++ -std=c++11 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine tools/test_conversation.cpp
#include "common/scummverse_conversation.h"
#include <cassert>
#include <iostream>
using Scummverse::Conversation;
using Scummverse::LineKind;
using Scummverse::ReplyJob;

static std::string transcript(const Conversation &c) {
	std::string out;
	for (const auto &line : c.lines()) {
		out += std::to_string(line.speaker); out += line.kind == LineKind::Classic ? "c:" : ":";
		out += line.text; out += "|";
	}
	return out;
}

int main() {
	const unsigned edna = 1u << 10, fred = 1u << 9, zak = 1u << 24;
	Conversation c;
	ReplyJob job{0, 0};

	// Nobody to talk to: nothing is accepted or scheduled.
	assert(!c.submit("hello") && !c.nextJob(job) && !c.busy());
	c.reset(edna);
	assert(!c.submit("") && !c.submit("   ") && !c.submit(std::string(513, 'x')));
	assert(c.submit(std::string(512, 'x'))); c.reset(edna);

	// A message sent while a reply is pending waits; the transcript stays causal.
	assert(c.submit("A"));
	assert(c.nextJob(job) && job.speaker == 10);
	const uint32_t first = job.ticket;
	assert(c.submit("B"));
	assert(c.outbox().size() == 1 && c.outbox().front() == "B");
	assert(!c.nextJob(job)); // One reply at a time.
	assert(transcript(c) == "0:A|");
	assert(!c.complete(first + 7, "wrong ticket", "x")); // Stale ticket ignored.
	assert(c.complete(first, "Reply to A.", "classic"));
	assert(!c.complete(first, "duplicate", "x")); // Completion is idempotent.
	assert(c.nextJob(job) && job.speaker == 10);
	assert(transcript(c) == "0:A|10:Reply to A.|0:B|");
	assert(c.complete(job.ticket, "", "Classic line.")); // Empty model reply.
	assert(transcript(c) == "0:A|10:Reply to A.|0:B|10c:Classic line.|");
	assert(!c.busy() && !c.nextJob(job));

	// Backpressure: at most kMaxQueued waiting messages; rejection keeps state.
	for (size_t n = 0; n < Conversation::kMaxQueued; ++n) assert(c.submit("q" + std::to_string(n)));
	const uint32_t revision = c.revision();
	assert(!c.submit("overflow") && c.revision() == revision);
	while (c.nextJob(job)) assert(c.complete(job.ticket, "ok.", ""));
	assert(c.outbox().empty() && c.lines().back().text == "ok.");

	// Groups: two replies per message, rotating who leads.
	c.reset(edna | fred | zak);
	int leads[3] = {};
	for (int round = 0; round < 3; ++round) {
		assert(c.submit("hi"));
		int speakers[2] = {}, count = 0;
		while (c.nextJob(job)) { speakers[count++] = job.speaker; assert(c.complete(job.ticket, "yes.", "")); }
		assert(count == 2 && speakers[0] != speakers[1]);
		leads[round] = speakers[0];
	}
	assert(leads[0] == 9 && leads[1] == 10 && leads[2] == 24);

	// A departing in-flight speaker is cancelled; queued absentees are skipped;
	// their earlier lines remain attributed in the transcript.
	c.reset(edna | fred);
	assert(c.submit("Who stays?") && c.nextJob(job));
	const int leaving = job.speaker; const uint32_t ticket = job.ticket;
	const unsigned remaining = (edna | fred) & ~(1u << leaving);
	assert(c.setParticipants(remaining));
	assert(!c.complete(ticket, "too late.", "")); // Late output never appears.
	assert(c.nextJob(job) && job.speaker != leaving);
	assert(c.complete(job.ticket, "I stay.", ""));
	assert(!c.busy());
	assert(!c.setParticipants(remaining)); // Unchanged membership is a no-op.
	c.setParticipants(0);
	assert(!c.submit("anyone?")); // Everyone left.

	// Joining mid-conversation affects the next scheduled message only.
	c.reset(edna);
	assert(c.submit("one") && c.nextJob(job));
	c.setParticipants(edna | fred);
	assert(c.complete(job.ticket, "first.", ""));
	assert(!c.nextJob(job)); // Fred was not scheduled for "one".
	assert(c.submit("two"));
	int answered = 0; while (c.nextJob(job)) { ++answered; c.complete(job.ticket, "sure.", ""); }
	assert(answered == 2);

	// Context for models excludes classic fallback and keeps order.
	c.reset(edna);
	c.submit("x"); c.nextJob(job); c.complete(job.ticket, "", "filler.");
	c.submit("y"); c.nextJob(job); c.complete(job.ticket, "real.", "");
	auto context = c.context(6);
	assert(context.size() == 3 && context[0].text == "x" && context[1].text == "y" && context[2].text == "real.");
	assert(c.context(1).size() == 1 && c.context(1)[0].text == "real.");

	// IDs never repeat across resets; the transcript is bounded.
	const uint32_t last = c.lines().back().id;
	c.reset(edna);
	for (size_t n = 0; n < Conversation::kMaxLines; ++n) { c.submit("m"); c.nextJob(job); c.complete(job.ticket, "r.", ""); }
	assert(c.lines().size() == Conversation::kMaxLines && c.lines().front().id > last);
	for (size_t n = 1; n < c.lines().size(); ++n) assert(c.lines()[n].id == c.lines()[n - 1].id + 1);

	// The player bit (0) can never become a participant.
	c.reset(1u | edna); assert(c.participants() == edna);

	// Participants past 32 bits (wanderers visiting, IDs 30..55) answer in
	// turn and leave like anyone.
	{
		const uint64_t guybrush = uint64_t(1) << 30, indy = uint64_t(1) << 55, last = uint64_t(1) << 63;
		Conversation w; w.reset(guybrush | indy | last);
		assert(w.participants() == (guybrush | indy | last));
		ReplyJob a, b; w.submit("Ahoy"); assert(w.nextJob(a) && a.speaker == 30); w.complete(a.ticket, "Arr.", "");
		assert(w.nextJob(b) && b.speaker == 55);
		assert(w.setParticipants(guybrush)); // Indy leaves mid-reply: cancelled.
		w.submit("Again"); assert(w.nextJob(a) && a.speaker == 30);
	}
	std::cout << "PASS: conversation ordering, backpressure, stale tickets, departures, groups, context and bounds\n";
}
