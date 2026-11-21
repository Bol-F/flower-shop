# Trivium: How Three Registers Create Encryption

## 01 The wire
### letters
Imagine that the only thing crossing a wire is the word hello.
You can read it in an instant. So can someone listening to the wire.
### alphabet
Inside the computer, each letter is already a pattern of eight bits.
Here is H in binary. We have changed the alphabet, but the message is still plain to see.
### veil
It gives us no secrecy at all. To hide the message, we need something the listener cannot reproduce.
Watch what happens when a second stream meets the first. Five readable letters turn into five quite different bytes.
### engine
Where does that second stream come from? Follow one of its bits back along the wire.
Inside the generator are three rows of memory, a handful of connections, and a clock.
### title
This is Trivium. We'll trace one bit from its birth inside the machine, all the way to the person reading the message.

## 02 A reversible switch
### pair
Think of each bit of the secret stream as an instruction for a switch.
A zero says, leave the message bit alone. A one says, turn it over.
### truth
The switch is called exclusive or. We'll write XOR.
Zero with zero gives zero. With one input on, the result is one. With both inputs on, the result drops back to zero.
### walk
Now read a pair of streams from left to right, one clock at a time.
The third position is the first place where our keystream says flip. Watch the output separate from the message there.
### undo
Send the result through the same switch again. A bit that flipped once flips back. A bit that stayed still stays still.
The receiver can now read the original eight bits.
### source
Getting that identical sequence of switches at both ends is the real trick. Let's open the generator and see what it remembers.

## 03 Inside the machine
### lengths
A register is a row of places where the machine can hold bits.
Here are the three rows drawn to the same scale. The blue row has ninety-three places, the teal row eighty-four, and the orange row one hundred and eleven.
### address
Together they hold two hundred and eighty-eight bits. Number the cells straight through all three rows.
Teal begins at ninety-four. Orange begins at one hundred and seventy-eight.
### lens
Look through this window. Filled cells hold one, open cells hold zero. Enlarging a cell leaves its address exactly where it was.
### shift
When the clock ticks, a stored bit moves one place along its own row.
The bit at the far end leaves. That makes room at the entrance for a freshly calculated bit.
### ring
Trace the connections. Blue helps feed teal, teal helps feed orange, and orange helps feed blue. To start this circuit we need an initial pattern.

## 04 Loading the state
### key
Here is a public practice key in hexadecimal. A real secret key stays with the sender and receiver.
Each pair of hex digits represents one byte. Ten pairs give us eighty key bits.
### iv
The other ten bytes are the initialization vector, or I V. The receiver can know this value.
Changing it lets the same key start a different message with a different internal arrangement.
### load
The key fills the first eighty blue cells. The vector fills positions ninety-four through one hundred and seventy-three in teal.
Notice which end enters first. In the reference byte convention, the high bit of the last printed byte goes into the first cell.
### padding
Fill the thirteen spare blue places and the four spare teal places with zero.
Orange starts with one hundred and eight zeros. Its last three positions, two hundred and eighty-six through two hundred and eighty-eight, hold ones.
### seed
Every position now has a value. Before we let this arrangement evolve, let's meet the rule that changes it.

## 05 One clock under a lens
### freeze
For a clock with interesting inputs, jump ahead to the first output clock of our example.
Freeze the state just before the clock ticks. Every wire we follow reads this same photograph.
### pairA
Begin in blue. A tap is simply a wire that reads a particular cell.
Read sixty-six and ninety-three. They contain one and zero. Their exclusive or gives the first intermediate signal, one.
### pairBC
In teal, read one hundred and sixty-two and one hundred and seventy-seven. Zero and one give us one again.
In orange, positions two hundred and forty-three and two hundred and eighty-eight both hold zero. Their signal is zero.
### output
Bring those three signals together. One exclusive or one is zero. Combining that zero with the last zero leaves zero.
That is our first keystream bit. The register entrances still need their own inputs.
### product
Look at the neighboring blue taps, ninety-one and ninety-two. This time the gate is AND.
Both cells contain one, so the gate opens. If either input were zero, its contribution would vanish. This product makes the feedback nonlinear.
### feedback
Combine that product with the blue signal and the bit at one hundred and seventy-one. The first feedback value is one.
Follow the other two paths. Each takes its own pair of neighbors and one tap from a different row.
### route
All three feedback values happen to be one in this photograph. Their destinations matter.
The third goes to blue, the first to teal, and the second to orange.
### commit
Now release the clock. Three new bits enter together as the old bits shift one place.
Reading even one tap after moving its row could change the calculation. The snapshot keeps that boundary precise.

## 06 Before the first output
### first
Rewind to the moment we loaded the key. Use exactly the clock rule we just traced.
Here is the first tick, and then the second and third. Red marks a position whose value differs from the previous tick.
### quarter
Let the counter run to two hundred and eighty-eight, the number of bits in the whole state.
The rows have different lengths, so this is a counting landmark, not a return to the beginning.
### half
At five hundred and seventy-six ticks, the key bits have repeatedly met bits arriving from other rows.
Every image here comes from stepping the machine. As the counter accelerates we sample its states for the screen.
### ready
The standard warm-up ends after eleven hundred and fifty-two clocks. Every candidate output so far has been discarded.
The very next clock produces the first bit that may actually be used to encrypt a message.

## 07 Sending and receiving
### inputs
Return to hello. Both endpoints have the same key and initialization vector. Independently, they arrive at the same warmed state.
One will send five bytes. The other needs forty matching keystream bits.
### bytes
In ordinary hexadecimal notation the first plaintext byte is forty-eight. The two L's have exactly the same byte value.
On this page, each binary byte is written in the familiar way, with its highest place on the left.
### mask
The cipher fills the lowest place first. Follow the early clock bits into the right-hand end of the first byte.
After eight clocks the completed mask byte reads F four. Four more bytes fill in beside it.
### cipher
Apply exclusive or down each column. The first byte becomes B C.
Look at the two identical L's. They land under different keystream bytes and give different ciphertext bytes.
### recover
At the receiver, pair each ciphertext byte with its original mask. The same gate brings back the five letters, including both L's.
### reuse
With a fixed key, use a fresh initialization vector for each separate message. Repeating the pair repeats the entire mask, exposing relationships between the messages.

## 08 A difference of one bit
### flip
Make a second copy of the experiment. Keep the key fixed, and flip just the high bit of the last vector byte.
In the loaded state that changes exactly one cell, the first one in teal. Everything else agrees.
### evolve
Clock both machines together. A discrepancy can move along a row before it reaches a tap.
When it enters a feedback calculation, it can influence another row as well. Watch the locations marked in red.
### metric
How do we count the effect on the output? Write the two streams one above the other.
Add one when their next bits differ and zero when they agree. The running total is called Hamming distance.
### curve
Here the horizontal distance is the number of output bits compared. Each upward step is one disagreement.
After the full warm-up, sixty-six of the first hundred and twenty-eight bits differ for this particular pair.
### checkpoints
Restart both copies and try shorter warm-ups. At two hundred and eighty-eight clocks, fifty-one outputs differ. At five hundred and seventy-six, sixty-three differ.
These shorter runs are teaching experiments. The specified cipher uses all eleven hundred and fifty-two initialization clocks.

## 09 Counting and checking
### sample
Take four thousand and ninety-six successive bits from the original, fully initialized machine. What can we measure about this one sample?
Start by sorting the bits into zeros and ones.
### balance
There are two thousand and forty-four zeros and two thousand and fifty-two ones. The frequency test measures that imbalance against what independent fair bits would produce.
### runs
Now keep the original order. A run is a maximal stretch of identical bits. Every change starts a new run.
Our sample has two thousand and fourteen runs. A perfectly alternating sequence could be balanced and still have far too many runs.
### limits
Each p-value measures how unusual the statistic is under a model of independent fair bits. Both exceed one percent.
This describes two properties of one sample. Establishing security is a much larger question.
### vector
For correctness, use a published answer. Load the key and vector from the eSTREAM record, generate sixty-four bytes, and compare every byte.
Expected and calculated match all the way to the end.

## 10 Put the machine together
### assemble
Now we can follow the entire journey. The secret key and public initialization vector supply the starting bits for three connected registers.
The three ones at the end complete the starting pattern.
### loop
Turn the clock. Exclusive or combines taps, AND introduces a product, and three feedback bits cross into their next rows.
Repeat the same rule eleven hundred and fifty-two times before keeping any output.
### wire
One more tick gives one keystream bit. A fresh message bit meets it at the switch.
The receiver recreates that switch and recovers the letter. We have followed the wire all the way back to hello.
### end
Three registers, one clock, and a small set of operations. That's the beauty of Trivium. Simple operations. Complex behavior.
