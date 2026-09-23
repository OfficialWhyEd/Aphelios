# Prompt pronti per Gemini - la mascotte di WhyEd

Aggiornati il 09/09/2026 col tratto **Cartoon Network / Jetix anni 2000** chiesto da lui.
Seguono `../SPECIFICA.md` e tutte le correzioni del 05/09.
**Uno per volta**, incollato su una riga sola nella barra di Gemini, poi clic sulla freccia blu.

In tutti: quadrato 1:1 pieno, contorno nero spesso, occhi enormi in basso, niente pupille,
corna piccole e affilate, sagoma asimmetrica, ombra piatta sotto, niente scritte, niente watermark.

---

## A - la viola (la direzione che gli era piaciuta)

2000s Cartoon Network Jetix cartoon style, app icon in squircle format, square 1:1 full bleed, deep violet solid background, one single character filling 90% of the frame, a black ink-drop creature shaped like a big rounded blob head, thick bold black outline all around it like early 2000s TV animation, simple geometric shapes only, no gradients on the character, deliberately asymmetric silhouette with one side heavier than the other, two very small sharp pointed horns on top, enormous oval eyes placed low on the face leaving a huge black forehead above them, eyes are solid flat white with no pupils and no highlights, no mouth, thin light-grey inner contour so the black body separates from the background, small flat elliptical shadow underneath because the creature floats, mischievous not cute, extreme contrast, three colours total, no text, no watermark, no letters, no border, no frame

---

## B - il nero pieno (il suo colore preferito)

2000s Cartoon Network Jetix cartoon style, app icon in squircle format, square 1:1 full bleed, near-black charcoal solid background, one single character filling 90% of the frame, a pure black ink-drop creature shaped like a big rounded blob head, thick bold outline in mid-grey all around it like early 2000s TV animation so the black character reads clearly against the black background, simple geometric shapes only, flat colours, asymmetric silhouette, two very small sharp pointed horns on top, enormous oval eyes placed low with a huge black forehead above, eyes are solid flat white with no pupils, no mouth, small flat shadow underneath because it floats, the expression comes only from the eyes, mischievous, no text, no watermark, no letters, no border, no frame

---

## C - il cremisi

2000s Cartoon Network Jetix cartoon style, app icon in squircle format, square 1:1 full bleed, deep crimson red solid background, one single character filling 90% of the frame, a black ink-drop creature, big rounded blob head, thick bold black cartoon outline, simple geometric shapes, flat colours, asymmetric silhouette leaning to one side as if made of liquid ink about to move, two tiny sharp horns, enormous flat white oval eyes low on the face with no pupils, no mouth, thin light-grey inner contour, flat shadow underneath, mischievous, extreme contrast, three colours total, no text, no watermark, no letters, no border, no frame

---

## D - il verde acido (contrasto massimo, per l'icona a 32px)

2000s Cartoon Network Jetix cartoon style, app icon in squircle format, square 1:1 full bleed, acid green solid background, one single character filling 92% of the frame, a solid black ink-drop creature, big rounded blob head, thick bold black cartoon outline, simple geometric shapes only, asymmetric, two tiny sharp horns, huge flat white oval eyes set low with a big forehead above, no pupils, no mouth, thin grey inner contour, flat shadow underneath, must stay readable as a black silhouette at 32x32 pixels, mischievous, no text, no watermark, no letters, no border, no frame

---

## Dopo, per le pose (solo sulla variante che sceglie lui)

Si riparte dall'immagine approvata e si chiede a Gemini "same character, same style, same colours,
same thick cartoon outline, only the pose changes" piu' la posa. Pose utili:
- che saluta con una mano
- che dorme
- che pensa, occhi in su
- che si allunga come inchiostro che cola
- che si spaventa, occhi spalancati
- di spalle

Le pose vanno salvate in `../out/pose/` con nome `posa-01-saluta.png` ecc.
Poi l'animazione si fa in CSS a sprite o in SVG: gira ovunque e pesa niente.

---

# IL PROMPT CHE FUNZIONA (10/09/2026)

Chat NUOVA di Gemini, tutto su una riga. Bianco e nero, si giudica solo la forma.

Generate one image: a mascot head silhouette, front view, pure solid black on a pure white background, flat vector, no colour, no gradient, no outline, no shading, no text, no watermark, no frame. The head is a rounded egg-like head, wider at the bottom, narrowing toward the top, it stays a proper HEAD with volume, not a thin mask. Out of the top of that head grow TWO LONG STRAIGHT POINTED EARS, like tall rabbit or bat ears, roughly as tall as the head itself, slightly leaning outward. The ears are SOLID FILLED BLACK, completely filled, no inner shape, no inner line, no hollow, no white slit inside. The junction where each ear meets the head is COMPLETELY SMOOTH AND SEAMLESS, one continuous flowing curve, no notch, no step, no corner, the ear grows out of the skull like it was cast in one piece. Between the two ears there is only a SHALLOW SHORT V valley near the very top, it must NOT cut down into the head. Inside the black head there are exactly two eyes and nothing else: TWO LARGE TEARDROP SHAPES in solid white, tilted, their pointed tips converging toward the top centre, sitting VERY LOW on the face, near the bottom edge of the head, with an enormous black forehead above them. No pupils, no mouth, no nose, no body, no shadow. The eyes are the signature of this character: they must carry ALL the expression on their own, so make them sharp and angled with real attitude, cocky, defiant, badass, never cute, never round, never soft. The whole silhouette must feel bold and badass.

## Perche' funziona, in breve
- **orecchie piene**, mai la fessura bianca dentro
- **attacco liscio**: l'orecchio esce dal cranio come fuso, nessuna tacca
- **V corta** in cima, non deve tagliare dentro la testa
- **occhi bassissimi**, fronte nera enorme sopra
- **gli occhi sono la firma**: ci deve stare tutta l'espressivita', quindi affilati e con
  attitudine, mai teneri
- riferimento di forma ammesso: Hornet di Silksong **solo per il liscio**, ma **mai
  copiarla**: deve restare un mix con la sua testa a uovo
