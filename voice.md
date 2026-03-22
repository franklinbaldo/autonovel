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
Gritty, pragmatic, and sensory. The narrator treats memory as a physical, wet commodity. Sentences are stripped of romanticism. The world is seen through the lens of a weary survivalist dealing with desperate addicts.

### Sentence Rhythm
Terse and rhythmic, mimicking the fractured nature of extracted memories. Short, blunt sentences for action and observation. Longer, flowing sentences reserved only for describing the euphoric rush or disorienting fog of consuming a memory.

### Vocabulary Register
Clinical and visceral. Words associated with surgery, butchery, and finance. "Siphon," "vial," "cortex," "spill," "hollow," "leech," "ledger," "dregs." Avoiding flowery adjectives in favor of strong nouns and active verbs.

### POV and Tense
Third-person limited, past tense. Close psychic distance to the protagonist, emphasizing their physical sensations—headaches, cold sweats, the smell of copper and ozone that accompanies an extraction.

### Dialogue Conventions
Minimal tags. Dialogue is transactional and often broken. Characters rarely say exactly what they mean, instead negotiating around the edges of their wants. The memory-rich speak in complete, languid sentences; the hollowed-out speak in repetitive fragments, grasping for words they've sold.

### Exemplar Passages
The needle slid into the base of the skull with the sound of a boot crushing frost. Kael held the glass vial steady. The memory—a summer afternoon eating bruised peaches—bled down the glass tube, glowing a faint, sickening amber. The client went slack in the chair. His eyes lost their focus. When he woke, he wouldn't remember the taste of the fruit, or the girl who handed it to him. He'd just have the coin Kael left on the table.

In the lower wards, the hollows begged for scraps. They didn't want coin anymore. They traded their boots, their coats, for a drop of someone else's nostalgia. Kael walked past them, keeping his hand tight on his satchel. The vials clinked against each other. A fortune in stolen grief and bought joy, heavy against his hip.

### Anti-Exemplars
*Too flowery and abstract:*
Kael felt a profound sense of sadness as he utilized the mystical needle to extract the myriad memories from the man's mind. It was a multifaceted tapestry of emotions, a true testament to the human condition.

*Too modern and casual:*
Okay, so basically, taking out memories sucked. Kael hated his job, but hey, it paid the bills. He grabbed the needle and stuck it in the guy's neck, watching the shiny stuff pour out into the bottle.
