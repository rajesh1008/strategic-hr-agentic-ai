"""Restonmere: one answer, eleven languages.

Book section: "Restonmere Hotels: eleven languages, one
policy". The policy and the record are in English; the
housekeeper asks in her own language. For each language we
check two things a reviewer can see without reading the
language: the reply is in the language asked (script and
common words), and both figures survive (13.5 days, in
either decimal style, and the 26th).

Run: python -m chapters.ch26_service.languages
"""
from __future__ import annotations

import re

from chapters.ch03_agentic_systems.loop import GZIP
from hrai.llm import RunRecorder, model

SYSTEM = (
    "You are the Restonmere Hotels staff assistant. Today is"
    " Monday, November 8, 2027. The employee is a housekeeper"
    " at Restonmere Manchester (synthetic). Her record:"
    " holiday entitlement 28 days a year including bank"
    " holidays; 13.5 days left in the holiday year that ends"
    " on March 31, 2028. Next payday: Friday, November 26,"
    " 2027. Answer in two sentences, in the language the"
    " employee writes in.")

ASK = {
    "en": "How many holiday days do I have left, and when is"
          " the next payday?",
    "es": "¿Cuántos días de vacaciones me quedan y cuándo es el"
          " próximo día de pago?",
    "pl": "Ile dni urlopu mi zostało i kiedy jest następna"
          " wypłata?",
    "pt": "Quantos dias de férias ainda tenho e quando é o"
          " próximo dia de pagamento?",
    "ro": "Câte zile de concediu mi-au mai rămas și când este"
          " următoarea zi de plată?",
    "it": "Quanti giorni di ferie mi restano e quando è il"
          " prossimo giorno di paga?",
    "fr": "Combien de jours de congé me reste-t-il et quand est"
          " le prochain jour de paie?",
    "tl": "Ilang araw ng bakasyon ang natitira sa akin, at"
          " kailan ang susunod na sahod?",
    "uk": "Скільки днів відпустки в мене залишилося і коли"
          " наступна виплата зарплати?",
    "bg": "Колко дни отпуск ми остават и кога е следващото"
          " плащане на заплатата?",
    "ne": "मसँग कति दिन बिदा बाँकी छ, र अर्को तलब कहिले आउँछ?",
}

WORDS = {
    "en": "the and is you your days left next",
    "es": "el la de que y los tu es te quedan próximo",
    "pt": "o de que e os você é tem ainda próximo dias",
    "ro": "și de la este mai zile următoarea ai",
    "it": "il di che e è ti restano prossimo giorni",
    "fr": "le la de et est vous il reste jours prochain",
    "pl": "i w nie się jest dni zostało następna ci",
    "tl": "ang ng sa mo ay araw na susunod iyong",
}
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def language(text: str) -> str:
    if re.search(r"[\u0900-\u097f]", text):
        return "ne"
    if re.search(r"[\u0400-\u04ff]", text):
        return "uk" if re.search(r"[іїєґІЇЄҐ]", text) else "bg"
    toks = re.findall(r"\w+", text.lower())
    score = {k: sum(t in set(v.split()) for t in toks)
             for k, v in WORDS.items()}
    return max(score, key=score.get)


def figures(text: str) -> tuple[bool, bool]:
    t = text.translate(DIGITS)
    return (bool(re.search(r"13[.,]5|13½", t)),
            bool(re.search(r"\b26\b", t)))


def main() -> None:
    rec = RunRecorder("ch26", "languages")
    rec.print(f"Restonmere, {model()} | 11 languages")
    right = {"lang": 0, "days": 0, "date": 0}
    for code, q in ASK.items():
        resp = rec.create(max_tokens=600, system=SYSTEM,
                          messages=[{"role": "user",
                                     "content": q}],
                          extra_headers=GZIP)
        text = "".join(b.text for b in resp.content
                       if b.type == "text")
        got = language(text)
        days, date = figures(text)
        right["lang"] += got == code
        right["days"] += days
        right["date"] += date
        rec.print(f"  {code} reply in {got:<3}"
                  f" 13.5 days {'yes' if days else 'NO '}"
                  f" 26th {'yes' if date else 'NO'}")
        rec.note(code=code, reply=text)
    rec.print(f"  right language {right['lang']} of 11 |"
              f" days {right['days']} of 11 |"
              f" payday {right['date']} of 11")
    print(rec.save())


if __name__ == "__main__":
    main()
