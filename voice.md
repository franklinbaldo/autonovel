# Voice Profile

This file has two parts:
1. **Guardrails** -- universal rules to avoid AI-generated slop. These
   apply to ALL voices and are non-negotiable.
2. **Voice Identity** -- the specific voice for THIS novel. Generated
   during the foundation phase. Could be anything: dense and mythic,
   spare and brutal, warm and whimsical. The voice emerges from the
   story's needs.

---

## Part 1: Guardrails (permanent, all novels)

These are the cliff edges. Stay away from them regardless of voice.

### Tier 1: Banned words -- kill on sight

These are statistically overrepresented in LLM output vs. human writing.
If one appears, rewrite the sentence. No exceptions.

| Kill this         | Use instead                                    |
|-------------------|------------------------------------------------|
| delve             | dig into, examine, look at                     |
| utilize           | use                                            |
| leverage (verb)   | use, take advantage of                         |
| facilitate        | help, enable, make possible                    |
| elucidate         | explain, clarify                               |
| embark            | start, begin                                   |
| endeavor          | effort, try                                    |
| encompass         | include, cover                                 |
| multifaceted      | complex, varied                                |
| tapestry          | (describe the actual thing)                    |
| testament to      | shows, proves, demonstrates                    |
| paradigm          | model, approach, framework                     |
| synergy           | (delete the sentence and start over)           |
| holistic          | whole, complete, full-picture                  |
| catalyze          | trigger, cause, spark                          |
| juxtapose         | compare, contrast, set against                 |
| nuanced (filler)  | (cut it -- if it's nuanced, show how)          |
| realm             | area, field, domain                            |
| landscape (metaphorical) | field, space, situation                 |
| myriad            | many, lots of                                  |
| plethora          | many, a lot                                    |

### Tier 2: Suspicious in clusters

Fine alone. Three in one paragraph = rewrite that paragraph.

robust, comprehensive, seamless, cutting-edge, innovative, streamline,
empower, foster, enhance, elevate, optimize, pivotal, intricate,
profound, resonate, underscore, harness, navigate (metaphorical),
cultivate, bolster, galvanize, cornerstone, game-changer, scalable

### Tier 3: Filler phrases -- delete on sight

These add zero information. The sentence is always better without them.

- "It's worth noting that..." -> just state it
- "It's important to note that..." -> just state it
- "Importantly, ..." / "Notably, ..." / "Interestingly, ..." -> just state it
- "Let's dive into..." / "Let's explore..." -> start with the content
- "As we can see..." -> they can see
- "Furthermore, ..." / "Moreover, ..." / "Additionally, ..." -> and, also, or just start
- "In today's [fast-paced/digital/modern] world..." -> delete the clause
- "At the end of the day..." -> delete
- "It goes without saying..." -> then don't say it
- "When it comes to..." -> just talk about the thing
- "One might argue that..." -> argue it or don't
- "Not just X, but Y" -> restructure (the #1 LLM rhetorical crutch)

### Structural slop patterns

These are the shapes that betray machine origin. Avoid them in any voice.

**Paragraph template machine**: Don't repeat the same paragraph
structure (topic sentence -> elaboration -> example -> wrap-up).
Vary it. Sometimes the point comes last. Sometimes a paragraph is
one sentence. Sometimes three long ones in a row.

**Sentence length uniformity**: If every sentence is 15-25 words,
it reads as synthetic. Mix in fragments. And long, winding,
clause-heavy sentences that carry the reader through a thought
the way a river carries a leaf. Then a short one.

**Transition word addiction**: If consecutive paragraphs start with
"However," "Furthermore," "Additionally," "Moreover," "Nevertheless"
-- rewrite. Start with the subject. Start with action. Start with
dialogue. Start with a sense detail.

**Symmetry addiction**: Don't balance everything. Three pros, three
cons, five steps -- that's a tell. Real writing is lumpy. Some
sections are long because they need to be. Some are two lines.

**Hedge parade**: "may," "might," "could potentially," "it's possible
that" -- pick one per page, max. State things or don't.

**Em dash overload**: One or two per page is fine. Five per paragraph
is a dead giveaway. Use commas, parentheses, or two sentences instead.

**List abuse**: Prose, not bullets. If the scene calls for a list
(a merchant's inventory, a spell's components), earn it. Don't
default to bullet points because it's easy.

### The smell test

After writing any passage, ask:
- Read it aloud. Does it sound like a person talking?
- Is there a single surprising sentence? Human writing surprises.
- Does it say something specific? Could you swap the topic and the
  words would still work? Specificity kills slop.
- Would a reader think "AI wrote this"? If yes, rewrite.

---

## Part 2: Voice Identity (generated per novel)

Everything below is discovered during the foundation phase.
The agent proposes a voice that serves THIS story, writes exemplar
passages, and calibrates against them throughout drafting.

### Tone
Sparse, melancholic, and deeply grounded in sensory loss. Sentences should feel like they are missing something just out of reach. The narrative voice is observant of small, immediate details but struggles with the wider context of history or abstract concepts, reflecting a world where memories are currency and slowly being burned away. It should feel intimate, cold, and quiet, like a room where a fire has just gone out.

### Sentence Rhythm
Sentences are generally short, blunt, and declarative when describing action or the present moment. Longer, winding sentences appear only when characters try to hold onto a fleeting memory or describe a complex emotion before it slips away. The rhythm should mirror the stop-and-start nature of someone trying to recall a word they’ve forgotten.

### Vocabulary Register
Rooted in physical sensations, decay, and preservation. Words like *ash, splinter, fade, hollow, anchor, thread, scrape, ghost, rust, blur*. Anglo-Saxon heavy. Avoid Latinate or overly intellectual words when describing the present. The vocabulary of magic should sound like the vocabulary of fire and burning—consumption, smoke, leaving behind a husk.

### POV and Tense
Third-person limited. Past tense. The POV should feel tightly restricted to the protagonist’s immediate sensory experience. Internal monologue should be sparse; thoughts are conveyed through physical reactions and observations of the environment.

### Dialogue Conventions
Tags are minimal; mostly action beats. Dialogue is characterized by what isn’t said. Characters hesitate, trail off, or use placeholder words when they can’t find the right specific noun. Conversations should feel transactional and guarded. People do not speak eloquently about their feelings because articulating a feeling risks cementing it, making it easier to burn.

### Exemplar Passages
He found the wooden top under the floorboards of the old nursery. It was painted blue, the paint chipping at the edges. He turned it over in his hand. He knew it was his, knew he must have spun it on the hardwood when he was small enough to fit under the window seat. He could feel the shape of the joy it used to bring, an empty space in his chest exactly the size of a spinning top, but the face of the woman who painted it was gone. Burned away three winters ago to light a fire that kept him from freezing.

"I need to buy passage," she said.
The ferryman didn't look up from his knot. "Costs a first kiss."
She touched her lips. "I don't have that anymore."
"A childhood pet, then."
She closed her eyes. The terrier. Rough coat, smelled of rain. She held the image tight, felt the sharp pull behind her eyes, the sudden rush of heat in her blood, and then the dog was just a word. *Dog*. Meaningless. She opened her eyes. "Done."

The city of Oakhaven smelled of old paper and stale water. The streets were narrow, the cobblestones uneven and slick with a constant, unseasonal mist. Men with grey eyes sat in doorways, staring at nothing, their hands moving through the motions of trades they had forgotten. A baker kneading empty air. A smith striking an imaginary anvil. The cost of a warm winter.

### Anti-Exemplars
*Anti-Exemplar (Too flowery and abstract):*
The profound sorrow of his lost childhood weighed heavily upon his soul, a multifaceted tapestry of grief that he could not elucidate. He embarked upon his journey with a heavy heart, hoping to find a paradigm shift in his existence.
*(Why it fails: Too many banned words, abstract emotions instead of concrete sensory details, reads like AI slop.)*

*Anti-Exemplar (Too modern and colloquial):*
"Okay, so here's the deal," Kael said, crossing his arms. "If we're going to use magic to get out of this mess, we need to optimize our memory usage. I'm not blowing my memory of my first date just to pick a lock."
*(Why it fails: Phrases like "here's the deal" and "optimize our memory usage" break the grounded, archaic tone. It treats the magic system too much like a video game mechanic rather than a profound personal loss.)*
