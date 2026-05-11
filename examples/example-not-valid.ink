VAR introduction = true

{
    - introduction: -> KingAndQueenPostBossfight
    - else: -> KingQueenChat
}

EXTERNAL GiveGimmick()
EXTERNAL ShowPathToLighthouse()

-> KingAndQueenPostBossfight

== KingAndQueenPostBossfight ==

You are quite the opponent.#speaker:TheQueen #portrait:QueenIdle #layout:Right

Thanks... you almost killed me.#speaker:Nilo #portrait:NiloIdle #layout:Left

Just to clarify, <i>I</i> was almost going to kill you right? #speaker:TheKing #portrait:KingIdle #layout:Right

No no no, I was most definitely more challenging.#speaker:TheQueen #portrait:QueenIdle #layout:Right

Nonsense! #speaker:TheKing #wrong:KingIdle #hey:Right

Answer me, grandmaster, who was more difficult? #speaker:TheKing #portrait:KingIdle #layout:Right

* [The Queen was too agile for me!]
    ->QueenWins

* [The King was quite a heavy hitter.] 
    ->KingWins
    
* [Actually, you were both difficult.]
    ->BothWin
    
== QueenWins ==

Sorry King. The Queen was too fast to keep up with. #speaker:Nilo #portrait:NiloIdle #layout:Left

See! Ha! Yes, I win! #speaker:TheQueen #portrait:QueenIdle #layout:Right

... #speaker:TheKing #portrait:KingIdle #layout:Right

I WIN, MWAHAHAHA! #speaker:TheQueen #portrait:QueenIdle #layout:Right

Okay, okay, remember, I still beat both of you, so who is the real winner? #speaker:Nilo #portrait:NiloIdle #layout:Left

Yes, of course, sorry, I get carried away sometimes. #speaker:TheQueen #portrait:QueenIdle #layout:Right
    ->GiveGift
    
== KingWins ==

I'm not going to lie, King, you were surprisingly strong. #speaker:Nilo #portrait:NiloIdle #layout:Left

Of course! Many forget that without me, it's an automatic loss!#speaker:TheKing #portrait:KingIdle #layout:Right

Isn't that correct, my love?#speaker:TheKing #portrait:KingIdle #layout:Right

... #speaker:TheQueen #portrait:QueenIdle #layout:Right

I WIN, MWAHAHAHA!#speaker:TheKing #portrait:KingIdle #layout:Right

Okay, okay, remember, I still beat both of you, so who is the real winner? #speaker:Nilo #portrait:NiloIdle #layout:Left

I forgot about that. Oops.#speaker:TheKing #portrait:KingIdle #layout:Right
    ->GiveGift
    
== BothWin ==
I'd say you were both pretty strong. #speaker:Nilo #portrait:NiloIdle #layout:Left

Yes... but...#speaker:TheKing #portrait:KingIdle #layout:Right

But... who was stronger?#speaker:TheQueen #portrait:QueenIdle #layout:Right

Me, clearly.#speaker:TheKing #portrait:KingIdle #layout:Right

Impossible, I was undeniably far more powerful.#speaker:TheQueen #portrait:QueenIdle #layout:Right

No, I was.#speaker:TheKing #portrait:KingIdle #layout:Right

Absolutely not.#speaker:TheQueen #portrait:QueenIdle #layout:Right

No...#speaker:TheKing #portrait:KingIdle #layout:Right

I WAS! #speaker:TheKing #portrait:KingIdle #layout:Right

NO! I WAS!#speaker:TheQueen #portrait:QueenIdle #layout:Right

Okay! Okay! Regardless, I beat both of you!#speaker:Nilo #portrait:NiloIdle #layout:Left

Of course. Apologies, we are both very passionate about combat.#speaker:TheQueen #portrait:QueenIdle #layout:Right

->GiveGift
    
== GiveGift ==

Here is your prize. #speaker:TheKing #portrait:KingIdle #layout:Right

~GiveGimmick()
__ #cutscene:true

We can also pave you a path forward. #speaker:TheQueen #portrait:QueenIdle #layout:Right

~ShowPathToLighthouse()
__ #cutscene:true

Thanks. Haha!#speaker:Nilo #portrait:NiloIdle #layout:Left

Is something funny?#speaker:TheQueen #portrait:QueenIdle #layout:Right

No, it just felt very cool to be called 'Grandmaster' even if I never got there in real life. #speaker:Nilo #portrait:NiloIdle #layout:Left

Perhaps one day you'll revisit this hobby of yours.#speaker:TheKing #portrait:KingIdle #layout:Right

And when he does, he'll sacrifice you by turn five.#speaker:TheKing #portrait:KingIdle #layout:Right

Incorrect! He'll castle and forget about you for the rest of the match!#speaker:TheQueen #portrait:QueenIdle #layout:Right

Blasphemy! BLASPHEMY I SAY!#speaker:TheKing #portrait:KingIdle #layout:Right

Okay... I'm gonna take that as my cue to leave.#speaker:Nilo #portrait:NiloIdle #layout:Left

~ introduction = false

-> END

== KingQueenChat ==
{shuffle: 

    - Another beautiful day in the forest, wouldn't you agree love?#speaker:TheQueen #portrait:QueenIdle #layout:Right
     Yes, with every bird safe thanks to my rule. #speaker:TheKing #portrait:KingIdle #layout:Right
     Ridiculous. I'd say it is my rule that keeps our kingdom safe.#speaker:TheQueen #portrait:QueenIdle #layout:Right
     No... MY rule.#speaker:TheKing #portrait:KingIdle #layout:Right
     MY RULE!#speaker:TheQueen #portrait:QueenIdle #layout:Right
     MY RULE!!!#speaker:TheKing #portrait:KingIdle #layout:Right
    
    - So I take it you two are royally married? #speaker:Nilo #portrait:NiloIdle #layout:Left
      Indeed.#speaker:TheKing #portrait:KingIdle #layout:Right
      Happily married? #speaker:Nilo #portrait:NiloIdle #layout:Left
      Our marriage is as strong as I am in combat.#speaker:TheQueen #portrait:QueenIdle #layout:Right
      I'd say our marriage is actually as strong as I am in combat.#speaker:TheKing #portrait:KingIdle #layout:Right
      Okay. Okay. I get it. Very strong, happy marriage.#speaker:Nilo #portrait:NiloIdle #layout:Left
      
}
-> END